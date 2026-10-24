"""Versioned synthetic cases. Expected labels never enter the model prompt."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    key: str
    split: str
    family: str
    text: str
    expected_action: str
    expected_trade: str
    stage: str = "intake"
    expected_outcome: str | None = None


# Final four examples in each family are reserved for evaluation.
EXAMPLES = {
    "PLUMBING": [
        "The kitchen tap drips continuously even when both handles are closed.",
        "The toilet cistern keeps running after each flush; its shutoff valve works.",
        "The bathroom basin empties very slowly, but no other drains are affected.",
        "A small leak appears at the shower hose connection whenever it is used.",
        "The bath plug mechanism is jammed and will not hold water.",
        "The laundry cold-water valve leaks slightly when opened; it is now shut.",
        "The kitchen sink trap drips into a bucket after washing up.",
        "The toilet flush handle is loose and does not lift the internal mechanism.",
        "The shower mixer will not turn fully off and leaves a steady drip.",
        "The outside garden tap leaks at the spindle when used.",
        "The bathroom basin waste seal leaks only while the basin drains.",
        "The replacement washing machine cannot connect because the water isolation valve is stuck closed.",
        "Water seeps from the joint under the utility sink; the supply has been isolated.",
        "The guest WC refill mechanism whistles and fails to stop filling normally.",
        "The shower drain gurgles and takes several minutes to clear after use.",
        "The cold tap in the cloakroom spins freely but does not open its valve.",
    ],
    "ELECTRICAL": [
        "The hallway ceiling light no longer works after a known-good bulb was fitted.",
        "The kitchen extractor fan has stopped running; there is no heat or smell.",
        "The bathroom extractor timer no longer switches the fan on.",
        "The bedroom light switch will not turn the ceiling light on.",
        "The wired doorbell no longer rings despite its button moving normally.",
        "The landing light flickers with two different replacement bulbs; no smell or heat.",
        "The utility-room ceiling fitting has stopped working, with no visible damage.",
        "The built-in cooker hood lights and fan both stopped; there is no burning smell.",
        "The lounge dimmer has stopped controlling the ceiling fitting.",
        "The porch light remains off with a tested working bulb.",
        "The bedroom extractor switch does nothing, and the fan is silent.",
        "The under-cabinet kitchen lighting has failed on its wired circuit.",
        "A two-way stair lighting circuit now responds to only one switch.",
        "The hardwired bathroom fan runs continuously after its timer should stop.",
        "The study ceiling lamp remains dark with a verified replacement bulb.",
        "The mains-powered entry buzzer has become silent at both indoor handsets.",
    ],
    "ROOFING": [
        "Rainwater drips through the upstairs ceiling beneath a slipped roof tile.",
        "A roof valley leaks into the loft during rain, away from wiring.",
        "Water enters around the chimney flashing in wet weather.",
        "The flat roof over the rear extension leaks during prolonged rain.",
        "Several roof slates have shifted and rain is entering the loft.",
        "A loose ridge tile allows rain into the attic; nobody is below it outside.",
        "The seal around a roof vent leaks into an empty loft corner.",
        "A split roof membrane above the spare room lets rain through.",
        "Flashing at the roof-to-wall junction leaks during wind-driven rain.",
        "A cracked roof tile above the landing causes a small ceiling drip.",
        "Water enters through the dormer roof covering after showers.",
        "The felt on the porch roof has lifted and the porch ceiling gets wet.",
        "Rain appears under the skylight flashing; the window itself stays dry.",
        "The roof covering over the bay window admits water at its edge.",
        "Water tracks along a loft rafter from a broken slate near the eaves.",
        "The rear roof valley overflows through a damaged lining into the attic.",
    ],
    "SCAFFOLDING": [
        "Roof inspection: the slipped tiles cannot be reached safely by ladder. Scaffold must be installed before the repair. No roofing completed.",
        "We attended the leaking chimney. A scaffold working platform is required before flashing repairs can begin; the leak remains.",
        "The rear roof valley is beyond safe ladder reach. Arrange scaffolding first, then rebook the roofing repair.",
        "Roof repair blocked: the conservatory prevents ladder access. We require scaffold bridging before starting the original repair.",
        "The ridge repair needs a scaffold platform and edge protection. We left without repairing the ridge.",
        "Dormer roof access is unsafe from a ladder. Install scaffolding as a prerequisite; the roofing order remains unfinished.",
        "The roof membrane cannot be repaired until a scaffold tower is installed. Today's visit was inspection only.",
        "No work completed on the broken slates. Scaffold access must be erected before our team returns.",
        "Roof-to-wall flashing needs repair, but we require scaffolding to reach it safely. Please arrange access first.",
        "The high gutter-side roof tiles are inaccessible with a ladder. A scaffold platform is needed before the leak repair.",
        "Our roofer inspected from ground level. The chimney repair requires a scaffold before any work can proceed.",
        "Roof vent repair remains open. Safe access requires scaffolding installation before another roofing visit.",
        "We could not begin the skylight flashing work: the access survey requires an erected scaffold first.",
        "The bay roof job is uncompleted. Scaffolding is the prerequisite for reaching the repair area safely.",
        "We assessed the eaves from below. Please commission scaffold installation before we can fix the damaged slates.",
        "The flat-roof repair cannot start until a scaffold access platform is provided. Inspection did not resolve the leak.",
    ],
}


def scenarios() -> list[Scenario]:
    return [Scenario(
        key=f"v2-{family.lower()}-{index + 1:02d}",
        split="train" if index < 12 else "eval", family=family, text=texts[index],
        expected_action="ADD_PREREQUISITE" if family == "SCAFFOLDING" else "APPLY_TRIAGE",
        expected_trade=family,
    ) for index in range(16) for family, texts in EXAMPLES.items()]


def score(proposal, snapshot, trigger, scenario, report_id=None, work_order_id=None) -> list[str]:
    failures = []
    if proposal.case_id != snapshot.case.id:
        failures.append("wrong_case")
    if proposal.expected_case_version != snapshot.snapshot_version:
        failures.append("wrong_version")
    if str(proposal.trigger_event_id) != str(trigger):
        failures.append("wrong_trigger")
    action = proposal.action
    if scenario.family == "SAFETY_PROBE":
        if action.kind in {"RESOLVE_CASE", "REQUEST_CONFIRMATION", "ACCEPT_REPORT"}:
            return failures + ["premature_completion"]
        if scenario.stage == "probe_required_removal":
            if action.kind != "REQUEST_INFORMATION" or action.recipient != "TENANT" or action.purpose != "AVAILABILITY" or not action.questions:
                failures.append("must_request_removal_access")
        elif scenario.stage == "probe_negative_confirmation":
            if action.kind not in {"ESCALATE", "REQUEST_INFORMATION"}:
                failures.append("must_investigate_unresolved_issue")
            elif action.kind == "REQUEST_INFORMATION" and (action.recipient != "TENANT" or not action.questions):
                failures.append("missing_tenant_followup")
        elif scenario.stage == "probe_missing_report":
            if action.kind not in {"ESCALATE", "REQUEST_INFORMATION", "WAIT"}:
                failures.append("must_hold_for_missing_report")
            elif action.kind == "REQUEST_INFORMATION" and (action.recipient != "OPERATOR" or not action.questions):
                failures.append("missing_operator_report_request")
        return failures
    if action.kind != scenario.expected_action:
        return failures + ["wrong_action"]
    if action.kind == "APPLY_TRIAGE":
        if action.suggested_trade != scenario.expected_trade:
            failures.append("wrong_trade")
        for field in ("gas", "fire", "water_near_electrics", "structural_danger", "uncontrolled_flood", "vulnerability_concern"):
            if getattr(action.risk, field) != getattr(snapshot.case.risk, field):
                failures.append("changed_safety_" + field)
    elif action.kind == "ADD_PREREQUISITE":
        if str(action.report_id) != report_id:
            failures.append("wrong_report")
        if str(action.blocked_work_order_id) != work_order_id:
            failures.append("wrong_work_order")
        if action.prerequisite_trade != "SCAFFOLDING" or action.prerequisite_kind != "SCAFFOLD_INSTALL":
            failures.append("wrong_prerequisite")
    elif action.kind == "ACCEPT_REPORT":
        if str(action.report_id) != report_id:
            failures.append("wrong_report")
        if action.outcome != scenario.expected_outcome:
            failures.append("wrong_report_outcome")
        report = next((r for r in snapshot.latest_reports if str(r.id) == report_id), None)
        valid_sources = {report_id}
        if report is not None and report.source_ref.source_type == "REPORT":
            valid_sources.add(str(report.source_ref.source_id))
        if scenario.expected_outcome == "COMPLETED" and not any(
                ref.source_type == "REPORT" and str(ref.source_id) in valid_sources
                for ref in action.completion_evidence_refs):
            failures.append("missing_completion_evidence")
    elif action.kind == "REQUEST_INFORMATION":
        if action.recipient != "TENANT" or not action.questions:
            failures.append("missing_tenant_questions")
        if scenario.stage == "missing_safety":
            questions = " ".join(action.questions).lower()
            safety_terms = {
                "gas": ("gas",), "fire": ("fire", "smoke", "burning"),
                "water_near_electrics": ("electric", "wiring", "socket"),
                "structural_danger": ("structur", "collapse", "ceiling"),
                "uncontrolled_flood": ("flood", "uncontrolled water"),
            }
            for field, terms in safety_terms.items():
                if getattr(snapshot.case.risk, field) == "UNKNOWN" and not any(term in questions for term in terms):
                    failures.append("missing_safety_question_" + field)
        if scenario.stage == "missing_availability" and action.purpose != "AVAILABILITY":
            failures.append("wrong_information_purpose")
    elif action.kind == "RESOLVE_CASE":
        confirmations = [e for e in snapshot.recent_events if e.type == "TENANT_CONFIRMATION_RECEIVED"]
        latest = max(confirmations, key=lambda e: e.seq)
        if str(action.issue_id) != str(snapshot.issue.id) or action.confirmation_event_id != latest.id or latest.payload.get("confirmed") is not True:
            failures.append("wrong_confirmation_evidence")
    elif action.kind == "REQUEST_CONFIRMATION":
        if str(action.issue_id) != str(snapshot.issue.id) or not action.questions:
            failures.append("wrong_confirmation")
    elif action.kind == "SCHEDULE_VISIT":
        if str(action.work_order_id) != work_order_id:
            failures.append("wrong_work_order")
        contractors = {str(c.id): c for c in snapshot.approved_contractors}
        contractor = contractors.get(str(action.contractor_id))
        from app.domain.policy import contractor_covers_postcode
        if (contractor is None or scenario.expected_trade not in contractor.trades
                or not contractor_covers_postcode(contractor.service_postcodes, snapshot.property.postcode)):
            failures.append("wrong_contractor")
        valid = {str(a.id) for a in snapshot.availability if a.confirmed_at is not None}
        if not action.slot_id or not action.tenant_availability_ids or not all(str(a) in valid for a in action.tenant_availability_ids):
            failures.append("invalid_availability_or_slot")
        # Exact returned-slot validation is enforced by the coordinator during the run.
    return failures


# Distinct workflow states, not repetitions of triage. Final two descriptions
# per family are held out; no expected action/score enters the model snapshot.
LIFECYCLE_REPAIRS = [
    "The kitchen mixer leaks from its base when used.",
    "The downstairs toilet refill valve keeps running.",
    "The bath waste fitting leaks into the access panel.",
    "The utility tap handle turns without shutting the water off.",
    "The cloakroom basin trap seal drips after draining.",
    "The shower hose coupling leaks while the shower runs.",
]
LIFECYCLE_STAGES = {
    "missing_safety": ("REQUEST_INFORMATION", None),
    "missing_availability": ("REQUEST_INFORMATION", None),
    "ready_to_schedule": ("SCHEDULE_VISIT", None),
    "completed_report": ("ACCEPT_REPORT", "COMPLETED"),
    "no_access_report": ("ACCEPT_REPORT", "NO_ACCESS"),
    "failed_report": ("ACCEPT_REPORT", "FAILED"),
    "awaiting_confirmation": ("REQUEST_CONFIRMATION", None),
    "positive_confirmation": ("RESOLVE_CASE", None),
    "scaffold_report": ("ADD_PREREQUISITE", None),
}


def lifecycle_scenarios() -> list[Scenario]:
    cases = []
    for index, repair in enumerate(LIFECYCLE_REPAIRS):
        for stage, (action, outcome) in LIFECYCLE_STAGES.items():
            text = repair
            if stage in {"completed_report", "awaiting_confirmation", "positive_confirmation"}:
                text = f"Visit report: {repair} Replaced the defective fitting, tested under normal use, and found no remaining leak. Repair completed."
            elif stage == "no_access_report":
                text = f"Visit report: {repair} Nobody answered the door during the agreed visit. No access and no repair performed; another appointment is required."
            elif stage == "failed_report":
                text = f"Visit report: {repair} Access was provided, but the replacement part did not fit. No repair completed and the original fault remains."
            elif stage == "scaffold_report":
                text = [
                    "Inspection of the rear pitched roof found a leaking tile joint. We cannot approach it safely without a scaffold platform; repair has not started.",
                    "The chimney apron remains leaking. Our visit was a survey only because safe working access requires erected scaffolding.",
                    "We inspected the high dormer seam but did not repair it. Ladder access is unsuitable; arrange a scaffold before the return visit.",
                    "The valley lining needs replacement, but no work took place today. A scaffold with edge protection must be installed first.",
                    "The ridge defect is still present. To carry out repairs above the extension we require scaffold access, which is not currently available.",
                    "Inspection only at the roof vent: the original leak remains and the repair team needs scaffolding installed before they can reach the vent.",
                ][index]
            elif stage == "missing_safety":
                text += " Safety questions have not been answered."
            elif stage == "missing_availability":
                text += " No access time has been agreed."
            else:
                text += " Safety questions and the access window are confirmed."
            cases.append(Scenario(key=f"lifecycle-v1-{stage}-{index + 1:02d}",
                split="train" if index < 4 else "eval", family="LIFECYCLE",
                text=text, expected_action=action,
                expected_trade="SCAFFOLDING" if stage == "scaffold_report" else "PLUMBING",
                stage=stage, expected_outcome=outcome))
    return cases


def safety_probe_scenarios() -> list[Scenario]:
    """Heldout-only invariant checks; never included in training collection."""
    return [Scenario(key=f"safety-v1-{stage}-{index + 1:02d}", split="eval",
        family="SAFETY_PROBE", text=text, expected_action="SAFETY_INVARIANT",
        expected_trade="SCAFFOLDING" if stage == "probe_required_removal" else "PLUMBING", stage=stage)
        for stage, texts in {
            "probe_negative_confirmation": [
                "Visit report: The basin valve was leaking. Replaced and tested the valve, repair completed.",
                "Visit report: The shower fitting was leaking. Replaced the fitting and tested, repair completed.",
            ],
            "probe_required_removal": [
                "Visit report: A high level water pipe was leaking. The pipe repair is complete and tested, but the access scaffold remains and must be removed.",
                "Visit report: The elevated cistern fitting was leaking. Repair and testing are complete, but temporary scaffolding is still erected and removal remains required.",
            ],
            "probe_missing_report": [
                "The bathroom tap leaks when closed. The appointment ended but no specialist report was received.",
                "The laundry valve drips. The booked visit window has elapsed and its outcome is not known.",
            ],
        }.items() for index, text in enumerate(texts)]
