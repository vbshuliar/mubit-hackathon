"""The one central Pydantic AI coordinator (docs/08/09/13).

GeminiCoordinator supplies the shared bounded execution path, also used
by MubitCoordinator. The factory selects the configured provider; auto
prefers Mubit, then Gemini, then the labelled offline fixture. A configured
provider failure propagates rather than falling back to another provider.
"""
from __future__ import annotations

import asyncio
import uuid

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.output import ToolOutput
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.settings import ModelSettings
from pydantic_ai.usage import UsageLimits

from app.agents.dependencies import CoordinatorDeps
from app.agents.instructions import COORDINATOR_INSTRUCTIONS
from app.agents.read_tools import prepare_missing_evidence, find_appointment_options, list_case_events, read_communication, read_report, read_research
from app.config import Settings
from app.schemas import ActionProposal, ApplyTriage, CaseSnapshot, RiskAssessment, ScheduleVisit, Wait, DiscoverContractors, RequestConfirmation, ResolveCase, AcceptReport, AddPrerequisite

# Verified live 2026-09-19: with 5 tools registered below, a case with even
# a handful of communications/events to review can legitimately need more
# than 3 tool calls before producing a final decision, which was tripping
# UsageLimitExceeded and forcing a silent retry cycle. Raised with headroom;
# still bounded, not unlimited (CLAUDE.md: "bounded retries").
MAX_MODEL_REQUESTS = 10
MAX_TOOL_CALLS = 8
# Per-request timeout (a single Gemini call). Kept separate from the outer
# run timeout below: with MAX_MODEL_REQUESTS raised to 10, a run needing
# several real round trips can legitimately take longer in total than any
# one request does, so reusing this value as the outer bound too would
# needlessly abort a run that's still correctly working (found alongside
# the fix above, not yet hit live).
MODEL_REQUEST_TIMEOUT_SECONDS = 60
RUN_TIMEOUT_SECONDS = 120


def validate_workflow_action(snapshot: CaseSnapshot, action) -> None:
    """Reject impossible workflow shortcuts before the model finishes its run."""
    from app.domain.policy import contractor_covers_postcode, has_unknown_critical_safety_fact, is_hazard

    if (isinstance(action, ApplyTriage)
            and has_unknown_critical_safety_fact(snapshot.case.risk)
            and not is_hazard(snapshot.case.risk) and not is_hazard(action.risk)):
        raise ModelRetry("Critical safety answers are still UNKNOWN. Use REQUEST_INFORMATION to ask the tenant the missing safety questions before APPLY_TRIAGE. Preserve unknown answers; an approval request does not supply missing evidence.")

    if isinstance(action, (AcceptReport, AddPrerequisite)):
        report = next((r for r in snapshot.latest_reports if r.id == action.report_id), None)
        if report is None or report.interpretation_status != "PENDING":
            ready = [str(w.id) for w in snapshot.work_orders if w.status == "READY"]
            raise ModelRetry(
                "Only PENDING reports may be interpreted. This report is missing or already applied; "
                "do not accept it again or add another prerequisite from it. "
                f"Remaining READY work order IDs: {ready}. Schedule eligible remaining work (including scaffold removal) "
                "using find_appointment_options; request confirmation only after all required work is completed."
            )
    from app.agents.decision_validation import validate_decision_details
    validate_decision_details(snapshot, action)

    if isinstance(action, DiscoverContractors):
        eligible = [c for c in snapshot.approved_contractors if action.trade in c.trades
                    and contractor_covers_postcode(c.service_postcodes, snapshot.property.postcode)]
        if eligible:
            raise ModelRetry("Approved contractors already cover this trade and postcode. Use them: request tenant availability if missing, otherwise call find_appointment_options. Do not perform unnecessary contractor research.")
        if any(e.type == "RESEARCH_COMPLETED" and e.payload.get("trade") == action.trade.value for e in snapshot.recent_events):
            raise ModelRetry("Research for this trade already completed. Read its result and request operator verification or escalate when no approved supplier is available; do not repeat research.")
    if isinstance(action, (RequestConfirmation, ResolveCase)):
        required_complete = all(w.status == "COMPLETED" for w in snapshot.work_orders if w.required_for_resolution)
        dependencies_complete = all(d.status == "SATISFIED" for d in snapshot.dependencies)
        if (str(action.issue_id) != str(snapshot.issue.id) or snapshot.case.status != "AWAITING_CONFIRMATION"
                or not required_complete or not dependencies_complete):
            raise ModelRetry("The repair is not ready for closure. First interpret the pending contractor report with ACCEPT_REPORT (or ADD_PREREQUISITE if blocked). Complete required work and dependencies before REQUEST_CONFIRMATION. Never skip report acceptance.")
    if isinstance(action, ResolveCase) and snapshot.issue.tenant_resolution_confirmed_at is None:
        raise ModelRetry("A contractor report is not tenant confirmation. Use REQUEST_CONFIRMATION, wait for an explicit tenant reply, and only then RESOLVE_CASE using its confirmation event ID.")
    if isinstance(action, ResolveCase):
        confirmations = [e for e in snapshot.recent_events if e.type == "TENANT_CONFIRMATION_RECEIVED"]
        if confirmations:
            latest = max(confirmations, key=lambda e: e.seq)
            if latest.id != action.confirmation_event_id or latest.payload.get("confirmed") is not True:
                raise ModelRetry("Copy the latest affirmative TENANT_CONFIRMATION_RECEIVED event ID from this case. Do not invent a confirmation event or cite a contractor report.")


def construct_agent(model) -> Agent[CoordinatorDeps, ActionProposal]:
    """Builds the coordinator agent for any Pydantic AI model instance --
    the real GoogleModel in production, or a TestModel/FunctionModel in
    tests, with identical tool wiring either way."""
    agent = Agent(
        model,
        deps_type=CoordinatorDeps,
        output_type=ToolOutput(ActionProposal),
        instructions=COORDINATOR_INSTRUCTIONS,
        model_settings=ModelSettings(timeout=MODEL_REQUEST_TIMEOUT_SECONDS),
        retries=1,
    )
    agent.tool(read_report, prepare=prepare_missing_evidence)
    agent.tool(read_communication, prepare=prepare_missing_evidence)
    agent.tool(list_case_events, prepare=prepare_missing_evidence)
    agent.tool(find_appointment_options)
    agent.tool(read_research)

    @agent.output_validator
    def validate_evidence(ctx: RunContext[CoordinatorDeps], output: ActionProposal) -> ActionProposal:
        if str(output.case_id) != ctx.deps.case_id or output.expected_case_version != ctx.deps.snapshot_version:
            raise ModelRetry("Use the current case ID and snapshot version exactly.")
        if ctx.deps.snapshot is not None:
            validate_workflow_action(ctx.deps.snapshot, output.action)
        if isinstance(output.action, ScheduleVisit):
            action = output.action
            offered = ctx.deps.offered_slots.get((str(action.work_order_id), str(action.contractor_id), action.slot_id))
            cited = {str(i) for i in action.tenant_availability_ids}
            if not offered or not cited or not cited.issubset(offered):
                raise ModelRetry("Before SCHEDULE_VISIT call find_appointment_options for this work order, contractor and tenant availability. Copy an exact returned slot_id and cite availability covering that slot. Never invent a date as a slot ID. If there are no slots, request availability instead.")
        if isinstance(output.action, ApplyTriage) and ctx.deps.recorded_risk is not None:
            from app.domain.policy import validate_triage_evidence
            from app.domain.errors import PolicyRejectedError
            try:
                validate_triage_evidence(RiskAssessment.model_validate(ctx.deps.recorded_risk), output.action.risk)
            except PolicyRejectedError as exc:
                raise ModelRetry(str(exc)) from exc
        return output

    return agent


def build_agent(model_name: str, api_key: str) -> Agent[CoordinatorDeps, ActionProposal]:
    return construct_agent(GoogleModel(model_name, provider=GoogleProvider(api_key=api_key)))


def _redact_snapshot(snapshot: CaseSnapshot) -> dict:
    """docs/19: "Redact phone numbers, audio/transcripts and tokens" before
    anything reaches a model. The coordinator proposes actions over IDs --
    raw contact info adds no capability to the text-demo workflow and is
    excluded. Verified
    2026-09-19: this was previously applied only to recording.media_path,
    leaving tenant.phone_e164/email and contractor contact_reference/phone
    going to Gemini on every wake."""
    data = snapshot.model_dump(mode="json")
    for comm in data.get("communications", []):
        recording = comm.get("recording")
        if recording:
            recording["media_path"] = None
    tenant = data.get("tenant")
    if tenant:
        tenant["phone_e164"] = None
        tenant["email"] = None
    for contractor in data.get("approved_contractors", []):
        contractor["contact_reference"] = None
    assigned = data.get("assigned_contractor")
    if assigned:
        assigned["contact_reference"] = None
        assigned["phone"] = None
    return data


def _compact_snapshot(snapshot: CaseSnapshot) -> dict:
    """A lossless evidence view with irrelevant roster and transport metadata removed.

    Keep all supplied reports, human response text, safety facts, work/dependency
    state and pending actions. Only the approved roster is narrowed by deterministic
    service eligibility; the complete database remains available to scoped reads.
    """
    from app.domain.policy import contractor_covers_postcode

    data = _redact_snapshot(snapshot)
    active_trades = {w.trade.value for w in snapshot.work_orders if w.status not in ("COMPLETED", "CANCELLED")}
    assigned_ids = {str(w.contractor_id) for w in snapshot.work_orders if w.contractor_id}
    data["approved_contractors"] = [
        {k: c[k] for k in ("id", "display_name", "trades", "service_postcodes", "approval_status", "verification_note", "provenance") if k in c and c[k] is not None}
        for c in data["approved_contractors"]
        if c["id"] in assigned_ids or (
            contractor_covers_postcode(c["service_postcodes"], snapshot.property.postcode)
            and (not active_trades or active_trades.intersection(c["trades"]))
        )
    ]
    data["communications"] = [
        {k: c[k] for k in ("id", "case_id", "tenant_id", "purpose", "direction", "provider", "state", "started_at", "ended_at", "provenance", "transcript", "outcome") if k in c and c[k] is not None}
        for c in data["communications"]
    ]
    data["recent_events"] = [
        {k: event[k] for k in ("id", "case_id", "type", "seq", "occurred_at", "received_at", "actor_type", "actor_id", "causation_event_id", "payload_version", "provenance", "payload") if k in event}
        for event in data["recent_events"]
    ]
    for event in data["recent_events"]:
        payload = event.get("payload", {})
        # source_text holds the verbatim response once; each safety fact used
        # to repeat that entire response in spoken_text, often six times.
        if payload.get("source_text"):
            for fact in payload.get("facts", []):
                if fact.get("spoken_text") == payload["source_text"]:
                    fact.pop("spoken_text")
    return data


def _format_prompt(snapshot: CaseSnapshot, trigger_event_id: str) -> str:
    import json

    payload = _compact_snapshot(snapshot)
    return (
        "A new event just occurred on this repair case. Decide the single next action.\n\n"
        f"trigger_event_id: {trigger_event_id}\n\n"
        "Current case snapshot (JSON):\n"
        f"{json.dumps(payload, separators=(',', ':'), ensure_ascii=False)}"
    )


class GeminiCoordinator:
    def __init__(self, agent: Agent[CoordinatorDeps, ActionProposal], model_id: str):
        self._agent = agent
        self.model_id = model_id

    async def decide(self, snapshot: CaseSnapshot, trigger_event_id: str) -> ActionProposal:
        return (await self._run(snapshot, trigger_event_id)).output

    async def _run(self, snapshot: CaseSnapshot, trigger_event_id: str, model_settings=None, *, usage=None):
        prompt = _format_prompt(snapshot, trigger_event_id)
        deps = CoordinatorDeps(
            case_id=str(snapshot.case.id), snapshot_version=snapshot.snapshot_version,
            run_id=str(uuid.uuid4()), policy_snapshot=snapshot.policy_snapshot,
            recorded_risk=snapshot.case.risk.model_dump(mode="json"), snapshot=snapshot,
        )
        result = await asyncio.wait_for(
            self._agent.run(
                prompt, deps=deps, model_settings=model_settings, usage=usage,
                usage_limits=getattr(self, 'usage_limits', None) or UsageLimits(request_limit=MAX_MODEL_REQUESTS, tool_calls_limit=MAX_TOOL_CALLS),
            ),
            timeout=RUN_TIMEOUT_SECONDS,
        )
        return result


class ConservativeFixtureCoordinator:
    """Wired up when no GEMINI_API_KEY is configured. Handles only the
    mechanical, non-interpretive step (triage a case with no work order
    yet, using the safety answers already on record) and otherwise WAITs
    with an explicit FIXTURE-mode explanation -- it must never guess at
    semantic interpretation of a report, which would misrepresent a
    keyword match as model reasoning (docs/04)."""

    model_id = "fixture-conservative"

    async def decide(self, snapshot: CaseSnapshot, trigger_event_id: str) -> ActionProposal:
        from app.schemas import ApplyTriage, Trade

        if not snapshot.work_orders:
            return ActionProposal(
                case_id=snapshot.case.id, expected_case_version=snapshot.snapshot_version, trigger_event_id=trigger_event_id,
                decision_summary="FIXTURE mode (no live model configured): applying recorded safety answers without semantic interpretation.",
                evidence_refs=[], action=ApplyTriage(
                    risk=snapshot.case.risk, issue_description=snapshot.issue.description, suggested_trade=Trade.OTHER,
                    scope=snapshot.issue.description,
                ),
            )
        return ActionProposal(
            case_id=snapshot.case.id, expected_case_version=snapshot.snapshot_version, trigger_event_id=trigger_event_id,
            decision_summary="FIXTURE mode: no live model configured, so no new semantic interpretation is attempted; waiting for operator review.",
            evidence_refs=[], action=Wait(reason="no live coordinator configured", waiting_for="model configuration / operator review"),
        )


def build_coordinator(settings: Settings):
    if settings.active_coordinator_provider == "mubit":
        from app.agents.mubit import MubitCoordinator

        return MubitCoordinator(settings)
    if settings.active_coordinator_provider == "gemini":
        agent = build_agent(settings.gemini_model, settings.gemini_api_key)
        return GeminiCoordinator(agent, model_id=settings.gemini_model)
    return ConservativeFixtureCoordinator()
