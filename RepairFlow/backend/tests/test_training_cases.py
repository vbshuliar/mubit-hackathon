import uuid
from collections import Counter

import pytest
from sqlalchemy import select, func

from app.collect_mubit import build_case
from app.training_cases import scenarios, score
from app.db import session_scope
from app.models import ContractorModel
from app.schemas import ActionProposal, ApplyTriage


def test_dataset_split_is_unique_and_balanced():
    cases = scenarios()
    assert len(cases) == len({c.key for c in cases}) == len({c.text for c in cases}) == 64
    assert Counter(c.split for c in cases) == {"train": 48, "eval": 16}
    assert set(c.text for c in cases if c.split == "train").isdisjoint(c.text for c in cases if c.split == "eval")
    assert all(n == 12 for n in Counter(c.family for c in cases if c.split == "train").values())


@pytest.mark.asyncio
async def test_all_synthetic_cases_build_and_share_roster(app_db):
    for scenario in scenarios():
        snapshot, trigger, report, work_order = await build_case(scenario)
        assert snapshot.availability
        assert len(snapshot.approved_contractors) == 4
        if scenario.family == "SCAFFOLDING":
            assert report and work_order
            assert snapshot.latest_reports[0].text == scenario.text
        else:
            assert not snapshot.work_orders
            proposal = ActionProposal(case_id=snapshot.case.id, expected_case_version=snapshot.snapshot_version,
                trigger_event_id=trigger, decision_summary="Synthetic expected proposal", evidence_refs=[],
                action=ApplyTriage(risk=snapshot.case.risk, issue_description=scenario.text,
                                  suggested_trade=scenario.family, scope=scenario.text))
            assert score(proposal, snapshot, trigger, scenario) == []
            proposal.case_id = uuid.uuid4()
            assert "wrong_case" in score(proposal, snapshot, trigger, scenario)
            proposal.action.suggested_trade = "OTHER"
            assert "wrong_trade" in score(proposal, snapshot, trigger, scenario)
    async with session_scope() as session:
        assert (await session.execute(select(func.count()).select_from(ContractorModel))).scalar_one() == 4


def test_lifecycle_split_is_distinct_from_legacy():
    from app.training_cases import lifecycle_scenarios
    cases = lifecycle_scenarios()
    assert len(cases) == len({c.key for c in cases}) == 54
    assert Counter(c.split for c in cases) == {"train": 36, "eval": 18}
    train = {c.text for c in cases if c.split == "train"}
    evaluation = {c.text for c in cases if c.split == "eval"}
    assert train.isdisjoint(evaluation)
    assert {c.text for c in cases}.isdisjoint(c.text for c in scenarios())
    assert len({c.stage for c in cases}) == 9


@pytest.mark.asyncio
async def test_lifecycle_snapshots_and_expected_actions(app_db):
    from app.training_cases import lifecycle_scenarios
    from app.schemas import RequestInformation, AcceptReport, RequestConfirmation, AddPrerequisite, EvidenceRef, ResolveCase, ScheduleVisit
    for scenario in lifecycle_scenarios():
        snapshot, trigger, report_id, work_id = await build_case(scenario)
        assert snapshot.case.status not in {"RESOLVED", "ESCALATED"}
        assert all(c.provenance == "SIMULATED" for c in snapshot.approved_contractors)
        if scenario.stage == "missing_safety":
            assert snapshot.case.risk.gas == "UNKNOWN"
            assert not snapshot.work_orders
            action = RequestInformation(recipient="TENANT", questions=["Any gas smell, fire or smoke, water near electrics, structural danger or uncontrolled flooding?"], purpose="FOLLOW_UP")
        elif scenario.stage == "missing_availability":
            assert not snapshot.availability
            assert snapshot.work_orders[0].status == "READY"
            action = RequestInformation(recipient="TENANT", questions=["When can you provide access?"], purpose="AVAILABILITY")
        elif scenario.stage == "ready_to_schedule":
            assert snapshot.availability
            assert snapshot.work_orders[0].status == "READY"
            contractor = next(c for c in snapshot.approved_contractors if "PLUMBING" in c.trades)
            action = ScheduleVisit(work_order_id=work_id, contractor_id=contractor.id,
                slot_id="validated-by-coordinator-tool", tenant_availability_ids=[snapshot.availability[0].id])
        elif scenario.stage == "awaiting_confirmation":
            assert snapshot.case.status == "AWAITING_CONFIRMATION"
            assert snapshot.work_orders[0].status == "COMPLETED"
            assert snapshot.latest_reports[0].interpretation_status == "APPLIED"
            action = RequestConfirmation(issue_id=snapshot.issue.id, questions=["Is the original problem resolved?"])
        elif scenario.stage == "positive_confirmation":
            assert snapshot.issue.tenant_resolution_confirmed_at is not None
            confirmation = next(e for e in snapshot.recent_events if e.type == "TENANT_CONFIRMATION_RECEIVED")
            action = ResolveCase(issue_id=snapshot.issue.id, confirmation_event_id=confirmation.id)
        elif scenario.stage == "scaffold_report":
            action = AddPrerequisite(report_id=report_id, blocked_work_order_id=work_id,
                prerequisite_trade="SCAFFOLDING", prerequisite_kind="SCAFFOLD_INSTALL",
                prerequisite_scope="Install safe access", reason="Report requires scaffolding")
        else:
            assert snapshot.latest_reports[0].interpretation_status == "PENDING"
            assert snapshot.work_orders[0].status == "AWAITING_REPORT"
            action = AcceptReport(report_id=report_id, outcome=scenario.expected_outcome,
                completion_evidence_refs=[EvidenceRef(source_type="REPORT", source_id=report_id,
                    observed_at=snapshot.latest_reports[0].observed_at, provenance="SIMULATED")])
        proposal = ActionProposal(case_id=snapshot.case.id, expected_case_version=snapshot.snapshot_version,
            trigger_event_id=trigger, decision_summary="Local expected result", evidence_refs=[], action=action)
        assert score(proposal, snapshot, trigger, scenario, report_id, work_id) == []
        if scenario.stage == "missing_safety":
            action.questions = ["What color is the tap?"]
            assert any(p.startswith("missing_safety_question_") for p in score(proposal, snapshot, trigger, scenario))
        if action.kind == "ACCEPT_REPORT":
            action.report_id = uuid.uuid4()
            assert "wrong_report" in score(proposal, snapshot, trigger, scenario, report_id, work_id)


@pytest.mark.asyncio
async def test_safety_probes_are_heldout_and_reject_premature_confirmation(app_db):
    from app.training_cases import safety_probe_scenarios
    from app.schemas import RequestInformation, RequestConfirmation, Escalate
    probes = safety_probe_scenarios()
    assert len(probes) == 6
    assert all(p.split == "eval" for p in probes)
    for probe in probes:
        snapshot, trigger, report, work = await build_case(probe)
        if probe.stage == "probe_required_removal":
            action = RequestInformation(recipient="TENANT", purpose="AVAILABILITY", questions=["When can the scaffold team remove the scaffold?"])
            assert any(w.kind == "SCAFFOLD_REMOVE" and w.required_for_resolution and w.status == "READY" for w in snapshot.work_orders)
        elif probe.stage == "probe_missing_report":
            action = RequestInformation(recipient="OPERATOR", purpose="CONTRACTOR", questions=["Please obtain the missing contractor report."])
            assert not snapshot.latest_reports
            assert snapshot.work_orders[0].status == "AWAITING_REPORT"
        else:
            action = Escalate(reason_code="TENANT_DISPUTES_COMPLETION", operator_message="Tenant still reports the original leak; investigate.")
            assert snapshot.issue.tenant_resolution_confirmed_at is None
            assert snapshot.issue.unresolved_concerns
        proposal = ActionProposal(case_id=snapshot.case.id, expected_case_version=snapshot.snapshot_version,
            trigger_event_id=trigger, decision_summary="Safety invariant", evidence_refs=[], action=action)
        assert score(proposal, snapshot, trigger, probe, report, work) == []
        proposal.action = RequestConfirmation(issue_id=snapshot.issue.id, questions=["Can we close?"])
        assert "premature_completion" in score(proposal, snapshot, trigger, probe, report, work)
