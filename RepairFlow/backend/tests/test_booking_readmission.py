"""A known failed booking can recover without retrying uncertain effects."""
import uuid

import pytest

from app.db import session_scope
from app.domain import services
from app.domain.errors import ConflictError
from app.domain.services import ActorContext
from app.orchestration.executor import admit_proposal
from app.schemas import ActionProposal, ScheduleVisit
from tests.test_fixi_ui_support import _drive_case_to_scheduled
from tests.test_hero_path import _seed_reference_data

ACTOR = ActorContext('OPERATOR', 'test', 'booking-recovery')


async def proposal_fixture():
    prop, tenant, roofer, _ = await _seed_reference_data()
    cid, _, work, appointment = await _drive_case_to_scheduled(prop, tenant, roofer)
    async with session_scope() as session:
        await services.cancel_appointment(session, appointment_id=appointment.id, reason='Recovery fixture', actor=ACTOR)
        snapshot = await services.load_case_snapshot(session, cid)
    return ActionProposal(case_id=cid, expected_case_version=snapshot.snapshot_version,
        trigger_event_id=uuid.uuid4(), decision_summary='Book a returned slot', evidence_refs=[],
        action=ScheduleVisit(work_order_id=work.id, contractor_id=roofer,
            slot_id='retry-test-slot', tenant_availability_ids=[w.id for w in snapshot.availability]))


@pytest.mark.asyncio
@pytest.mark.parametrize('state,reconcile,allowed', [
    ('FAILED', False, True), ('REJECTED', False, True), ('FAILED', True, False),
    ('UNKNOWN', False, False), ('PENDING', False, False), ('RUNNING', False, False),
    ('SUCCEEDED', False, False), ('AWAITING_APPROVAL', False, False),
])
async def test_new_version_booking_retry_requires_conclusive_failure(app_db, state, reconcile, allowed):
    proposal = await proposal_fixture()
    async with session_scope() as session:
        original = await admit_proposal(session, proposal, ACTOR)
        original.state = state
        original.result = {'status': 'REJECTED', 'error': {'reconciliation_required': reconcile}}
        case = await services.load_case(session, str(proposal.case_id))
        services.bump_version(case)
        retry_proposal = proposal.model_copy(update={'expected_case_version': case.version, 'trigger_event_id': uuid.uuid4()})
        if not allowed:
            with pytest.raises(ConflictError):
                await admit_proposal(session, retry_proposal, ACTOR)
            return
        retry = await admit_proposal(session, retry_proposal, ACTOR)
        assert retry.id != original.id
        assert retry.idempotency_key.endswith(f':v{case.version}')
        replay = await admit_proposal(session, retry_proposal, ACTOR)
        assert replay.id == retry.id
        retry.state = 'UNKNOWN'
        services.bump_version(case)
        next_proposal = retry_proposal.model_copy(update={'expected_case_version': case.version, 'trigger_event_id': uuid.uuid4()})
        with pytest.raises(ConflictError):
            await admit_proposal(session, next_proposal, ACTOR)


@pytest.mark.asyncio
async def test_same_version_changed_booking_cannot_bypass_failure_idempotency(app_db):
    proposal = await proposal_fixture()
    async with session_scope() as session:
        original = await admit_proposal(session, proposal, ACTOR)
        original.state = 'FAILED'
        original.result = {'status': 'REJECTED'}
        assert (await admit_proposal(session, proposal, ACTOR)).id == original.id
        with pytest.raises(ConflictError):
            await admit_proposal(session, proposal.model_copy(update={'trigger_event_id': uuid.uuid4()}), ACTOR)


@pytest.mark.asyncio
@pytest.mark.parametrize('reservation_status,allowed', [('RESERVED', False), ('CANCELLED', True)])
async def test_booking_retry_requires_confirmed_compensation(app_db, reservation_status, allowed):
    from sqlalchemy import select
    from app.models import MockReservationModel

    proposal = await proposal_fixture()
    async with session_scope() as session:
        original = await admit_proposal(session, proposal, ACTOR)
        original.state = 'FAILED'
        original.result = {'status': 'REJECTED', 'error': {'reconciliation_required': False}}
        reservation = (await session.execute(select(MockReservationModel).where(
            MockReservationModel.work_order_id == str(proposal.action.work_order_id)))).scalars().one()
        reservation.action_id = original.id
        reservation.status = reservation_status
        await session.flush()
        case = await services.load_case(session, str(proposal.case_id))
        services.bump_version(case)
        retry_proposal = proposal.model_copy(update={'expected_case_version': case.version, 'trigger_event_id': uuid.uuid4()})
        if allowed:
            assert (await admit_proposal(session, retry_proposal, ACTOR)).id != original.id
        else:
            with pytest.raises(ConflictError):
                await admit_proposal(session, retry_proposal, ACTOR)
