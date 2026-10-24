"""Offline adversarial checks; these are not measurements of model quality."""
import uuid
import pytest
from pydantic_ai import ModelRetry
from app.agents.coordinator import validate_workflow_action
from app.agents.decision_validation import SAFETY_QUESTIONS
from app.db import session_scope
from app.domain import services
from app.schemas import AcceptReport, ApplyTriage, EvidenceRef, RequestInformation, RiskAssessment
from tests.test_coordinator import _case_with_pending_report

@pytest.fixture
async def snapshot(app_db):
    case_id, _, _ = await _case_with_pending_report()
    async with session_scope() as session:
        return await services.load_case_snapshot(session, case_id)

@pytest.mark.asyncio
@pytest.mark.parametrize('omitted', list(SAFETY_QUESTIONS))
async def test_missing_question(snapshot, omitted):
    snapshot.case.risk = RiskAssessment()
    action = RequestInformation(recipient='TENANT', purpose='INTAKE', questions=[q for f, (_, q) in SAFETY_QUESTIONS.items() if f != omitted])
    with pytest.raises(ModelRetry, match='every unanswered safety'):
        validate_workflow_action(snapshot, action)
    action.questions.append(SAFETY_QUESTIONS[omitted][1])
    validate_workflow_action(snapshot, action)

@pytest.mark.asyncio
async def test_known_answers_and_operator_questions(snapshot):
    action = RequestInformation(recipient='TENANT', purpose='AVAILABILITY', questions=['When can the contractor visit?'])
    validate_workflow_action(snapshot, action)
    snapshot.case.risk = RiskAssessment()
    action.recipient = 'OPERATOR'
    validate_workflow_action(snapshot, action)
    action.questions = [' ']
    with pytest.raises(ModelRetry, match='non-empty'):
        validate_workflow_action(snapshot, action)

@pytest.mark.asyncio
async def test_retriage(snapshot):
    action = ApplyTriage(risk=snapshot.case.risk, issue_description='Roof leak', suggested_trade='ROOFING', scope='Repair roof')
    with pytest.raises(ModelRetry, match='already exist'):
        validate_workflow_action(snapshot, action)
    action.risk = action.risk.model_copy(update={'gas': 'YES'})
    validate_workflow_action(snapshot, action)
    action.risk = snapshot.case.risk
    snapshot.work_orders = []
    validate_workflow_action(snapshot, action)

@pytest.mark.asyncio
@pytest.mark.parametrize('invalid', ['empty', 'foreign', 'wrong_type', 'wrong_provenance'])
async def test_completion_evidence(snapshot, invalid):
    report = snapshot.latest_reports[0]
    ref = EvidenceRef(source_type='REPORT', source_id=report.id, observed_at=report.observed_at, provenance=report.provenance)
    action = AcceptReport(report_id=report.id, outcome='COMPLETED', completion_evidence_refs=[ref])
    validate_workflow_action(snapshot, action)
    if invalid == 'empty': action.completion_evidence_refs = []
    elif invalid == 'foreign': ref.source_id = uuid.uuid4()
    elif invalid == 'wrong_type': ref.source_type = 'EVENT'
    else: ref.provenance = 'REAL'
    with pytest.raises(ModelRetry, match='completion_evidence_refs'):
        validate_workflow_action(snapshot, action)

@pytest.mark.asyncio
@pytest.mark.parametrize('text', [
    'Tenant was home. Scaffold is required to reach the roof safely.',
    'Scaffold is NOT required. The tenant was not home.',
    'Cannot reach tiles safely off a ladder; access equipment needed.',
    'No access; tenant absent, and scaffold may also be needed.',
])
async def test_equipment_ambiguity(snapshot, text):
    snapshot.latest_reports[0].text = text
    action = AcceptReport(report_id=snapshot.latest_reports[0].id, outcome='NO_ACCESS')
    with pytest.raises(ModelRetry, match='OPERATOR clarification'):
        validate_workflow_action(snapshot, action)
    assert len(snapshot.work_orders) == 1
    action.outcome = 'FAILED'
    with pytest.raises(ModelRetry, match='consume the report'):
        validate_workflow_action(snapshot, action)

@pytest.mark.asyncio
async def test_tenant_no_access(snapshot):
    snapshot.latest_reports[0].text = 'Tenant absent; nobody answered the door. No work carried out.'
    validate_workflow_action(snapshot, AcceptReport(report_id=snapshot.latest_reports[0].id, outcome='NO_ACCESS'))

@pytest.mark.asyncio
@pytest.mark.parametrize('failure', ['safety', 'retriage', 'completion', 'equipment'])
async def test_invalid_decision_gets_one_bounded_correction(snapshot, failure):
    from pydantic_ai.messages import ModelResponse, ToolCallPart
    from pydantic_ai.models.function import FunctionModel
    from app.agents.coordinator import GeminiCoordinator, construct_agent
    from tests.test_coordinator import _last_trigger_event_id

    report = snapshot.latest_reports[0]
    if failure == 'safety':
        snapshot.case.risk = RiskAssessment()
        invalid = {'kind': 'REQUEST_INFORMATION', 'recipient': 'TENANT', 'purpose': 'INTAKE', 'questions': ['Is there gas?']}
    elif failure == 'retriage':
        invalid = ApplyTriage(risk=snapshot.case.risk, issue_description='Leak', suggested_trade='ROOFING', scope='Repair').model_dump(mode='json')
    else:
        report.text = 'Scaffold is needed before repair can proceed.'
        invalid = {'kind': 'ACCEPT_REPORT', 'report_id': str(report.id), 'outcome': 'COMPLETED' if failure == 'completion' else 'NO_ACCESS'}
    calls = 0
    def respond(messages, info):
        nonlocal calls
        calls += 1
        action = invalid if calls == 1 else {'kind': 'ESCALATE', 'reason_code': 'NEEDS_REVIEW', 'operator_message': 'Please review this ambiguous decision.', 'evidence_refs': []}
        return ModelResponse(parts=[ToolCallPart(tool_name=info.output_tools[0].name, args={
            'case_id': str(snapshot.case.id), 'expected_case_version': snapshot.snapshot_version,
            'trigger_event_id': _last_trigger_event_id(messages), 'decision_summary': 'Review current evidence',
            'evidence_refs': [], 'action': action,
        })])
    coordinator = GeminiCoordinator(construct_agent(FunctionModel(respond)), model_id='offline-validation-test')
    proposal = await coordinator.decide(snapshot, str(uuid.uuid4()))
    assert calls == 2
    assert proposal.action.kind == 'ESCALATE'

@pytest.mark.asyncio
@pytest.mark.parametrize('recipient', ['TENANT', 'OPERATOR'])
async def test_follow_up_reserved_for_confirmation(snapshot, recipient):
    with pytest.raises(ModelRetry, match='reserved for tenant resolution'):
        validate_workflow_action(snapshot, RequestInformation(recipient=recipient, purpose='FOLLOW_UP', questions=['Please clarify the repair details.']))

@pytest.mark.asyncio
async def test_specialist_report_must_target_operator(snapshot):
    action = RequestInformation(recipient='TENANT', purpose='CONTRACTOR', questions=['Please provide the missing specialist report.'])
    with pytest.raises(ModelRetry, match='must target OPERATOR'):
        validate_workflow_action(snapshot, action)
    snapshot.case.risk = RiskAssessment(gas='YES')
    action.recipient = 'OPERATOR'
    validate_workflow_action(snapshot, action)

@pytest.mark.asyncio
@pytest.mark.parametrize('kind', ['ACCEPT_REPORT', 'ADD_PREREQUISITE'])
async def test_newer_same_appointment_report_requires_correction(snapshot, kind):
    from datetime import timedelta, timezone
    from app.schemas import AddPrerequisite
    report = snapshot.latest_reports[0]
    report.text = 'Replacement part was defective; repair unsuccessful.'
    if kind == 'ACCEPT_REPORT':
        action = AcceptReport(report_id=report.id, outcome='FAILED')
    else:
        action = AddPrerequisite(report_id=report.id, blocked_work_order_id=report.work_order_id,
                                 prerequisite_trade='SCAFFOLDING', prerequisite_kind='SCAFFOLD_INSTALL',
                                 prerequisite_scope='Safe access', reason='Contractor finding')
    newer = report.model_copy(update={'id': uuid.uuid4(), 'received_at': report.received_at.replace(tzinfo=timezone.utc) + timedelta(seconds=1),
                                     'observed_at': report.observed_at - timedelta(days=1)})
    snapshot.latest_reports.append(newer)
    with pytest.raises(ModelRetry, match='newer report was received'):
        validate_workflow_action(snapshot, action)
    # A newer observation time alone cannot supersede server receipt ordering.
    newer.received_at = report.received_at
    newer.observed_at = report.observed_at + timedelta(days=1)
    validate_workflow_action(snapshot, action)
    # Different visits do not supersede each other.
    newer.received_at = report.received_at + timedelta(seconds=1)
    newer.appointment_id = uuid.uuid4()
    validate_workflow_action(snapshot, action)

@pytest.mark.asyncio
async def test_cannot_accept_failed_visit_then_add_scaffold_from_consumed_report(snapshot):
    from app.schemas import AddPrerequisite
    report = snapshot.latest_reports[0]
    report.text = 'Attended property. Cannot safely repair the roof until scaffolding is installed. Tenant provided access.'
    with pytest.raises(ModelRetry, match='accepting the visit first prevents adding a prerequisite'):
        validate_workflow_action(snapshot, AcceptReport(report_id=report.id, outcome='FAILED'))
    assert report.interpretation_status == 'PENDING'
    validate_workflow_action(snapshot, AddPrerequisite(
        report_id=report.id, blocked_work_order_id=report.work_order_id,
        prerequisite_trade='SCAFFOLDING', prerequisite_kind='SCAFFOLD_INSTALL',
        prerequisite_scope='Install safe roof access', reason='Report explicitly requires scaffold before repair',
    ))

@pytest.mark.asyncio
async def test_failed_repair_without_equipment_remains_available(snapshot):
    report = snapshot.latest_reports[0]
    report.text = 'Replacement valve was defective; leak remains after attempted repair.'
    validate_workflow_action(snapshot, AcceptReport(report_id=report.id, outcome='FAILED'))
