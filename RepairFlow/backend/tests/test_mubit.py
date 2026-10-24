"""Real Anthropic serialization against a fake transport; no provider calls."""
import json
import uuid

import httpx2
import pytest
from pydantic import ValidationError
from pydantic_ai.exceptions import ModelHTTPError, UsageLimitExceeded

from app.agents.coordinator import build_coordinator
from app.agents.instructions import COORDINATOR_INSTRUCTIONS
from app.agents.mubit import MubitCoordinator, capture_request_id, reserve_run, MubitBudgetExceeded
from app.config import Settings
from app.db import session_scope
from app.domain import services
from tests.test_coordinator import _case_with_pending_report


def test_budget_reservation_persists_and_zero_pauses(tmp_path):
    settings = Settings(_env_file=None, data_dir=tmp_path, mubit_budget_path=tmp_path / 'budget.db', mubit_max_runs=2)
    assert reserve_run(settings) == 1
    assert reserve_run(settings.model_copy(update={"data_dir": tmp_path / "different-output"})) == 2
    with pytest.raises(MubitBudgetExceeded):
        reserve_run(settings.model_copy())
    with pytest.raises(MubitBudgetExceeded):
        reserve_run(settings.model_copy(update={"mubit_budget_path": tmp_path / "paused.db", "mubit_max_runs": 0}))


def test_budget_concurrent_reservations_cannot_exceed_limit(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    settings = Settings(_env_file=None, data_dir=tmp_path, mubit_budget_path=tmp_path / 'budget.db', mubit_max_runs=3)

    def attempt(_):
        try:
            return reserve_run(settings)
        except MubitBudgetExceeded:
            return None

    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(attempt, range(10)))
    assert sorted(r for r in results if r is not None) == [1, 2, 3]


@pytest.mark.asyncio
async def test_paused_budget_never_reaches_gateway(app_db, tmp_path):
    case_id, _, _ = await _case_with_pending_report()
    async with session_scope() as session:
        snapshot = await services.load_case_snapshot(session, case_id)

    def forbidden(request):
        pytest.fail("Paused budget must not make a network request")

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(forbidden))
    coordinator = MubitCoordinator(Settings(_env_file=None, mubit_api_key="test", data_dir=tmp_path, mubit_budget_path=tmp_path / 'budget.db', mubit_max_runs=0), http_client=client)
    try:
        with pytest.raises(MubitBudgetExceeded):
            await coordinator.decide(snapshot, str(uuid.uuid4()))
    finally:
        await coordinator.aclose()
    metrics = json.loads((tmp_path / "mubit-runs.jsonl").read_text())
    assert metrics["error_type"] == "MubitBudgetExceeded"
    assert metrics["request_ids"] == []


@pytest.mark.parametrize("options", [
    {"coordinator_provider": "mubit"},
    {"coordinator_provider": "mubit", "mubit_api_key": "test", "mubit_model": "gpt-6-luna"},
    {"coordinator_provider": "mubit", "mubit_api_key": "test", "mubit_base_url": "http://api.mubit.ai/anthropic"},
    {"coordinator_provider": "mubit", "mubit_api_key": "test", "mubit_base_url": "https://api.mubit.ai/anthropic/v1"},
])
def test_invalid_config_fails_clearly(options):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **options)


def test_selection_is_explicit_and_secrets_are_hidden():
    settings = Settings(_env_file=None, mubit_api_key="secret-for-tests", gemini_api_key="google-test")
    assert settings.active_coordinator_provider == "mubit"
    assert "secret-for-tests" not in repr(settings)
    assert build_coordinator(Settings(_env_file=None, coordinator_provider="fixture", mubit_api_key="test")).model_id == "fixture-conservative"


@pytest.mark.asyncio
async def test_gateway_tool_roundtrip_and_session(app_db, tmp_path, monkeypatch):
    case_id, report_id, _ = await _case_with_pending_report()
    async with session_scope() as session:
        snapshot = await services.load_case_snapshot(session, case_id)
    # Partial snapshot makes a genuine scoped report read necessary.
    snapshot = snapshot.model_copy(update={"latest_reports": []})
    trigger = str(uuid.uuid4())
    requests = []
    # A developer's Anthropic credentials must never be sent beside the Mubit key.
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "unrelated-token")

    def respond(request):
        body = json.loads(request.content)
        requests.append(body)
        assert str(request.url).split('?')[0] == "https://api.mubit.ai/anthropic/v1/messages"
        assert request.headers['x-api-key'] == 'test-mubit-key'
        assert 'authorization' not in request.headers
        assert request.headers['x-middleware-record'] == 'off'
        assert body['metadata']['user_id'] == f'repairflow-case-{case_id}'
        if len(requests) == 1:
            name, args = 'read_report', {'case_id': case_id, 'record_id': report_id}
        else:
            name = next(t['name'] for t in body['tools'] if t['name'] not in {
                'read_report', 'read_communication', 'list_case_events', 'find_appointment_options', 'read_research'})
            args = {'case_id': case_id, 'expected_case_version': snapshot.snapshot_version,
                    'trigger_event_id': trigger, 'decision_summary': 'Needs operator review.',
                    'evidence_refs': [], 'action': {'kind': 'WAIT', 'reason': 'review', 'waiting_for': 'operator'}}
        return httpx2.Response(200, headers={'x-middleware-request-id': f'mreq_test_{len(requests)}'}, json={
            'id': 'msg_test', 'type': 'message', 'role': 'assistant', 'model': 'claude-haiku-4-5',
            'content': [{'type': 'tool_use', 'id': f'tool_{len(requests)}', 'name': name, 'input': args}],
            'stop_reason': 'tool_use', 'stop_sequence': None, 'usage': {'input_tokens': 20, 'output_tokens': 10},
        })

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(respond), event_hooks={'response': [capture_request_id]})
    settings = Settings(_env_file=None, mubit_api_key='test-mubit-key', mubit_record='off', data_dir=tmp_path, mubit_budget_path=tmp_path / 'budget.db')
    coordinator = MubitCoordinator(settings, http_client=client)
    try:
        proposal = await coordinator.decide(snapshot, trigger)
    finally:
        await coordinator.aclose()
    assert proposal.action.kind == 'WAIT'
    assert len(requests) == 2
    assert requests[0]['system'] == requests[1]['system']
    assert requests[0]['system'][0]['text'] == COORDINATOR_INSTRUCTIONS.strip()
    assert requests[0]['tools'] == requests[1]['tools']
    log = json.loads((tmp_path / 'mubit-runs.jsonl').read_text())
    assert log['request_ids'] == ['mreq_test_1', 'mreq_test_2']
    assert log['requests'] == 2 and log['input_tokens'] == 40
    assert log['status'] == 'validated_proposal'
    assert 'test-mubit-key' not in json.dumps(log)


@pytest.mark.asyncio
async def test_gateway_failure_is_recorded_without_fallback(app_db, tmp_path):
    case_id, _, _ = await _case_with_pending_report()
    async with session_scope() as session:
        snapshot = await services.load_case_snapshot(session, case_id)
    client = httpx2.AsyncClient(transport=httpx2.MockTransport(lambda request: httpx2.Response(
        401, headers={'x-middleware-request-id': 'mreq_failed'},
        json={'type': 'error', 'error': {'type': 'authentication_error', 'message': 'private-provider-message'}},
    )), event_hooks={'response': [capture_request_id]})
    coordinator = MubitCoordinator(Settings(_env_file=None, mubit_api_key='test', data_dir=tmp_path, mubit_budget_path=tmp_path / 'budget.db', mubit_max_runs=1), http_client=client)
    try:
        with pytest.raises(ModelHTTPError):
            await coordinator.decide(snapshot, str(uuid.uuid4()))
        with pytest.raises(MubitBudgetExceeded):
            await coordinator.decide(snapshot, str(uuid.uuid4()))
    finally:
        await coordinator.aclose()
    text = (tmp_path / 'mubit-runs.jsonl').read_text()
    rows = [json.loads(line) for line in text.splitlines()]
    metrics = rows[0]
    assert metrics['status'] == 'failed'
    assert metrics['request_ids'] == ['mreq_failed']
    assert 'private-provider-message' not in text
    assert rows[1]['error_type'] == 'MubitBudgetExceeded'
    assert rows[1]['request_ids'] == []
    assert rows[1]['requests'] == 0
    assert rows[1]['input_tokens'] == 0
    assert rows[1]['tool_calls'] == 0


@pytest.mark.asyncio
async def test_token_limit_prevents_another_gateway_request(app_db, tmp_path):
    case_id, report_id, _ = await _case_with_pending_report()
    async with session_scope() as session:
        snapshot = await services.load_case_snapshot(session, case_id)
    # Partial snapshot makes a genuine scoped report read necessary.
    snapshot = snapshot.model_copy(update={"latest_reports": []})
    requests = []

    def respond(request):
        requests.append(request)
        return httpx2.Response(200, json={
            'id': 'msg_limit', 'type': 'message', 'role': 'assistant', 'model': 'claude-haiku-4-5',
            'content': [{'type': 'tool_use', 'id': 'read_1', 'name': 'read_report',
                         'input': {'case_id': case_id, 'record_id': report_id}}],
            'stop_reason': 'tool_use', 'stop_sequence': None,
            'usage': {'input_tokens': 2000, 'output_tokens': 10},
        })

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(respond))
    coordinator = MubitCoordinator(Settings(
        _env_file=None, mubit_api_key='test', data_dir=tmp_path,
        mubit_budget_path=tmp_path / 'budget.db', mubit_max_tokens_per_run=1000,
    ), http_client=client)
    try:
        with pytest.raises(UsageLimitExceeded):
            await coordinator.decide(snapshot, str(uuid.uuid4()))
    finally:
        await coordinator.aclose()
    assert len(requests) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize('limit_kind', ['request_limit', 'tool_calls_limit', 'total_tokens_limit'])
async def test_failed_run_retains_numeric_usage_and_safe_limit_kind(app_db, tmp_path, limit_kind):
    from pydantic_ai.usage import UsageLimits

    case_id, report_id, _ = await _case_with_pending_report()
    async with session_scope() as session:
        snapshot = await services.load_case_snapshot(session, case_id)
    # Partial snapshot makes a genuine scoped report read necessary.
    snapshot = snapshot.model_copy(update={"latest_reports": []})

    def respond(request):
        calls = 2 if limit_kind == 'tool_calls_limit' else 1
        return httpx2.Response(200, json={
            'id': 'msg_limit', 'type': 'message', 'role': 'assistant', 'model': 'claude-haiku-4-5',
            'content': [{'type': 'tool_use', 'id': f'read_{i}', 'name': 'read_report',
                         'input': {'case_id': case_id, 'record_id': report_id}} for i in range(calls)],
            'stop_reason': 'tool_use', 'stop_sequence': None,
            'usage': {'input_tokens': 2000, 'output_tokens': 10},
        })

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(respond))
    coordinator = MubitCoordinator(Settings(
        _env_file=None, mubit_api_key='private-key', data_dir=tmp_path,
        mubit_budget_path=tmp_path / 'budget.db',
    ), http_client=client)
    coordinator.usage_limits = UsageLimits(**{limit_kind: 1})
    try:
        with pytest.raises(UsageLimitExceeded):
            await coordinator.decide(snapshot, str(uuid.uuid4()))
    finally:
        await coordinator.aclose()
    text = (tmp_path / 'mubit-runs.jsonl').read_text()
    metrics = json.loads(text)
    assert metrics['status'] == 'failed'
    assert metrics['requests'] == 1
    assert metrics['input_tokens'] == 2000
    assert metrics['output_tokens'] == 10
    assert metrics['tool_calls'] == (1 if limit_kind == 'request_limit' else 0)
    assert metrics['limit_kind'] == limit_kind
    assert 'private-key' not in text
    assert 'Current case snapshot' not in text
    assert 'Consider raising' not in text
