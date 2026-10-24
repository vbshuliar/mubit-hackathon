"""Shadow integration checks use fake inference only, never the live gateway."""
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.agents import report_routing
from app.config import Settings
from app.db import session_scope
from app.domain import services
from tests.test_coordinator import _case_with_pending_report


@pytest.fixture
async def snapshot(app_db):
    case_id, _, _ = await _case_with_pending_report()
    async with session_scope() as session:
        return await services.load_case_snapshot(session, case_id)


def test_shadow_disabled_by_default():
    assert not Settings(_env_file=None).mubit_report_shadow_enabled


@pytest.mark.asyncio
async def test_disabled_never_constructs_task(snapshot, monkeypatch):
    def forbidden(*args):
        pytest.fail('Disabled shadow must not construct a model client')
    monkeypatch.setattr(report_routing, 'ReportTask', forbidden)
    assert await report_routing.observe_report(snapshot, Settings(_env_file=None)) == {'status': 'disabled'}


@pytest.mark.asyncio
@pytest.mark.parametrize('mutation', ['multiple', 'foreign_case', 'foreign_work', 'foreign_contractor',
                                     'stale_attempt', 'completed', 'applied', 'oversized'])
async def test_ineligible_evidence(snapshot, mutation):
    report = snapshot.latest_reports[0]
    if mutation == 'multiple':
        snapshot.latest_reports.append(report.model_copy(update={'id': uuid4()}))
    elif mutation == 'foreign_case':
        report.case_id = uuid4()
    elif mutation == 'foreign_work':
        report.work_order_id = uuid4()
    elif mutation == 'foreign_contractor':
        report.contractor_id = uuid4()
    elif mutation == 'stale_attempt':
        snapshot.appointments.append(snapshot.appointments[0].model_copy(update={'id': uuid4(), 'attempt_number': 2}))
    elif mutation == 'completed':
        snapshot.work_orders[0].status = 'COMPLETED'
    elif mutation == 'applied':
        report.interpretation_status = 'APPLIED'
    elif mutation == 'oversized':
        report.text = 'x' * 6001
    assert report_routing.select_report(snapshot) is None


@pytest.mark.asyncio
async def test_shadow_record_off_preserves_snapshot_and_unknown_provenance(snapshot, monkeypatch):
    before = snapshot.model_dump()
    calls = []

    class FakeTask:
        def __init__(self, settings):
            pass

        async def infer(self, evidence, *, split):
            calls.append((evidence, split))
            return SimpleNamespace(classification='SCAFFOLD_REQUIRED'), {'record_mode': 'off'}

        async def aclose(self):
            calls.append('closed')

    monkeypatch.setattr(report_routing, 'ReportTask', FakeTask)
    result = await report_routing.observe_report(snapshot, Settings(_env_file=None, mubit_report_shadow_enabled=True))
    assert result['classification'] == 'SCAFFOLD_REQUIRED'
    assert result['serving_provenance'] == 'unknown'
    assert result['mode'] == 'shadow'
    assert calls[0][1] == 'dev'
    assert calls[0][0].report_text == snapshot.latest_reports[0].text
    assert calls[0][0].work_scope == snapshot.work_orders[0].scope
    assert calls[1] == 'closed'
    assert snapshot.model_dump() == before


@pytest.mark.asyncio
async def test_shadow_error_is_content_free(snapshot, monkeypatch):
    class FakeTask:
        last_metrics = {}

        def __init__(self, settings):
            pass

        async def infer(self, *args, **kwargs):
            raise RuntimeError('private report text and credential')

        async def aclose(self):
            pass

    monkeypatch.setattr(report_routing, 'ReportTask', FakeTask)
    result = await report_routing.observe_report(snapshot, Settings(_env_file=None, mubit_report_shadow_enabled=True))
    assert result['status'] == 'error'
    assert result['error_type'] == 'RuntimeError'
    assert 'private' not in str(result)


@pytest.mark.asyncio
async def test_cancellation_propagates_and_closes(snapshot, monkeypatch):
    import asyncio
    closed = []

    class FakeTask:
        def __init__(self, settings):
            pass

        async def infer(self, *args, **kwargs):
            raise asyncio.CancelledError()

        async def aclose(self):
            closed.append(True)

    monkeypatch.setattr(report_routing, 'ReportTask', FakeTask)
    with pytest.raises(asyncio.CancelledError):
        await report_routing.observe_report(snapshot, Settings(_env_file=None, mubit_report_shadow_enabled=True))
    assert closed == [True]


@pytest.mark.asyncio
async def test_last_reservation_preserves_operational_proposal(snapshot, tmp_path):
    from app.agents.mubit import MubitCoordinator
    from pydantic_ai.usage import RunUsage
    import json

    coordinator = object.__new__(MubitCoordinator)
    coordinator.settings = Settings(_env_file=None, mubit_api_key='fake',
        data_dir=tmp_path, mubit_budget_path=tmp_path / 'budget.db',
        mubit_max_runs=1, mubit_report_shadow_enabled=True)
    coordinator.model_id = 'test-coordinator'
    proposal = SimpleNamespace(action=SimpleNamespace(kind='WAIT'))

    async def run(*args, **kwargs):
        return SimpleNamespace(output=proposal, usage=RunUsage())

    coordinator._run = run
    assert await coordinator.decide(snapshot, str(uuid4())) is proposal
    metrics = json.loads((tmp_path / 'mubit-runs.jsonl').read_text())
    assert metrics['status'] == 'validated_proposal'
    assert metrics['report_shadow']['error_type'] == 'MubitBudgetExceeded'
