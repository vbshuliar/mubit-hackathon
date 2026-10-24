"""Phase 3: the real coordinator's *mechanical* round trip -- agent.run()
through tool execution to a validated discriminated-union ActionProposal --
exercised with Pydantic AI's FunctionModel/TestModel so it needs zero
credentials (docs/22: "Pydantic AI's test models and function-model
facilities can control model behavior in unit tests"). What is genuinely
untestable without a live Gemini key is *semantic* interpretation quality
(novel phrasing, prompt-injection resistance) -- that's deferred to the
live-model evaluation gate in docs/22, reported UNMET in docs/23.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from app.agents.coordinator import GeminiCoordinator, construct_agent
from app.db import session_scope
from app.domain import services
from app.domain.services import ActorContext
from app.models import CommunicationModel
from app.orchestration import dispatcher
from app.schemas import (
    AddPrerequisite,
    ApplyTriage,
    Escalate,
    EvidenceRef,
    IntakeSubmission,
    Provenance,
    ReportSubmission,
    RiskAssessment,
    SourceType,
    Trade,
    Wait,
    WorkOrderKind,
)

from tests.test_hero_path import _seed_reference_data, _work_order, uid


async def _case_with_pending_report():
    """A case with one BLOCKED-worthy report already recorded: a real REPAIR
    work order, SCHEDULED appointment, and a contractor report describing
    (in the agent's own novel wording, not hard-coded anywhere in app code)
    why the roofer can't proceed -- exactly the input the coordinator must
    turn into an AddPrerequisite proposal."""
    property_id, tenant_id, roofer_id, scaffolder_id = await _seed_reference_data()
    comm_id = uid()
    async with session_scope() as session:
        session.add(CommunicationModel(id=comm_id, purpose="INTAKE", direction="BROWSER", correlation_token_hash=uid(), state="ACTIVE", provenance="FIXTURE"))
    async with session_scope() as session:
        case_id, intake_result = await services.submit_intake(
            session, communication_id=comm_id,
            submission=IntakeSubmission(
                safety_answers={name: "NO" for name in ("gas", "fire", "water_near_electrics", "structural_danger", "uncontrolled_flood", "vulnerability_concern")},

                communication_id=uuid.UUID(comm_id), property_id=uuid.UUID(property_id), tenant_id=uuid.UUID(tenant_id),
                description="Water ingress near the roofline.", location="Rear bedroom ceiling", source_text="src",
            ),
            actor=ActorContext("VOICE_TOOL", comm_id, comm_id),
        )
    async with session_scope() as session:
        triage_result = await services.apply_triage(
            session, case_id=case_id,
            action=ApplyTriage(
                risk=RiskAssessment(urgency="ROUTINE", gas="NO", fire="NO", water_near_electrics="NO", structural_danger="NO", uncontrolled_flood="NO", vulnerability_concern="NO"),
                issue_description="Water ingress near the roofline.", suggested_trade=Trade.ROOFING, scope="Repair roof ingress.",
            ),
            trigger_event_id=str(intake_result.event_ids[0]), actor=ActorContext("SYSTEM", "test-setup", uid()),
        )
    repair_wo = await _work_order(case_id, "REPAIR")

    from app.models import ActionRecordModel, AppointmentModel

    async with session_scope() as session:
        appt = AppointmentModel(
            id=uid(), case_id=case_id, work_order_id=repair_wo.id, contractor_id=roofer_id, slot_id="fixture-slot",
            start_at=datetime.now(timezone.utc), end_at=datetime.now(timezone.utc), status="CONFIRMED", connector="MOCK",
            provider_booking_id="mock-fixture", action_id=uid(), attempt_number=1, availability_revision=1, provenance="SIMULATED",
        )
        session.add(appt)
        session.add(ActionRecordModel(id=appt.action_id, case_id=case_id, kind="SCHEDULE_VISIT", idempotency_key=f"fixture:{appt.id}", payload_hash="fixture", proposal={}, state="SUCCEEDED"))

    async with session_scope() as session:
        report_id, _ = await services.record_contractor_report(
            session,
            submission=ReportSubmission(
                work_order_id=uuid.UUID(repair_wo.id), appointment_id=uuid.UUID(appt.id), contractor_id=uuid.UUID(roofer_id),
                text="Had a look today -- there's genuinely no way to reach those tiles off a ladder without real access "
                     "equipment in place first. I don't want to risk it.",
                observed_at=datetime.now(timezone.utc),
            ),
            source_ref=EvidenceRef(source_type=SourceType.REPORT, source_id=uid(), observed_at=datetime.now(timezone.utc), provenance=Provenance.SIMULATED),
            provenance=Provenance.SIMULATED, actor=ActorContext("CONTRACTOR_ADAPTER", roofer_id, uid()),
        )
    return case_id, report_id, repair_wo.id


def _last_trigger_event_id(messages: list[ModelMessage]) -> str:
    text = messages[0].parts[0].content
    for line in text.splitlines():
        if line.startswith("trigger_event_id:"):
            return line.split(":", 1)[1].strip()
    raise AssertionError("trigger_event_id not found in prompt")


@pytest.mark.asyncio
async def test_agent_calls_read_report_then_returns_add_prerequisite(app_db):
    case_id, report_id, repair_wo_id = await _case_with_pending_report()

    async with session_scope() as session:
        snapshot = await services.load_case_snapshot(session, case_id)

    # A stale supplied report keeps the scoped read available; complete,
    # unchanged reports are intentionally no longer offered for rereading.
    snapshot.latest_reports[0] = snapshot.latest_reports[0].model_copy(update={
        "text": "Earlier report: " + snapshot.latest_reports[0].text})
    call_count = {"n": 0}

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        call_count["n"] += 1
        if call_count["n"] == 1:
            return ModelResponse(parts=[ToolCallPart(tool_name="read_report", args={"case_id": case_id, "record_id": report_id})])
        output_tool = info.output_tools[0].name
        trigger_event_id = _last_trigger_event_id(messages)
        proposal_args = {
            "case_id": case_id, "expected_case_version": snapshot.snapshot_version, "trigger_event_id": trigger_event_id,
            "decision_summary": "Roofer cannot safely reach the tiles without access equipment; scaffold required.",
            "evidence_refs": [{"source_type": "REPORT", "source_id": report_id, "observed_at": datetime.now(timezone.utc).isoformat(), "provenance": "SIMULATED"}],
            "action": {
                "kind": "ADD_PREREQUISITE", "report_id": report_id, "blocked_work_order_id": repair_wo_id,
                "prerequisite_trade": "SCAFFOLDING", "prerequisite_kind": "SCAFFOLD_INSTALL",
                "prerequisite_scope": "Erect scaffold for safe roof access.", "reason": "No safe ladder access per contractor report.",
            },
        }
        return ModelResponse(parts=[ToolCallPart(tool_name=output_tool, args=proposal_args)])

    agent = construct_agent(FunctionModel(respond))
    coordinator = GeminiCoordinator(agent, model_id="test-function-model")

    proposal = await coordinator.decide(snapshot, trigger_event_id=uid())

    assert call_count["n"] == 2, "the agent must actually invoke read_report, not just be offered it"
    assert isinstance(proposal.action, AddPrerequisite)
    assert str(proposal.action.report_id) == report_id
    assert str(proposal.action.blocked_work_order_id) == repair_wo_id
    assert proposal.action.prerequisite_kind == WorkOrderKind.SCAFFOLD_INSTALL

    # And the resulting proposal is a real, executable ActionProposal --
    # confirm it clears the same admission path the worker uses.
    async with session_scope() as session:
        from app.orchestration.executor import admit_proposal

        record = await admit_proposal(session, proposal, ActorContext("COORDINATOR", coordinator.model_id, uid()))
        assert record.kind == "ADD_PREREQUISITE"


@pytest.mark.asyncio
async def test_agent_direct_output_wait(app_db):
    property_id, tenant_id, roofer_id, scaffolder_id = await _seed_reference_data()
    comm_id = uid()
    async with session_scope() as session:
        session.add(CommunicationModel(id=comm_id, purpose="INTAKE", direction="BROWSER", correlation_token_hash=uid(), state="ACTIVE", provenance="FIXTURE"))
    async with session_scope() as session:
        case_id, _ = await services.submit_intake(
            session, communication_id=comm_id,
            submission=IntakeSubmission(
                communication_id=uuid.UUID(comm_id), property_id=uuid.UUID(property_id), tenant_id=uuid.UUID(tenant_id),
                description="desc", location="loc", source_text="src",
            ),
            actor=ActorContext("VOICE_TOOL", comm_id, comm_id),
        )

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        output_tool = info.output_tools[0].name
        trigger_event_id = _last_trigger_event_id(messages)
        return ModelResponse(parts=[ToolCallPart(tool_name=output_tool, args={
            "case_id": case_id, "expected_case_version": 1, "trigger_event_id": trigger_event_id,
            "decision_summary": "Nothing new to do yet.", "evidence_refs": [],
            "action": {"kind": "WAIT", "reason": "awaiting first triage", "waiting_for": "nothing specific"},
        })])

    agent = construct_agent(FunctionModel(respond))
    coordinator = GeminiCoordinator(agent, model_id="test-function-model")

    async with session_scope() as session:
        snapshot = await services.load_case_snapshot(session, case_id)

    proposal = await coordinator.decide(snapshot, trigger_event_id=uid())
    assert isinstance(proposal.action, Wait)


@pytest.mark.asyncio
async def test_hazard_gate_bypasses_coordinator_entirely(app_db):
    """docs/13: the deterministic safety gate runs before the model is ever
    called. A coordinator that raises if invoked proves it truly wasn't."""

    class PoisonCoordinator:
        model_id = "poison"

        async def decide(self, snapshot, trigger_event_id):
            raise AssertionError("coordinator must not be invoked when the hazard gate fires")

    property_id, tenant_id, roofer_id, scaffolder_id = await _seed_reference_data()
    comm_id = uid()
    async with session_scope() as session:
        session.add(CommunicationModel(id=comm_id, purpose="INTAKE", direction="BROWSER", correlation_token_hash=uid(), state="ACTIVE", provenance="FIXTURE"))
    async with session_scope() as session:
        case_id, intake_result = await services.submit_intake(
            session, communication_id=comm_id,
            submission=IntakeSubmission(
                communication_id=uuid.UUID(comm_id), property_id=uuid.UUID(property_id), tenant_id=uuid.UUID(tenant_id),
                description="Smell of gas near the boiler.", location="Airing cupboard", source_text="src",
                safety_answers={"gas": "YES"},
            ),
            actor=ActorContext("VOICE_TOOL", comm_id, comm_id),
        )
    trigger_event_id = str(intake_result.event_ids[0])

    record = await dispatcher.run_coordinate(case_id=case_id, trigger_event_id=trigger_event_id, coordinator=PoisonCoordinator())
    assert record is None

    async with session_scope() as session:
        case = await services.load_case(session, case_id)
        assert case.status == "ESCALATED"
        assert case.escalation_reason


@pytest.mark.asyncio
async def test_schedule_validator_retries_then_requires_actual_scoped_options(app_db):
    from pydantic_ai.messages import ToolReturnPart, RetryPromptPart
    from tests.test_fixi_ui_support import _drive_case_to_scheduled
    prop, tenant, roofer, _ = await _seed_reference_data()
    case_id, _, work, appointment = await _drive_case_to_scheduled(prop, tenant, roofer)
    async with session_scope() as session:
        await services.cancel_appointment(session, appointment_id=appointment.id, reason="Rebook for test", actor=ActorContext("OPERATOR", "test", "test-cancel"))
        snapshot = await services.load_case_snapshot(session, case_id)
    availability = [str(w.id) for w in snapshot.availability]
    count = 0

    def respond(messages, info):
        nonlocal count
        count += 1
        if count == 2:
            assert any(isinstance(p, RetryPromptPart) for m in messages for p in m.parts)
            return ModelResponse(parts=[ToolCallPart(tool_name='find_appointment_options', args={
                'case_id':case_id,'work_order_id':work.id,'contractor_id':roofer,'tenant_availability_ids':availability})])
        slot_id = '2099-01-01T10:00:00Z'
        if count == 3:
            returned = next(p.content for m in reversed(messages) for p in m.parts if isinstance(p,ToolReturnPart) and p.tool_name=='find_appointment_options')
            slot_id = returned.slots[0].slot_id
        return ModelResponse(parts=[ToolCallPart(tool_name=info.output_tools[0].name,args={
            'case_id':case_id,'expected_case_version':snapshot.snapshot_version,'trigger_event_id':_last_trigger_event_id(messages),
            'decision_summary':'Use an actual offered slot','evidence_refs':[],
            'action':{'kind':'SCHEDULE_VISIT','work_order_id':work.id,'contractor_id':roofer,
                      'slot_id':slot_id,'tenant_availability_ids':availability}})])

    coordinator=GeminiCoordinator(construct_agent(FunctionModel(respond)),model_id='test-function-model')
    proposal=await coordinator.decide(snapshot,uid())
    assert count==3
    assert proposal.action.slot_id!='2099-01-01T10:00:00Z'


@pytest.mark.asyncio
async def test_unreturned_slot_retry_is_bounded(app_db):
    from pydantic_ai.exceptions import UnexpectedModelBehavior
    from tests.test_fixi_ui_support import _drive_case_to_scheduled
    prop,tenant,roofer,_=await _seed_reference_data()
    case_id,_,work,_=await _drive_case_to_scheduled(prop,tenant,roofer)
    async with session_scope() as session:
        snapshot=await services.load_case_snapshot(session,case_id)
    count=0
    def respond(messages,info):
        nonlocal count
        count+=1
        return ModelResponse(parts=[ToolCallPart(tool_name=info.output_tools[0].name,args={
            'case_id':case_id,'expected_case_version':snapshot.snapshot_version,'trigger_event_id':_last_trigger_event_id(messages),
            'decision_summary':'Invented option','evidence_refs':[],
            'action':{'kind':'SCHEDULE_VISIT','work_order_id':work.id,'contractor_id':roofer,
                      'slot_id':'fake','tenant_availability_ids':[str(w.id) for w in snapshot.availability]}})])
    coordinator=GeminiCoordinator(construct_agent(FunctionModel(respond)),model_id='test-function-model')
    with pytest.raises(UnexpectedModelBehavior):
        await coordinator.decide(snapshot,uid())
    assert count==2


@pytest.mark.asyncio
async def test_compact_prompt_preserves_evidence_and_filters_irrelevant_roster(app_db):
    import json
    from app.agents.coordinator import _compact_snapshot, _format_prompt, _redact_snapshot
    case_id, _, _ = await _case_with_pending_report()
    async with session_scope() as session:
        snapshot=await services.load_case_snapshot(session,case_id)
    template=snapshot.approved_contractors[0]
    for _ in range(20):
        snapshot.approved_contractors.append(template.model_copy(update={
            'id':uuid.uuid4(),'service_postcodes':['BS99'],'display_name':'Outside the service area'}))
    compact=_compact_snapshot(snapshot)
    full=_redact_snapshot(snapshot)
    assert compact['case']['risk']==full['case']['risk']
    for compact_event, original_event in zip(compact['recent_events'],full['recent_events']):
        for field in ('id','case_id','type','seq','occurred_at','received_at','provenance','actor_type','actor_id','causation_event_id','payload_version'):
            if field in original_event:
                assert compact_event[field]==original_event[field]
    assert compact['latest_reports']==full['latest_reports']
    assert compact['work_orders']==full['work_orders']
    assert compact['dependencies']==full['dependencies']
    assert compact['pending_actions']==full['pending_actions']
    assert [c['transcript'] for c in compact['communications']]==[c['transcript'] for c in full['communications']]
    for projected, original in zip(compact['communications'], full['communications']):
        for field in ('direction', 'provider', 'ended_at'):
            assert projected.get(field) == original.get(field)
    assert all('BS1' in c['service_postcodes'] for c in compact['approved_contractors'])
    assert all('ROOFING' in c['trades'] for c in compact['approved_contractors'])
    assert all('correlation_token_hash' not in c and 'recording' not in c for c in compact['communications'])
    assert len(_format_prompt(snapshot,uid())) < len(json.dumps(full,indent=2))*0.6


@pytest.mark.asyncio
async def test_usage_limit_failure_is_persisted_and_never_retried(app_db):
    from pydantic_ai.exceptions import UsageLimitExceeded
    from app.models import JobModel, OrchestrationRunModel
    from sqlalchemy import select
    from app.orchestration.worker import drain_due_jobs
    from tests.test_fixi_ui_support import _intake
    prop,tenant,_,_=await _seed_reference_data()
    case_id=await _intake(prop,tenant,'Kitchen sink leaking')
    class ExhaustedCoordinator:
        model_id='test-exhausted'
        calls=0
        async def decide(self,snapshot,trigger_event_id):
            self.calls+=1
            raise UsageLimitExceeded('Explicit test token limit reached')
    coordinator=ExhaustedCoordinator()
    assert await drain_due_jobs(coordinator)==1
    assert coordinator.calls==1
    async with session_scope() as session:
        run=(await session.execute(select(OrchestrationRunModel).where(OrchestrationRunModel.case_id==case_id))).scalar_one()
        assert run.state=='FAILED' and run.finished_at is not None
        assert run.error_code=='UsageLimitExceeded'
        job=(await session.execute(select(JobModel).where(JobModel.case_id==case_id))).scalar_one()
        assert job.status=='FAILED' and job.attempts==1


@pytest.mark.asyncio
async def test_workflow_validator_preserves_prerequisite_and_blocks_shortcuts(app_db):
    from pydantic_ai import ModelRetry
    from app.agents.coordinator import validate_workflow_action
    from app.schemas import DiscoverContractors, ResolveCase, RequestConfirmation, AddPrerequisite
    case_id,report_id,work_id=await _case_with_pending_report()
    async with session_scope() as session:
        snap=await services.load_case_snapshot(session,case_id)
    with pytest.raises(ModelRetry,match='already cover'):
        validate_workflow_action(snap,DiscoverContractors(trade='ROOFING',postcode='BS1'))
    with pytest.raises(ModelRetry,match='not ready for closure'):
        validate_workflow_action(snap,ResolveCase(issue_id=snap.issue.id,confirmation_event_id=uuid.uuid4()))
    with pytest.raises(ModelRetry,match='not ready for closure'):
        validate_workflow_action(snap,RequestConfirmation(issue_id=snap.issue.id,questions=['Fixed?']))
    validate_workflow_action(snap,AddPrerequisite(report_id=report_id,blocked_work_order_id=work_id,
        prerequisite_trade='SCAFFOLDING',prerequisite_kind='SCAFFOLD_INSTALL',prerequisite_scope='Safe roof access',reason='Report requires scaffold'))
    snap.case.status='AWAITING_CONFIRMATION'
    for w in snap.work_orders:w.status='COMPLETED'
    validate_workflow_action(snap,RequestConfirmation(issue_id=snap.issue.id,questions=['Fixed?']))
    with pytest.raises(ModelRetry,match='not tenant confirmation'):
        validate_workflow_action(snap,ResolveCase(issue_id=snap.issue.id,confirmation_event_id=uuid.uuid4()))
    snap.issue.tenant_resolution_confirmed_at=datetime.now(timezone.utc)
    validate_workflow_action(snap,ResolveCase(issue_id=snap.issue.id,confirmation_event_id=uuid.uuid4()))


@pytest.mark.asyncio
async def test_invalid_resolution_is_corrected_to_report_interpretation_in_same_run(app_db):
    case_id,report_id,work_id=await _case_with_pending_report()
    async with session_scope() as session:
        snap=await services.load_case_snapshot(session,case_id)
    count=0
    def respond(messages,info):
        nonlocal count
        count+=1
        action=({'kind':'RESOLVE_CASE','issue_id':str(snap.issue.id),'confirmation_event_id':uid()} if count==1 else
                {'kind':'ADD_PREREQUISITE','report_id':report_id,'blocked_work_order_id':work_id,
                 'prerequisite_trade':'SCAFFOLDING','prerequisite_kind':'SCAFFOLD_INSTALL',
                 'prerequisite_scope':'Safe access','reason':'Contractor requires scaffold'})
        return ModelResponse(parts=[ToolCallPart(tool_name=info.output_tools[0].name,args={
            'case_id':case_id,'expected_case_version':snap.snapshot_version,'trigger_event_id':_last_trigger_event_id(messages),
            'decision_summary':'Interpret reported finding','evidence_refs':[],'action':action})])
    coordinator=GeminiCoordinator(construct_agent(FunctionModel(respond)),model_id='test-function-model')
    proposal=await coordinator.decide(snap,uid())
    assert count==2 and proposal.action.kind=='ADD_PREREQUISITE'


@pytest.mark.asyncio
async def test_applied_report_cannot_be_interpreted_twice(app_db):
    from pydantic_ai import ModelRetry
    from app.agents.coordinator import validate_workflow_action
    from app.schemas import AcceptReport, AddPrerequisite
    case_id, report_id, work_id = await _case_with_pending_report()
    async with session_scope() as session:
        snap = await services.load_case_snapshot(session, case_id)
    action = AcceptReport(report_id=report_id, outcome="COMPLETED", completion_evidence_refs=[EvidenceRef(source_type="REPORT", source_id=report_id, observed_at=datetime.now(timezone.utc), provenance=snap.latest_reports[0].provenance)])
    validate_workflow_action(snap, action)
    snap.latest_reports[0].interpretation_status = "APPLIED"
    snap.work_orders[0].status = "READY"
    for proposal in (action, AddPrerequisite(
        report_id=report_id, blocked_work_order_id=work_id,
        prerequisite_trade="SCAFFOLDING", prerequisite_kind="SCAFFOLD_INSTALL",
        prerequisite_scope="Safe roof access", reason="Report requires scaffold",
    )):
        with pytest.raises(ModelRetry, match="Remaining READY work order IDs") as exc:
            validate_workflow_action(snap, proposal)
        assert str(snap.work_orders[0].id) in str(exc.value)


@pytest.mark.asyncio
async def test_unknown_safety_requires_questions_before_model_triage(app_db):
    from pydantic_ai import ModelRetry
    from app.agents.coordinator import validate_workflow_action
    case_id, _, _ = await _case_with_pending_report()
    async with session_scope() as session:
        snap = await services.load_case_snapshot(session, case_id)
    snap.case.risk = RiskAssessment()
    action = ApplyTriage(risk=RiskAssessment(), issue_description="Dripping pipe",
                         suggested_trade="PLUMBING", scope="Repair pipe")
    with pytest.raises(ModelRetry, match="REQUEST_INFORMATION"):
        validate_workflow_action(snap, action)
    action.risk.gas = "YES"
    validate_workflow_action(snap, action)
    action.risk.gas = "UNKNOWN"
    snap.case.risk.gas = "YES"
    validate_workflow_action(snap, action)

@pytest.mark.asyncio
async def test_read_tools_reference_unchanged_snapshot_evidence_and_preserve_history(app_db):
    from types import SimpleNamespace
    from app.agents.dependencies import CoordinatorDeps
    from app.agents.read_tools import read_report, read_communication, list_case_events
    from app.schemas import RecordRef, ReadEvents
    case_id, report_id, _ = await _case_with_pending_report()
    async with session_scope() as session:
        snapshot = await services.load_case_snapshot(session, case_id)
    ctx = SimpleNamespace(deps=CoordinatorDeps(case_id=case_id, snapshot_version=snapshot.snapshot_version,
        run_id=uid(), policy_snapshot={}, snapshot=snapshot))
    report = await read_report(ctx, RecordRef(case_id=case_id, record_id=report_id))
    assert report.snapshot_path == f'latest_reports[id={report_id}]'
    assert 'text' not in report.model_dump()
    comm_id = snapshot.communications[0].id
    comm = await read_communication(ctx, RecordRef(case_id=case_id, record_id=comm_id))
    assert comm.snapshot_path == f'communications[id={comm_id}]'
    assert 'transcript' not in comm.additional_fields
    assert 'correlation_token_hash' not in comm.additional_fields
    events = await list_case_events(ctx, ReadEvents(case_id=case_id, limit=100))
    assert [getattr(e, 'record_id', getattr(e, 'id', None)) for e in events] == [e.id for e in snapshot.recent_events]
    assert all(len(e.model_dump_json()) <= len(original.model_dump_json())
               for e, original in zip(events, snapshot.recent_events))
    # Partial snapshot must not hide older evidence; same pagination/order remains.
    snapshot.latest_reports.clear()
    snapshot.communications.clear()
    snapshot.recent_events = snapshot.recent_events[-1:]
    assert (await read_report(ctx, RecordRef(case_id=case_id, record_id=report_id))).text
    assert (await read_communication(ctx, RecordRef(case_id=case_id, record_id=comm_id))).id == comm_id
    historical = await list_case_events(ctx, ReadEvents(case_id=case_id, limit=100))
    assert historical[0].id == getattr(events[0], 'record_id', getattr(events[0], 'id', None))
    assert getattr(historical[-1], 'record_id', getattr(historical[-1], 'id', None)) == snapshot.recent_events[-1].id

@pytest.mark.asyncio
async def test_read_report_returns_changed_evidence_and_rejects_wrong_case(app_db):
    from types import SimpleNamespace
    from pydantic_ai import ModelRetry
    from app.agents.dependencies import CoordinatorDeps
    from app.agents.read_tools import read_report
    from app.models import ContractorReportModel
    from app.schemas import RecordRef
    case_id, report_id, _ = await _case_with_pending_report()
    async with session_scope() as session:
        snapshot = await services.load_case_snapshot(session, case_id)
    ctx = SimpleNamespace(deps=CoordinatorDeps(case_id=case_id, snapshot_version=snapshot.snapshot_version,
        run_id=uid(), policy_snapshot={}, snapshot=snapshot))
    async with session_scope() as session:
        report = await session.get(ContractorReportModel, report_id)
        report.text = 'Updated evidence must never be hidden by a snapshot reference'
    assert (await read_report(ctx, RecordRef(case_id=case_id, record_id=report_id))).text.startswith('Updated evidence')
    with pytest.raises(ModelRetry):
        await read_report(ctx, RecordRef(case_id=uuid.uuid4(), record_id=report_id))

@pytest.mark.asyncio
async def test_prepare_read_tools_omits_only_complete_unchanged_snapshot_collections(app_db):
    from types import SimpleNamespace
    from pydantic_ai.tools import ToolDefinition
    from app.agents.dependencies import CoordinatorDeps
    from app.agents.read_tools import prepare_missing_evidence
    from app.models import ContractorReportModel
    case_id, report_id, _ = await _case_with_pending_report()
    async with session_scope() as session:
        snapshot = await services.load_case_snapshot(session, case_id)
    ctx = SimpleNamespace(deps=CoordinatorDeps(case_id=case_id, snapshot_version=snapshot.snapshot_version,
        run_id=uid(), policy_snapshot={}, snapshot=snapshot))
    for name, collection in [('read_report', 'latest_reports'), ('read_communication', 'communications'), ('list_case_events', 'recent_events')]:
        tool = ToolDefinition(name=name)
        assert await prepare_missing_evidence(ctx, tool) is None
        original = getattr(snapshot, collection)
        setattr(snapshot, collection, [])
        assert await prepare_missing_evidence(ctx, tool) is tool
        setattr(snapshot, collection, original)
    async with session_scope() as session:
        row = await session.get(ContractorReportModel, report_id)
        row.text = 'New content on the same report ID'
    tool = ToolDefinition(name='read_report')
    assert await prepare_missing_evidence(ctx, tool) is tool
    no_snapshot = SimpleNamespace(deps=CoordinatorDeps(case_id=case_id, snapshot_version=0, run_id=uid(), policy_snapshot={}))
    assert await prepare_missing_evidence(no_snapshot, tool) is tool
