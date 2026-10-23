"""Scoped read tools exposed to the coordinator agent (docs/10).

Every tool re-validates that the requested record belongs to the case in
`RunContext.deps` -- dependency injection supplies scope, it does not by
itself enforce it (docs/09). `get_case_snapshot` is not registered: the
full snapshot is already the run's prompt content (docs/10).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, JsonValue

from pydantic_ai import ModelRetry, RunContext
from pydantic_ai.tools import ToolDefinition
from sqlalchemy import select

from app.agents.dependencies import CoordinatorDeps
from app.db import session_scope
from app.domain import services
from app.domain.errors import NotFoundError
from app.integrations.booking import mock_booking_connector
from app.models import (
    AvailabilityWindowModel,
    ContractorModel,
    PropertyModel,
    CaseEventModel,
    CommunicationModel,
    ContractorCandidateModel,
    ContractorReportModel,
    ResearchSnapshotModel,
)
from app.schemas import (
    AppointmentOptions,
    AppointmentQuery,
    CaseEvent,
    Communication,
    ContractorCandidate,
    ContractorReport,
    ContractorSearchResult,
    ReadEvents,
    RecordRef,
    ResearchSnapshot,
)


class SnapshotEvidenceReference(BaseModel):
    """Evidence already in the prompt; no second copy of human text is needed."""
    status: Literal["ALREADY_IN_SNAPSHOT"] = "ALREADY_IN_SNAPSHOT"
    record_id: UUID
    snapshot_path: str
    instruction: str = "Use the evidence at this path in the supplied snapshot; do not reread it."
    additional_fields: dict[str, JsonValue] = Field(default_factory=dict)


def _snapshot_reference(
    deps: CoordinatorDeps,
    collection: Literal["latest_reports", "communications", "recent_events"],
    record: ContractorReport | Communication | CaseEvent,
) -> SnapshotEvidenceReference | None:
    if deps.snapshot is None:
        return None
    existing = next((item for item in getattr(deps.snapshot, collection) if item.id == record.id), None)
    if existing is None or existing != record:
        return None  # Older or changed evidence must be returned in full.
    from app.agents.coordinator import _compact_snapshot

    # Use the exact prompt projection, retaining metadata it omits. Nested
    # event payloads are already preserved there (duplicated spoken_text is
    # represented once by source_text); do not repeat the entire payload.
    projected = next(item for item in _compact_snapshot(deps.snapshot)[collection]
                     if item["id"] == str(record.id))
    extra = {key: value for key, value in record.model_dump(mode="json").items()
             if key not in projected and key != "correlation_token_hash"}
    if "recording" in extra:
        extra["recording"]["media_path"] = None
    reference = SnapshotEvidenceReference(record_id=record.id,
        snapshot_path=f"{collection}[id={record.id}]", additional_fields=extra)
    # A small event can be shorter than its reference envelope.
    return reference if len(reference.model_dump_json()) < len(record.model_dump_json()) else None


async def prepare_missing_evidence(
    ctx: RunContext[CoordinatorDeps], tool: ToolDefinition,
) -> ToolDefinition | None:
    """Hide a redundant read only after proving full, unchanged DB coverage.

    Do not infer completeness from snapshot length: reports/events are capped,
    and tests/collection callers may intentionally supply partial snapshots.
    Each preparation uses a short read transaction before the model request.
    """
    snapshot = ctx.deps.snapshot
    if snapshot is None or str(snapshot.case.id) != ctx.deps.case_id:
        return tool
    collections = {
        "read_report": ("latest_reports", ContractorReportModel, ContractorReport),
        "read_communication": ("communications", CommunicationModel, Communication),
        "list_case_events": ("recent_events", CaseEventModel, CaseEvent),
    }
    entry = collections.get(tool.name)
    if entry is None:
        return tool
    collection, row_type, schema = entry
    async with session_scope() as session:
        try:
            case = await services.load_case(session, ctx.deps.case_id)
        except NotFoundError:
            return tool
        if case.version != ctx.deps.snapshot_version:
            return tool
        rows = (await session.execute(select(row_type).where(
            row_type.case_id == ctx.deps.case_id))).scalars().all()
        current = {row.id: schema.model_validate(row) for row in rows}
    supplied = {str(item.id): item for item in getattr(snapshot, collection)}
    return None if current == supplied else tool


def _check_scope(deps: CoordinatorDeps, case_id) -> None:
    if str(case_id) != deps.case_id:
        raise ModelRetry("that record is not part of the current case; use only IDs from the supplied case snapshot")


async def read_report(ctx: RunContext[CoordinatorDeps], ref: RecordRef) -> ContractorReport | SnapshotEvidenceReference:
    """Read a report missing from latest_reports in the supplied snapshot. Already supplied reports need no read; unchanged ones return a reference."""
    _check_scope(ctx.deps, ref.case_id)
    async with session_scope() as session:
        report = await session.get(ContractorReportModel, str(ref.record_id))
        if report is None or report.case_id != ctx.deps.case_id:
            raise ModelRetry(f"no report {ref.record_id} found in this case")
        model = ContractorReport.model_validate(report)
        return _snapshot_reference(ctx.deps, "latest_reports", model) or model


async def read_communication(ctx: RunContext[CoordinatorDeps], ref: RecordRef) -> Communication | SnapshotEvidenceReference:
    """Read communication evidence missing from the supplied snapshot. Already supplied transcripts need no read; unchanged ones return a reference."""
    _check_scope(ctx.deps, ref.case_id)
    async with session_scope() as session:
        comm = await session.get(CommunicationModel, str(ref.record_id))
        if comm is None or comm.case_id != ctx.deps.case_id:
            raise ModelRetry(f"no communication {ref.record_id} found in this case")
        model = Communication.model_validate(comm)
        reference = _snapshot_reference(ctx.deps, "communications", model)
        if reference is not None:
            return reference
        model.recording.media_path = None  # never expose the audio file path to the model
        return model


async def list_case_events(ctx: RunContext[CoordinatorDeps], query: ReadEvents) -> list[CaseEvent | SnapshotEvidenceReference]:
    """Read missing case history ordered by sequence after after_seq. Use recent_events directly when sufficient. Overlapping unchanged events return references; missing events return in full."""
    _check_scope(ctx.deps, query.case_id)
    async with session_scope() as session:
        rows = (
            await session.execute(
                select(CaseEventModel)
                .where(CaseEventModel.case_id == ctx.deps.case_id, CaseEventModel.seq > query.after_seq)
                .order_by(CaseEventModel.seq)
                .limit(min(query.limit, 100))
            )
        ).scalars().all()
        events = [CaseEvent.model_validate(e) for e in rows]
        return [_snapshot_reference(ctx.deps, "recent_events", event) or event for event in events]


async def read_research(ctx: RunContext[CoordinatorDeps], ref: RecordRef) -> ContractorSearchResult:
    """Reads a completed DISCOVER_CONTRACTORS result: the ResearchSnapshot
    plus every UNVERIFIED ContractorCandidate it produced. A candidate here
    is web evidence, never an approved contractor -- the coordinator must
    not treat verification_status as anything other than UNVERIFIED from
    this tool alone (docs/12, CLAUDE.md)."""
    _check_scope(ctx.deps, ref.case_id)
    async with session_scope() as session:
        snapshot = await session.get(ResearchSnapshotModel, str(ref.record_id))
        if snapshot is None or snapshot.case_id != ctx.deps.case_id:
            raise ModelRetry(f"no research {ref.record_id} found in this case")
        candidates = (
            await session.execute(
                select(ContractorCandidateModel).where(ContractorCandidateModel.research_id == snapshot.id)
            )
        ).scalars().all()
        return ContractorSearchResult(
            research=ResearchSnapshot.model_validate(snapshot),
            candidates=[ContractorCandidate.model_validate(c) for c in candidates],
        )


async def find_appointment_options(ctx: RunContext[CoordinatorDeps], query: AppointmentQuery) -> AppointmentOptions:
    _check_scope(ctx.deps, query.case_id)
    async with session_scope() as session:
        # The other four tools all raise ModelRetry on not-found, which
        # pydantic_ai turns into a cheap in-run re-prompt. load_work_order
        # instead raises NotFoundError (a plain DomainError) -- uncaught,
        # that aborts the whole run and burns a full COORDINATE retry (a
        # fresh Gemini call) on what should just be a stale ID the model
        # can self-correct from. Same bug class as tonight's earlier
        # UsageLimits fix.
        try:
            work_order = await services.load_work_order(session, ctx.deps.case_id, str(query.work_order_id))
        except NotFoundError:
            raise ModelRetry(f"no work order {query.work_order_id} found in this case; use only IDs from the supplied case snapshot")

        contractor = await session.get(ContractorModel, str(query.contractor_id))
        if contractor is None or contractor.approval_status != "APPROVED":
            return AppointmentOptions(slots=[], reason_if_empty="Choose an approved contractor from this case snapshot")
        if work_order.trade.value not in contractor.trades:
            return AppointmentOptions(slots=[], reason_if_empty="This contractor does not provide the required trade")
        case = await services.load_case(session, ctx.deps.case_id)
        if case.status != "ACTIVE" or work_order.status != "READY":
            return AppointmentOptions(slots=[], reason_if_empty="Only READY work on an ACTIVE case can be scheduled; resolve the current hold or visit first")
        prop = await session.get(PropertyModel, case.property_id)
        from app.domain.policy import contractor_covers_postcode
        if prop is None or not contractor_covers_postcode(contractor.service_postcodes, prop.postcode):
            return AppointmentOptions(slots=[], reason_if_empty="This contractor does not cover the property's postcode; select another approved contractor")

        windows = (
            await session.execute(
                select(AvailabilityWindowModel).where(
                    AvailabilityWindowModel.case_id == ctx.deps.case_id,
                    AvailabilityWindowModel.id.in_([str(i) for i in query.tenant_availability_ids]),
                    AvailabilityWindowModel.person_type == "TENANT",
                    AvailabilityWindowModel.person_id == case.tenant_id,
                    AvailabilityWindowModel.confirmed_at.is_not(None),
                    AvailabilityWindowModel.expires_at > datetime.now(timezone.utc),
                    AvailabilityWindowModel.end_at > datetime.now(timezone.utc),
                )
            )
        ).scalars().all()
        if not windows:
            return AppointmentOptions(slots=[], reason_if_empty="no matching tenant availability window in this case")

        slots = await mock_booking_connector.list_slots(session, query, trade=work_order.trade)

    valid = [
        s for s in slots
        if any(w.start_at <= s.start_at and s.end_at <= w.end_at for w in windows)
    ]
    if not valid:
        return AppointmentOptions(slots=[], reason_if_empty="no contractor slot intersects the cited availability")
    for slot in valid:
        ctx.deps.offered_slots[(str(query.work_order_id), str(query.contractor_id), slot.slot_id)] = {
            str(w.id) for w in windows if w.start_at <= slot.start_at and slot.end_at <= w.end_at
        }
    return AppointmentOptions(slots=valid)
