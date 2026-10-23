"""Conservative output checks; these checks never infer facts from human prose.

Text checks establish questionnaire coverage or flag an ambiguous classification.
They do not prove that a question is answered or that a prerequisite is needed.
"""
from __future__ import annotations

import re
from datetime import timezone

from pydantic_ai import ModelRetry

from app.schemas import AcceptReport, AddPrerequisite, Answer, ApplyTriage, CaseSnapshot, RequestInformation

# Recognisable categories, not a classifier of the tenant's answers. Retry text
# supplies unambiguous wording when the model uses an unsupported paraphrase.
SAFETY_QUESTIONS = {
    "gas": (r"\bgas\b", "Can you smell gas?"),
    "fire": (r"\b(?:fire|smoke|burning)\b", "Is there fire, smoke or a burning smell?"),
    "water_near_electrics": (r"(?=.*\b(?:water|wet|leak\w*)\b)(?=.*\b(?:electric\w*|socket\w*|wiring)\b)", "Is water near electrical sockets, wiring or appliances?"),
    "structural_danger": (r"\b(?:structural|collapse|collapsing|unstable)\b", "Is there structural danger or anything at risk of collapse?"),
    "uncontrolled_flood": (r"\b(?:flood\w*|uncontrolled water)\b", "Is there uncontrolled flooding?"),
    "vulnerability_concern": (r"\b(?:vulnerab\w*|disab\w*|mobility|accessibility|additional needs)\b", "Does anyone have vulnerability, mobility or accessibility needs affecting safety or the visit?"),
}
ACCESS_EQUIPMENT = re.compile(r"\b(?:scaffold\w*|access equipment|access platform\w*|cherry picker|ladder\w*)\b", re.I)


def validate_decision_details(snapshot: CaseSnapshot, action) -> None:
    from app.domain.policy import is_hazard

    if isinstance(action, ApplyTriage) and snapshot.work_orders and not is_hazard(action.risk) and not is_hazard(snapshot.case.risk):
        raise ModelRetry("Work orders already exist. Do not repeat APPLY_TRIAGE. Continue the existing work order workflow or escalate if its scope needs operator review.")

    if isinstance(action, RequestInformation):
        if action.purpose == "FOLLOW_UP":
            raise ModelRetry("FOLLOW_UP is reserved for tenant resolution confirmation via REQUEST_CONFIRMATION. For ordinary questions use INTAKE or AVAILABILITY; use CONTRACTOR with recipient OPERATOR for a missing specialist report.")
        if action.purpose == "CONTRACTOR" and action.recipient != "OPERATOR":
            raise ModelRetry("Contractor report questions must target OPERATOR, not TENANT. Use recipient OPERATOR with purpose CONTRACTOR.")
        if not action.questions or any(not question.strip() for question in action.questions):
            raise ModelRetry("REQUEST_INFORMATION must contain explicit, non-empty questions.")
        if action.recipient == "TENANT" and not is_hazard(snapshot.case.risk):
            missing = [question for field, (pattern, question) in SAFETY_QUESTIONS.items()
                       if getattr(snapshot.case.risk, field) == Answer.UNKNOWN
                       and not any(re.search(pattern, text, re.I | re.S) for text in action.questions)]
            if missing:
                raise ModelRetry("Ask every unanswered safety category explicitly before progressing. Include these questions: " + " ".join(missing))

    if not isinstance(action, (AcceptReport, AddPrerequisite)):
        return
    report = next((report for report in snapshot.latest_reports if report.id == action.report_id), None)
    if report is None:
        return  # The workflow validator reports missing/already interpreted reports.
    # received_at is server receipt time, unlike contractor-supplied observed_at.
    # Equal receipt timestamps need the authoritative database event sequence;
    # do not invent ordering from UUIDs or snapshot list order.
    def received_utc(item):
        value = item.received_at
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)

    if any(other.appointment_id == report.appointment_id and other.id != report.id
           and received_utc(other) > received_utc(report) for other in snapshot.latest_reports):
        raise ModelRetry("A newer report was received for this appointment. Review the latest report and its conflicting or corrected evidence before ACCEPT_REPORT or ADD_PREREQUISITE. Do not interpret a superseded report.")
    if not isinstance(action, AcceptReport):
        return
    if action.outcome == "COMPLETED" and not any(
        ref.source_type == "REPORT" and ref.source_id == report.id and ref.provenance == report.provenance
        for ref in action.completion_evidence_refs
    ):
        raise ModelRetry("COMPLETED requires completion_evidence_refs citing this report's exact ID, source_type REPORT and its recorded provenance. Evidence must support completion; otherwise clarify or escalate.")
    if action.outcome in ("NO_ACCESS", "FAILED") and ACCESS_EQUIPMENT.search(report.text):
        raise ModelRetry("This report mentions access equipment. NO_ACCESS or FAILED would consume the report and can hide an equipment prerequisite; accepting the visit first prevents adding a prerequisite from that same report later. Review the full report: use ADD_PREREQUISITE only when it explicitly establishes required work; if negated, mixed or ambiguous, request OPERATOR clarification or ESCALATE. Do not infer a scaffold requirement from a keyword.")
