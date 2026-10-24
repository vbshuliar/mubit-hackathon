"""Offline regressions for recovery, cancellation races, and visit identity."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db import session_scope
from app.main import app
from app.domain import services
from app.domain.errors import PolicyRejectedError
from app.domain.services import ActorContext
from app.models import ActionRecordModel, AppointmentModel, CommunicationModel, WorkOrderModel, AvailabilityWindowModel
from app.orchestration.executor import execute_action
from app.schemas import ActionProposal, AvailabilityInput, EvidenceRef, ObservationSubmission, ReportSubmission, RequestInformation
from tests.test_hero_path import _seed_reference_data, uid
from tests.test_fixi_ui_support import _drive_case_to_scheduled, _drive_case_to_resolved

ACTOR = ActorContext("OPERATOR", "test", "test")

async def scheduled():
    prop, tenant, roofer, other = await _seed_reference_data()
    cid, coordinator, work, appointment = await _drive_case_to_scheduled(prop, tenant, roofer)
    return cid, tenant, roofer, other, work, appointment

async def report(session, work, appointment, contractor):
    return await services.record_contractor_report(session,
        submission=ReportSubmission(work_order_id=work.id, appointment_id=appointment.id,
            contractor_id=contractor, text="Repair completed", observed_at=datetime.now(timezone.utc)),
        source_ref=EvidenceRef(source_type="OPERATOR", source_id=uid(), observed_at=datetime.now(timezone.utc), provenance="SIMULATED"),
        provenance="SIMULATED", actor=ACTOR)

@pytest.mark.asyncio
async def test_report_must_match_visit_work_and_contractor(app_db):
    cid, tenant, roofer, other, work, appointment = await scheduled()
    async with session_scope() as session:
        with pytest.raises(PolicyRejectedError, match="match"):
            await report(session, work, appointment, other)
        second = WorkOrderModel(id=uid(), case_id=cid, issue_id=work.issue_id, kind="REPAIR", trade="ROOFING",
            scope="different work", status="READY", required_for_resolution=True)
        session.add(second)
        await session.flush()
        with pytest.raises(PolicyRejectedError, match="match"):
            await report(session, second, appointment, roofer)

@pytest.mark.asyncio
async def test_report_from_old_attempt_cannot_complete_new_visit(app_db):
    cid, tenant, roofer, other, work, appointment = await scheduled()
    async with session_scope() as session:
        session.add(AppointmentModel(id=uid(), case_id=cid, work_order_id=work.id, contractor_id=roofer,
            slot_id="new", start_at=appointment.start_at, end_at=appointment.end_at, status="PENDING",
            connector="MOCK", action_id=appointment.action_id, attempt_number=2, availability_revision=1, provenance="SIMULATED"))
    async with session_scope() as session:
        with pytest.raises(PolicyRejectedError, match="earlier visit"):
            await report(session, work, appointment, roofer)

@pytest.mark.asyncio
@pytest.mark.parametrize("state", ["CANCELLED", "ESCALATED"])
async def test_queued_action_cannot_execute_after_case_hold(app_db, state):
    cid, tenant, roofer, other, work, appointment = await scheduled()
    async with session_scope() as session:
        case = await services.load_case(session, cid)
        proposal = ActionProposal(case_id=cid, expected_case_version=case.version, trigger_event_id=uuid.uuid4(),
            decision_summary="Request current details", evidence_refs=[],
            action=RequestInformation(recipient="TENANT", purpose="INTAKE", questions=["More details?"]))
        action = ActionRecordModel(id=uid(), case_id=cid, kind="REQUEST_INFORMATION", idempotency_key=uid(),
            payload_hash="test", proposal=proposal.model_dump(mode="json"), state="PENDING")
        session.add(action)
        action_id = action.id
        case.status = state
    result = await execute_action(action_id)
    assert result.status == "REJECTED"
    async with session_scope() as session:
        assert (await session.get(ActionRecordModel, action_id)).state == "FAILED"

@pytest.mark.asyncio
async def test_cancel_case_retires_appointments_and_work(app_db):
    cid, tenant, roofer, other, work, appointment = await scheduled()
    async with session_scope() as session:
        version = (await services.load_case(session, cid)).version
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
        response = await client.post(f"/api/v1/cases/{cid}/cancel", json={"version": version, "reason": "Tenant withdrew request"})
        assert response.status_code == 202, response.text
    async with session_scope() as session:
        assert (await session.get(AppointmentModel, appointment.id)).status == "CANCELLED"
        assert (await session.get(WorkOrderModel, work.id)).status == "CANCELLED"

@pytest.mark.asyncio
async def test_reopen_preserves_history_and_creates_followup_work(app_db):
    prop, tenant, roofer, _ = await _seed_reference_data()
    cid = await _drive_case_to_resolved(prop, tenant, roofer)
    async with session_scope() as session:
        version = (await services.load_case(session, cid)).version
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
        response = await client.post(f"/api/v1/cases/{cid}/reopen", json={"version": version, "reason": "Leak returned"})
        assert response.status_code == 202, response.text
    async with session_scope() as session:
        works = (await session.execute(select(WorkOrderModel).where(WorkOrderModel.case_id == cid))).scalars().all()
        assert sorted(str(w.status.value) for w in works) == ["COMPLETED", "READY"]
        assert (await services.load_case(session, cid)).status == "ESCALATED"
        assert (await services.load_issue(session, cid)).tenant_resolution_confirmed_at is None

@pytest.mark.asyncio
async def test_confirmation_cannot_be_recorded_before_completion(app_db):
    cid, tenant, roofer, other, work, appointment = await scheduled()
    async with session_scope() as session:
        comm = CommunicationModel(id=uid(), case_id=cid, tenant_id=tenant, purpose="FOLLOW_UP",
            direction="BROWSER", correlation_token_hash=uid(), state="ENDED", provenance="SIMULATED")
        session.add(comm)
        await session.flush()
        with pytest.raises(PolicyRejectedError, match="awaiting confirmation"):
            await services.record_observations(session, case_id=cid, communication_id=comm.id,
                submission=ObservationSubmission(communication_id=comm.id, source_text="Yes", tenant_confirms_resolved=True), actor=ACTOR)

@pytest.mark.asyncio
async def test_new_availability_withdraws_old_windows(app_db):
    cid, tenant, roofer, other, work, appointment = await scheduled()
    async with session_scope() as session:
        old = (await session.execute(select(AvailabilityWindowModel).where(AvailabilityWindowModel.case_id == cid))).scalars().all()
        comm = CommunicationModel(id=uid(), case_id=cid, tenant_id=tenant, purpose="INTAKE",
            direction="BROWSER", correlation_token_hash=uid(), state="ENDED", provenance="SIMULATED")
        session.add(comm)
        await session.flush()
        start = datetime.now(timezone.utc) + timedelta(days=8)
        await services.record_observations(session, case_id=cid, communication_id=comm.id,
            submission=ObservationSubmission(communication_id=comm.id, source_text="Changed availability", availability=[AvailabilityInput(
                start_at=start, end_at=start+timedelta(hours=4), timezone="UTC", spoken_text="Only this new time", confirmed_by_speaker=True)]), actor=ACTOR)
        assert all(w.expires_at <= datetime.now(timezone.utc) for w in old)

@pytest.mark.asyncio
async def test_negative_confirmation_creates_repair_and_new_yes_clears_only_dispute(app_db):
    cid, tenant, roofer, other, work, appointment = await scheduled()
    async with session_scope() as session:
        case = await services.load_case(session, cid)
        case.status = "AWAITING_CONFIRMATION"
        original = await session.get(WorkOrderModel, work.id)
        original.status = "COMPLETED"
        issue = await services.load_issue(session, cid)
        issue.tenant_resolution_confirmed_at = datetime.now(timezone.utc)
        comm = CommunicationModel(id=uid(), case_id=cid, tenant_id=tenant, purpose="FOLLOW_UP",
            direction="BROWSER", correlation_token_hash=uid(), state="ENDED", provenance="SIMULATED")
        session.add(comm)
        await session.flush()
        await services.record_observations(session, case_id=cid, communication_id=comm.id,
            submission=ObservationSubmission(communication_id=comm.id, source_text="It still leaks", tenant_confirms_resolved=False), actor=ACTOR)
        works = (await session.execute(select(WorkOrderModel).where(WorkOrderModel.case_id == cid))).scalars().all()
        followup = next(w for w in works if w.id != work.id)
        assert original.status == "COMPLETED"
        assert followup.status == "READY" and followup.approved_limit_pence is None
        assert issue.tenant_resolution_confirmed_at is None
        assert case.status == "ACTIVE"
        followup.status = "COMPLETED"
        await services.maybe_advance_to_awaiting_confirmation(session, case)
        assert case.status == "AWAITING_CONFIRMATION"
        issue.unresolved_concerns = [*issue.unresolved_concerns, "independent damp concern"]
        comm2 = CommunicationModel(id=uid(), case_id=cid, tenant_id=tenant, purpose="FOLLOW_UP",
            direction="BROWSER", correlation_token_hash=uid(), state="ENDED", provenance="SIMULATED")
        session.add(comm2)
        await session.flush()
        await services.record_observations(session, case_id=cid, communication_id=comm2.id,
            submission=ObservationSubmission(communication_id=comm2.id, source_text="Repair fixed now", tenant_confirms_resolved=True), actor=ACTOR)
        assert issue.unresolved_concerns == ["independent damp concern"]
        assert issue.tenant_resolution_confirmed_at is not None

@pytest.mark.asyncio
async def test_booking_result_after_cancellation_is_compensated(app_db):
    from app.orchestration.executor import _apply_schedule_result
    from app.schemas import BookingOutcome, BookingRequest
    from app.models import MockReservationModel
    cid, tenant, roofer, other, work, appointment = await scheduled()
    async with session_scope() as session:
        case = await services.load_case(session, cid)
        case.status = "CANCELLED"
        record = await session.get(ActionRecordModel, appointment.action_id)
        action = record.proposal["action"]
        request = BookingRequest(case_id=cid, work_order_id=work.id, contractor_id=roofer,
            slot_id=appointment.slot_id, tenant_availability_ids=action["tenant_availability_ids"],
            access_confirmed=True, authorized_limit_pence=25000, idempotency_key=record.idempotency_key)
    outcome = BookingOutcome(status="CONFIRMED", provider_booking_id=appointment.provider_booking_id,
        confirmed_start=appointment.start_at, confirmed_end=appointment.end_at, provenance="SIMULATED")
    result = await _apply_schedule_result(appointment.action_id, work.id, request, 2, outcome)
    assert result.status == "REJECTED"
    async with session_scope() as session:
        appointments = (await session.execute(select(AppointmentModel).where(AppointmentModel.case_id == cid))).scalars().all()
        assert len(appointments) == 1
        reservation = (await session.execute(select(MockReservationModel).where(MockReservationModel.provider_booking_id == appointment.provider_booking_id))).scalar_one()
        assert reservation.status == "CANCELLED"

@pytest.mark.asyncio
async def test_withdraw_access_holds_booking_until_cancelled(app_db):
    cid, tenant, roofer, other, work, appointment = await scheduled()
    async with session_scope() as session:
        comm = CommunicationModel(id=uid(), case_id=cid, tenant_id=tenant, purpose="INTAKE",
            direction="BROWSER", correlation_token_hash=uid(), state="ENDED", provenance="SIMULATED")
        session.add(comm)
        await session.flush()
        await services.record_observations(session, case_id=cid, communication_id=comm.id,
            submission=ObservationSubmission(communication_id=comm.id, source_text="I cannot provide access at any time now",
                withdraw_availability=True), actor=ACTOR)
        case = await services.load_case(session, cid)
        assert case.status == "ESCALATED"
        assert "availability" in case.escalation_reason
        from app.models import CaseEventModel
        event = (await session.execute(select(CaseEventModel).where(
            CaseEventModel.case_id == cid, CaseEventModel.type == "AVAILABILITY_RECEIVED",
        ).order_by(CaseEventModel.seq.desc()).limit(1))).scalar_one()
        assert event.payload["withdraw_availability"] is True
        assert event.payload["window_count"] == 0
        version = case.version
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
        response = await client.post(f"/api/v1/cases/{cid}/resume", json={"version": version,
            "reason": "Continue", "resolved_hold_evidence": "Reviewed"})
        assert response.status_code == 422, response.text
    async with session_scope() as session:
        await services.cancel_appointment(session, appointment_id=appointment.id, reason="No tenant access", actor=ACTOR)
        assert await services.appointments_without_access(session, await services.load_case(session, cid)) == []

@pytest.mark.asyncio
async def test_cancel_while_waiting_for_tenant_confirmation(app_db):
    cid, tenant, roofer, other, work, appointment = await scheduled()
    async with session_scope() as session:
        case = await services.load_case(session, cid)
        case.status = "AWAITING_CONFIRMATION"
        version = case.version
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
        response = await client.post(f"/api/v1/cases/{cid}/cancel", json={"version": version, "reason": "Withdrawn"})
        assert response.status_code == 202, response.text

@pytest.mark.asyncio
async def test_existing_information_request_can_collect_missing_questions(app_db):
    cid, tenant, roofer, other, work, appointment = await scheduled()
    async with session_scope() as session:
        first = await services.request_information(session, case_id=cid,
            action=RequestInformation(recipient="TENANT", purpose="INTAKE", questions=["Any gas smell?"]), actor=ACTOR)
        expanded = await services.request_information(session, case_id=cid,
            action=RequestInformation(recipient="TENANT", purpose="INTAKE", questions=["Any gas smell?", "Any fire or smoke?"]), actor=ACTOR)
        assert first.resource_ids == expanded.resource_ids
        assert expanded.status == "APPLIED"
        comm = await session.get(CommunicationModel, str(first.resource_ids["communication_id"]))
        assert [t["text"] for t in comm.transcript if t["speaker"] == "AGENT"] == ["Any gas smell?", "Any fire or smoke?"]
        assert any(t["speaker"] == "USER" for t in comm.transcript)

@pytest.mark.asyncio
@pytest.mark.parametrize("recipient,purpose", [("TENANT", "CONTRACTOR"), ("OPERATOR", "FOLLOW_UP"), ("TENANT", "FOLLOW_UP")])
async def test_information_requests_cannot_impersonate_confirmation_or_contractor(app_db, recipient, purpose):
    cid, *_ = await scheduled()
    async with session_scope() as session:
        with pytest.raises(PolicyRejectedError):
            await services.request_information(session, case_id=cid,
                action=RequestInformation(recipient=recipient, purpose=purpose, questions=["Give an update"]), actor=ACTOR)

@pytest.mark.asyncio
async def test_resume_late_hold_after_resolution_creates_new_work(app_db):
    from app.schemas import Escalate
    prop, tenant, roofer, _ = await _seed_reference_data()
    cid = await _drive_case_to_resolved(prop, tenant, roofer)
    async with session_scope() as session:
        await services.escalate_to_human(session, case_id=cid,
            action=Escalate(reason_code="LATE_REPORT", operator_message="New concern after sign-off"),
            trigger_event_id=None, actor=ACTOR)
        version = (await services.load_case(session, cid)).version
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
        response = await client.post(f"/api/v1/cases/{cid}/resume", json={"version": version,
            "reason": "Inspect returned leak", "resolved_hold_evidence": "Operator reviewed the late report"})
        assert response.status_code == 202, response.text
    async with session_scope() as session:
        assert (await services.load_case(session, cid)).status == "ACTIVE"
        assert (await services.load_issue(session, cid)).tenant_resolution_confirmed_at is None
        ready = (await session.execute(select(WorkOrderModel).where(WorkOrderModel.case_id == cid,
            WorkOrderModel.status == "READY"))).scalars().all()
        assert len(ready) == 1

@pytest.mark.asyncio
async def test_operator_can_address_only_selected_concerns_with_evidence(app_db):
    cid, *_ = await scheduled()
    async with session_scope() as session:
        issue = await services.load_issue(session, cid)
        issue.unresolved_concerns = ["Damp patch needs inspection", "tenant reports issue still unresolved"]
        comm = CommunicationModel(id=uid(), case_id=cid, purpose="INTAKE", direction="BROWSER",
            correlation_token_hash=uid(), state="ENDED", provenance="SIMULATED")
        session.add(comm)
        await session.flush()
        result = await services.record_observations(session, case_id=cid, communication_id=comm.id,
            submission=ObservationSubmission(communication_id=comm.id, source_text="Inspected damp patch and confirmed fully dry",
                resolved_concerns=["Damp patch needs inspection"]), actor=ACTOR)
        assert issue.unresolved_concerns == ["tenant reports issue still unresolved"]
        assert result.status == "APPLIED"

@pytest.mark.asyncio
@pytest.mark.parametrize("selected,actor_type,text", [
    (["tenant reports issue still unresolved"], "OPERATOR", "Reviewed"),
    (["Not a current concern"], "OPERATOR", "Reviewed"),
    (["Damp patch needs inspection"], "COORDINATOR", "Reviewed"),
    (["Damp patch needs inspection"], "OPERATOR", " "),
])
async def test_concern_resolution_cannot_clear_unreviewed_or_tenant_dispute(app_db, selected, actor_type, text):
    cid, *_ = await scheduled()
    async with session_scope() as session:
        issue = await services.load_issue(session, cid)
        issue.unresolved_concerns = ["Damp patch needs inspection", "tenant reports issue still unresolved"]
        comm = CommunicationModel(id=uid(), case_id=cid, purpose="INTAKE", direction="BROWSER",
            correlation_token_hash=uid(), state="ENDED", provenance="SIMULATED")
        session.add(comm)
        await session.flush()
        with pytest.raises(PolicyRejectedError):
            await services.record_observations(session, case_id=cid, communication_id=comm.id,
                submission=ObservationSubmission(communication_id=comm.id, source_text=text, resolved_concerns=selected),
                actor=ActorContext(actor_type, "test", "test"))
        assert len(issue.unresolved_concerns) == 2

@pytest.mark.asyncio
@pytest.mark.parametrize("work_status", ["COMPLETED", "BLOCKED", "AWAITING_REPORT"])
async def test_historical_visit_without_current_access_does_not_block_resume(app_db, work_status):
    cid, tenant, roofer, other, work, appointment = await scheduled()
    async with session_scope() as session:
        current = await session.get(WorkOrderModel, work.id)
        current.status = work_status
        windows = (await session.execute(select(AvailabilityWindowModel).where(AvailabilityWindowModel.case_id == cid))).scalars().all()
        for window in windows:
            window.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        assert await services.appointments_without_access(session, await services.load_case(session, cid)) == []

@pytest.mark.asyncio
async def test_new_vulnerability_invalidates_prior_approval_before_execution(app_db):
    from app.schemas import Approval, RiskAssessment
    cid, tenant, roofer, other, work, appointment = await scheduled()
    async with session_scope() as session:
        case = await services.load_case(session, cid)
        action = await session.get(ActionRecordModel, appointment.action_id)
        action.approval = Approval(operator_id="operator", approved_at=datetime.now(timezone.utc),
            action_payload_hash=action.payload_hash, reason="Reviewed original plan",
            reviewed_risk=RiskAssessment.model_validate(case.risk)).model_dump(mode="json")
        action.state = "PENDING"
        (await session.get(WorkOrderModel, work.id)).status = "READY"
        case.risk = {**case.risk, "vulnerability_concern": "YES"}
    result = await execute_action(appointment.action_id)
    assert result.status == "REJECTED"
    assert "changed after approval" in result.error.message

@pytest.mark.asyncio
async def test_human_arranged_appointment_can_be_cancelled(app_db):
    cid, tenant, roofer, other, work, appointment = await scheduled()
    async with session_scope() as session:
        visit = await session.get(AppointmentModel, appointment.id)
        visit.connector = "HUMAN"
        visit.provider_booking_id = None
        outcome, _ = await services.cancel_appointment(session, appointment_id=visit.id,
            reason="Tenant withdrew access", actor=ACTOR)
        assert outcome.status == "CANCELLED"
        assert visit.status == "CANCELLED"
        assert (await session.get(WorkOrderModel, work.id)).status == "READY"

@pytest.mark.asyncio
async def test_failed_cancellation_cannot_create_replacement(app_db, monkeypatch):
    from app.integrations.booking import mock_booking_connector
    from app.schemas import CancellationOutcome
    cid, tenant, roofer, other, work, appointment = await scheduled()
    async def rejected(*args, **kwargs):
        return CancellationOutcome(status="REJECTED", reason="Reservation needs review", provenance="SIMULATED")
    monkeypatch.setattr(mock_booking_connector, "cancel", rejected)
    start = datetime.now(timezone.utc) + timedelta(days=3)
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
        response = await client.post(f"/api/v1/appointments/{appointment.id}/reschedule", json={
            "start_at": start.isoformat(), "end_at": (start+timedelta(hours=3)).isoformat(),
            "reason": "New time agreed", "arranged_with": "Tenant and contractor"})
        assert response.status_code == 422, response.text
    async with session_scope() as session:
        visits = (await session.execute(select(AppointmentModel).where(AppointmentModel.case_id == cid))).scalars().all()
        assert len(visits) == 1 and visits[0].status == "PENDING"

@pytest.mark.asyncio
async def test_successful_reschedule_keeps_work_scheduled_and_single_active_visit(app_db):
    cid, tenant, roofer, other, work, appointment = await scheduled()
    start = datetime.now(timezone.utc) + timedelta(days=3)
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
        response = await client.post(f"/api/v1/appointments/{appointment.id}/reschedule", json={
            "start_at": start.isoformat(), "end_at": (start+timedelta(hours=3)).isoformat(),
            "reason": "New time agreed", "arranged_with": "Tenant and contractor"})
        assert response.status_code == 202, response.text
    async with session_scope() as session:
        active = (await session.execute(select(AppointmentModel).where(AppointmentModel.case_id == cid,
            AppointmentModel.status.in_(["PENDING", "CONFIRMED"])))).scalars().all()
        assert len(active) == 1 and active[0].id != appointment.id
        current = await session.get(WorkOrderModel, work.id)
        assert current.status == "SCHEDULED" and current.contractor_id == roofer

@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["accept", "prerequisite"])
async def test_older_pending_report_cannot_override_later_received_evidence(app_db, operation):
    from app.models import ContractorReportModel
    from app.schemas import AcceptReport, AddPrerequisite
    cid, tenant, roofer, other, work, appointment = await scheduled()
    async with session_scope() as session:
        first_id, _ = await report(session, work, appointment, roofer)
        first = await session.get(ContractorReportModel, first_id)
        # Older claimed observation time still wins when the correction arrived later.
        second_id, _ = await services.record_contractor_report(session,
            submission=ReportSubmission(work_order_id=work.id, appointment_id=appointment.id,
                contractor_id=roofer, text="Correction: leak remains and scaffold is required",
                observed_at=datetime.now(timezone.utc) - timedelta(days=2)),
            source_ref=EvidenceRef(source_type="OPERATOR", source_id=uid(),
                observed_at=datetime.now(timezone.utc), provenance="SIMULATED"),
            provenance="SIMULATED", actor=ACTOR)
        with pytest.raises(PolicyRejectedError, match="newer report"):
            if operation == "accept":
                await services.accept_report(session, case_id=cid, action=AcceptReport(report_id=first_id, outcome="COMPLETED"),
                    action_id=appointment.action_id, trigger_event_id=uid(), actor=ACTOR)
            else:
                await services.add_prerequisite(session, case_id=cid,
                    action=AddPrerequisite(report_id=first_id, blocked_work_order_id=work.id,
                        prerequisite_trade="SCAFFOLDING", prerequisite_kind="SCAFFOLD_INSTALL",
                        prerequisite_scope="Access platform", reason="Unsafe ladder access"),
                    action_id=appointment.action_id, trigger_event_id=uid(), actor=ACTOR)
        assert (await session.get(WorkOrderModel, work.id)).status == "AWAITING_REPORT"
        assert first.interpretation_status == "PENDING"
        await services.require_current_report(session, await session.get(ContractorReportModel, second_id))

@pytest.mark.asyncio
async def test_report_receipt_event_orders_equal_server_timestamps(app_db):
    from app.models import ContractorReportModel
    cid, tenant, roofer, other, work, appointment = await scheduled()
    async with session_scope() as session:
        first_id, _ = await report(session, work, appointment, roofer)
        second_id, _ = await report(session, work, appointment, roofer)
        first = await session.get(ContractorReportModel, first_id)
        second = await session.get(ContractorReportModel, second_id)
        second.received_at = first.received_at
        await session.flush()
        with pytest.raises(PolicyRejectedError, match="supersedes"):
            await services.require_current_report(session, first)
        await services.require_current_report(session, second)
