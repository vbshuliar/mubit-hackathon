"""Explicitly simulated human evidence. Only the coordinator can choose an action."""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select, text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_operator
from app.domain import services
from app.domain.errors import ConflictError, DomainError, NotFoundError, StaleVersionError
from app.domain.services import ActorContext
from app.models import AppointmentModel, CommunicationModel
from app.schemas import (AvailabilityInput, CommandResult, EvidenceRef, FactInput,
    ObservationSubmission, Provenance, ReportSubmission, SafetyAnswers, SourceType, validate_availability_windows)

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_operator)])
_NAMESPACE = uuid.UUID("94940cd0-d549-4453-ab43-29a046dbbfbc")


class DemoInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    input_id: uuid.UUID
    expected_case_version: int = Field(ge=1)
    kind: Literal["TENANT_REPLY", "AVAILABILITY", "CONTRACTOR_REPORT", "ATTENDANCE_OUTCOME", "TENANT_CONFIRMATION", "OPERATOR_UPDATE"]
    text: str = Field(min_length=1, max_length=4000)
    appointment_id: uuid.UUID | None = None
    response_to_communication_id: uuid.UUID | None = None
    safety_answers: SafetyAnswers | None = None
    availability: list[AvailabilityInput] = Field(default_factory=list, max_length=10)
    resolved_concerns: list[str] = Field(default_factory=list, max_length=50)
    withdraw_availability: bool = False
    confirms_resolved: bool | None = None
    attendance_outcome: Literal["NO_ACCESS", "NO_SHOW", "AWAITING_REPORT"] | None = None

    @model_validator(mode="after")
    def valid_shape(self):
        if not self.text.strip():
            raise ValueError("A response is required")
        if self.resolved_concerns and self.kind != "OPERATOR_UPDATE":
            raise ValueError("Only an operator update may mark concerns addressed")
        visit = self.kind in ("CONTRACTOR_REPORT", "ATTENDANCE_OUTCOME")
        if visit != (self.appointment_id is not None):
            raise ValueError("Appointment is required only for visit updates")
        if (self.kind == "TENANT_CONFIRMATION") != (self.confirms_resolved is not None):
            raise ValueError("Resolution confirmation requires an explicit yes or no")
        if (self.kind == "ATTENDANCE_OUTCOME") != (self.attendance_outcome is not None):
            raise ValueError("Attendance updates require an outcome")
        if self.kind == "AVAILABILITY" and not self.availability and not self.withdraw_availability:
            raise ValueError("At least one availability window is required")
        if self.kind not in ("TENANT_REPLY", "AVAILABILITY", "OPERATOR_UPDATE") and (self.availability or self.withdraw_availability or self.safety_answers is not None):
            raise ValueError("Safety and availability belong to an information response")
        if self.withdraw_availability and self.availability:
            raise ValueError("Withdraw existing times or supply replacement times, not both")
        validate_availability_windows(self.availability)
        return self


@router.post("/cases/{case_id}/demo-inputs", status_code=202)
async def record_demo_input(case_id: str, update: DemoInput,
    session: AsyncSession = Depends(get_session), operator: str = Depends(require_operator)):
    # SQLite write reservation serializes version checks, idempotency and evidence
    # writes. No model/network work happens inside this short transaction.
    await session.execute(sql_text("BEGIN IMMEDIATE"))
    case = await services.load_case(session, case_id)
    comm_id = str(uuid.uuid5(_NAMESPACE, f"{case_id}:{update.input_id}"))
    digest = hashlib.sha256(update.model_dump_json().encode()).hexdigest()
    existing = await session.get(CommunicationModel, comm_id)
    if existing:
        if existing.correlation_token_hash != digest:
            raise ConflictError("Input ID was already used for different content")
        return {"input_id": update.input_id, "result": CommandResult(status="NOOP", case_version=case.version)}
    if case.archive_batch_id or case.status in ("RESOLVED", "CANCELLED"):
        raise ConflictError("Reopen this case before adding new evidence")
    if case.version != update.expected_case_version:
        raise StaleVersionError("Case changed; review the latest state and submit again", case.version)
    appointment = None
    if update.appointment_id:
        appointment = await session.get(AppointmentModel, str(update.appointment_id))
        if not appointment or appointment.case_id != case_id:
            raise NotFoundError("Appointment does not belong to this case")
        if appointment.status in ("CANCELLED", "FAILED"):
            raise ConflictError("Cannot submit evidence against a cancelled or failed appointment")
        work = await services.load_work_order(session, case_id, appointment.work_order_id)
        if work.status in ("COMPLETED", "CANCELLED"):
            raise ConflictError("This work order has already finished")
    if update.kind == "TENANT_CONFIRMATION" and case.status != "AWAITING_CONFIRMATION":
        raise ConflictError("Tenant resolution confirmation is only accepted after required work is complete")
    responding_to = None
    if update.response_to_communication_id:
        responding_to = await session.get(CommunicationModel, str(update.response_to_communication_id))
        if not responding_to or responding_to.case_id != case_id:
            raise NotFoundError("Response request does not belong to this case")
        if responding_to.state != "REQUESTED":
            raise ConflictError("This response request is no longer pending")
        tenant_input = update.kind in ("TENANT_REPLY", "AVAILABILITY", "TENANT_CONFIRMATION")
        if (responding_to.tenant_id is not None) != tenant_input:
            raise ConflictError("Response must come from the requested person")
        if (responding_to.purpose == "FOLLOW_UP") != (update.kind == "TENANT_CONFIRMATION"):
            raise ConflictError("Resolution requests require an explicit resolution confirmation")
        supplies_report = update.kind == "CONTRACTOR_REPORT" or (
            update.kind == "ATTENDANCE_OUTCOME" and update.attendance_outcome != "AWAITING_REPORT"
        )
        if (responding_to.purpose == "CONTRACTOR") != supplies_report:
            raise ConflictError("A specialist-report request must be answered with visit evidence")
    now = datetime.now(timezone.utc)
    actor = ActorContext("OPERATOR", operator, str(update.input_id))
    comm = CommunicationModel(id=comm_id, case_id=case_id,
        tenant_id=case.tenant_id if update.kind in ("TENANT_REPLY", "AVAILABILITY", "TENANT_CONFIRMATION") else None,
        purpose="FOLLOW_UP" if update.kind == "TENANT_CONFIRMATION" else "INTAKE", direction="BROWSER",
        provider="OPERATOR", correlation_token_hash=digest, state="ENDED", provenance=Provenance.SIMULATED,
        started_at=now, ended_at=now)
    session.add(comm)
    await session.flush()
    evidence = EvidenceRef(source_type=SourceType.OPERATOR, source_id=comm_id, observed_at=now, provenance=Provenance.SIMULATED)
    if appointment and update.attendance_outcome != "AWAITING_REPORT":
        text = update.text if update.kind == "CONTRACTOR_REPORT" else f"Attendance outcome: {update.attendance_outcome}. {update.text}"
        comm.transcript = [{"turn_id": str(update.input_id), "speaker": "USER", "text": text, "time_in_call_secs": 0}]
        _, result = await services.record_contractor_report(session,
            submission=ReportSubmission(work_order_id=appointment.work_order_id, appointment_id=appointment.id,
                contractor_id=appointment.contractor_id, text=text, observed_at=now),
            source_ref=evidence, provenance=Provenance.SIMULATED, actor=actor)
    elif appointment:
        # Persist the missing-report evidence in the same event which wakes the agent.
        result = await services.mark_attendance_window_ended(session, case_id=case_id, appointment_id=appointment.id, actor=actor, provenance=Provenance.SIMULATED)
        comm.transcript = [{"turn_id": str(update.input_id), "speaker": "USER", "text": update.text, "time_in_call_secs": 0}]
        if result.status == "NOOP":
            raise ConflictError("Visit window has already been marked as ended; submit the contractor report next")
    else:
        facts = []
        if update.safety_answers:
            facts = [FactInput(field=name, value=value, spoken_text=update.text, confirmed_by_speaker=True)
                for name, value in update.safety_answers.model_dump(mode="json", exclude_unset=True).items()]
        result = await services.record_observations(session, case_id=case_id, communication_id=comm_id,
            submission=ObservationSubmission(communication_id=comm_id, facts=facts, availability=update.availability,
                tenant_confirms_resolved=update.confirms_resolved, source_text=update.text,
                withdraw_availability=update.withdraw_availability, resolved_concerns=update.resolved_concerns), actor=actor)
    # Close only requests addressed to the simulated speaker. Contractor reports do
    # not answer an unrelated tenant safety question or resolution confirmation.
    if not responding_to and update.kind in ("TENANT_REPLY", "AVAILABILITY", "TENANT_CONFIRMATION", "OPERATOR_UPDATE"):
        pending = (await session.execute(select(CommunicationModel).where(
            CommunicationModel.case_id == case_id, CommunicationModel.state == "REQUESTED"))).scalars().all()
        for request in pending:
            matches_person = (request.tenant_id is None) == (update.kind == "OPERATOR_UPDATE")
            matches_purpose = (request.purpose == "FOLLOW_UP") == (update.kind == "TENANT_CONFIRMATION")
            supplies_required_data = request.purpose != "CONTRACTOR" and (
                request.purpose != "AVAILABILITY" or bool(update.availability)
            )
            if matches_person and matches_purpose and supplies_required_data:
                request.state = "ENDED"
                request.ended_at = now
    if responding_to:
        if responding_to.purpose != "AVAILABILITY" or update.availability:
            responding_to.state = "ENDED"
            responding_to.ended_at = now
    elif update.kind == "CONTRACTOR_REPORT" or (
        update.kind == "ATTENDANCE_OUTCOME" and update.attendance_outcome != "AWAITING_REPORT"
    ):
        # Requests have no structural appointment linkage. Auto-close only a
        # single pending report request; multiple waits need an explicit request ID.
        pending_reports = (await session.execute(select(CommunicationModel).where(
            CommunicationModel.case_id == case_id, CommunicationModel.state == "REQUESTED",
            CommunicationModel.tenant_id.is_(None), CommunicationModel.purpose == "CONTRACTOR"))).scalars().all()
        if len(pending_reports) == 1:
            pending_reports[0].state = "ENDED"
            pending_reports[0].ended_at = now
    return {"input_id": update.input_id, "result": result}
