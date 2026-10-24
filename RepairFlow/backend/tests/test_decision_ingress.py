"""Partial replies must not erase different waits or unconfirmed evidence."""
import uuid
from datetime import datetime, timedelta, timezone
import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from app.main import app
from app.db import session_scope
from app.domain import services
from app.domain.services import ActorContext
from app.schemas import FactInput, ObservationSubmission, RequestInformation
from tests.test_demo_inputs import create, body

@pytest.mark.parametrize('value', ['safe', True, None, 'yes'])
def test_safety_observations_reject_untyped_answers(value):
    with pytest.raises(ValidationError):
        FactInput(field='gas', value=value, spoken_text='Reported evidence', confirmed_by_speaker=True)

def test_unconfirmed_safety_fact_cannot_replace_recorded_risk():
    with pytest.raises(ValidationError):
        FactInput(field='gas', value='NO', spoken_text='Maybe safe', confirmed_by_speaker=False)

def test_observation_rejects_unconfirmed_availability():
    start = datetime.now(timezone.utc) + timedelta(days=1)
    with pytest.raises(ValidationError):
        ObservationSubmission(communication_id=uuid.uuid4(), source_text='Not confirmed', availability=[{
            'start_at': start, 'end_at': start + timedelta(hours=2), 'timezone': 'Europe/London',
            'spoken_text': 'Maybe tomorrow', 'confirmed_by_speaker': False}])

@pytest.mark.asyncio
async def test_operator_note_does_not_answer_missing_contractor_report(app_db):
    async with AsyncClient(transport=ASGITransport(app), base_url='http://test') as client:
        cid = await create(client)
        async with session_scope() as session:
            result = await services.request_information(session, case_id=cid,
                action=RequestInformation(recipient='OPERATOR', purpose='CONTRACTOR', questions=['Obtain the visit report']),
                actor=ActorContext('SYSTEM', 'test', str(uuid.uuid4())))
            request_id = str(result.resource_ids['communication_id'])
        rejected = await client.post(f'/api/v1/cases/{cid}/demo-inputs', json=body('OPERATOR_UPDATE', response_to_communication_id=request_id))
        assert rejected.status_code == 409
        accepted = await client.post(f'/api/v1/cases/{cid}/demo-inputs', json=body('OPERATOR_UPDATE', text='The specialist has not replied yet.'))
        assert accepted.status_code == 202, accepted.text
        async with session_scope() as session:
            snap = await services.load_case_snapshot(session, cid)
            assert any(str(c.id) == request_id and c.state == 'REQUESTED' for c in snap.communications)

@pytest.mark.asyncio
@pytest.mark.parametrize('explicit', [False, True])
async def test_partial_availability_reply_preserves_request(app_db, explicit):
    async with AsyncClient(transport=ASGITransport(app), base_url='http://test') as client:
        cid = await create(client)
        async with session_scope() as session:
            result = await services.request_information(session, case_id=cid,
                action=RequestInformation(recipient='TENANT', purpose='AVAILABILITY', questions=['When can you provide access?']),
                actor=ActorContext('SYSTEM', 'test', str(uuid.uuid4())))
            request_id = str(result.resource_ids['communication_id'])
        payload = body(text='I do not know my availability yet.')
        if explicit:
            payload['response_to_communication_id'] = request_id
        response = await client.post(f'/api/v1/cases/{cid}/demo-inputs', json=payload)
        assert response.status_code == 202, response.text
        async with session_scope() as session:
            snap = await services.load_case_snapshot(session, cid)
            assert any(str(c.id) == request_id and c.state == 'REQUESTED' for c in snap.communications)


@pytest.mark.asyncio
@pytest.mark.parametrize('request_count,explicit,ended_count', [(1, False, 1), (2, False, 0), (2, True, 1)])
async def test_report_closes_only_unambiguous_or_explicit_request(app_db, request_count, explicit, ended_count):
    from app.models import CommunicationModel
    from tests.test_hero_path import _seed_reference_data
    from tests.test_fixi_ui_support import _drive_case_to_scheduled

    prop, tenant, roofer, _ = await _seed_reference_data()
    cid, _, _, appointment = await _drive_case_to_scheduled(prop, tenant, roofer)
    request_ids = [str(uuid.uuid4()) for _ in range(request_count)]
    async with session_scope() as session:
        version = (await services.load_case(session, cid)).version
        for request_id in request_ids:
            session.add(CommunicationModel(id=request_id, case_id=cid, tenant_id=None,
                purpose='CONTRACTOR', direction='BROWSER', provider='OPERATOR',
                correlation_token_hash=str(uuid.uuid4()), state='REQUESTED', provenance='SIMULATED'))
    payload = body('CONTRACTOR_REPORT', appointment_id=appointment.id, expected_case_version=version,
        text='The contractor attended and repaired the flashing.')
    if explicit:
        payload['response_to_communication_id'] = request_ids[0]
    async with AsyncClient(transport=ASGITransport(app), base_url='http://test') as client:
        response = await client.post(f'/api/v1/cases/{cid}/demo-inputs', json=payload)
        assert response.status_code == 202, response.text
    async with session_scope() as session:
        requests = [await session.get(CommunicationModel, request_id) for request_id in request_ids]
        assert sum(request.state == 'ENDED' for request in requests) == ended_count
        if explicit:
            assert requests[0].state == 'ENDED'
            assert requests[1].state == 'REQUESTED'


@pytest.mark.asyncio
@pytest.mark.parametrize('mutation,expected', [
    ('valid', True), ('expired', False), ('wrong_person', False),
    ('wrong_type', False), ('scheduled', False), ('held', False),
])
async def test_read_options_require_current_tenant_window_and_ready_active_work(app_db, mutation, expected):
    from types import SimpleNamespace
    from sqlalchemy import select
    from app.agents.dependencies import CoordinatorDeps
    from app.agents.read_tools import find_appointment_options
    from app.models import AvailabilityWindowModel
    from app.schemas import AppointmentQuery
    from tests.test_hero_path import _seed_reference_data
    from tests.test_fixi_ui_support import _drive_case_to_scheduled

    prop, tenant, roofer, _ = await _seed_reference_data()
    cid, _, work, appointment = await _drive_case_to_scheduled(prop, tenant, roofer)
    async with session_scope() as session:
        if mutation != 'scheduled':
            await services.cancel_appointment(session, appointment_id=appointment.id,
                reason='Read option regression', actor=ActorContext('OPERATOR', 'test', str(uuid.uuid4())))
        case = await services.load_case(session, cid)
        window = (await session.execute(select(AvailabilityWindowModel).where(
            AvailabilityWindowModel.case_id == cid))).scalars().first()
        assert window is not None
        if mutation == 'expired':
            window.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        elif mutation == 'wrong_person':
            window.person_id = str(uuid.uuid4())
        elif mutation == 'wrong_type':
            window.person_type = 'CONTRACTOR'
        elif mutation == 'held':
            case.status = 'ESCALATED'
        window_id = window.id
        version = case.version
    deps = CoordinatorDeps(case_id=cid, snapshot_version=version, run_id=str(uuid.uuid4()), policy_snapshot={})
    result = await find_appointment_options(SimpleNamespace(deps=deps), AppointmentQuery(
        case_id=cid, work_order_id=work.id, contractor_id=roofer, tenant_availability_ids=[window_id]))
    assert bool(result.slots) is expected
    assert bool(deps.offered_slots) is expected

@pytest.mark.parametrize('kind', ['TENANT_REPLY', 'AVAILABILITY', 'TENANT_CONFIRMATION'])
def test_only_operator_can_mark_concerns_addressed(kind):
    from app.api.demo_inputs import DemoInput
    with pytest.raises(ValidationError, match='Only an operator'):
        DemoInput.model_validate(body(kind, resolved_concerns=['Damaged seal']))


def test_withdrawal_is_explicit_and_excludes_replacement_times():
    from app.api.demo_inputs import DemoInput
    parsed = DemoInput.model_validate(body('AVAILABILITY', withdraw_availability=True))
    assert parsed.withdraw_availability and not parsed.availability
    start = datetime.now(timezone.utc) + timedelta(days=1)
    with pytest.raises(ValidationError, match='not both'):
        DemoInput.model_validate(body('AVAILABILITY', withdraw_availability=True, availability=[{
            'start_at': start, 'end_at': start + timedelta(hours=2), 'timezone': 'Europe/London',
            'spoken_text': 'Confirmed tomorrow', 'confirmed_by_speaker': True}]))
