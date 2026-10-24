"""Bounded, proposal-only collection in a separate synthetic database.

uv run python -m app.collect_mubit --live --split train --limit 48
Without --live, builds and validates local cases without any model calls.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select

from app.config import BACKEND_DIR, Settings, get_settings
from app.training_cases import Scenario, scenarios, lifecycle_scenarios, safety_probe_scenarios, score


def uid() -> str:
    return str(uuid.uuid4())


async def build_case(scenario: Scenario):
    if scenario.family == "SAFETY_PROBE":
        return await build_safety_probe(scenario)
    from app.db import session_scope
    from app.domain import services
    from app.domain.services import ActorContext
    from app.models import PropertyModel, TenantModel, ContractorModel, CommunicationModel, WorkOrderModel, AppointmentModel, ActionRecordModel, ContractorReportModel
    from app.schemas import IntakeSubmission, ApplyTriage, RiskAssessment, ReportSubmission, EvidenceRef, AcceptReport, ObservationSubmission

    property_id, tenant_id, comm_id = [uid() for _ in range(3)]
    now = datetime.now(timezone.utc)
    actor = ActorContext("SYSTEM", "synthetic-collection", uid())
    safety = dict.fromkeys(["gas", "fire", "water_near_electrics", "structural_danger", "uncontrolled_flood", "vulnerability_concern"], "NO")
    report_stage = scenario.stage in {"completed_report", "no_access_report", "failed_report", "awaiting_confirmation", "positive_confirmation", "scaffold_report"} or scenario.family == "SCAFFOLDING"
    scaffold = scenario.family == "SCAFFOLDING" or scenario.stage == "scaffold_report"
    description = "Rain is entering the roof; the repair remains unresolved." if scaffold else scenario.text
    if report_stage and not scaffold:
        description = scenario.text.split("Visit report: ", 1)[-1].split(". ", 1)[0] + "."
    if scenario.stage == "missing_safety":
        safety = dict.fromkeys(safety, "UNKNOWN")
    async with session_scope() as session:
        session.add(PropertyModel(id=property_id, address_line="1 Synthetic Training Street", postcode="BS1 1AA", landlord_reference="SYNTHETIC", roof_responsibility="LANDLORD"))
        session.add(TenantModel(id=tenant_id, property_id=property_id, display_name="Synthetic Resident", preferred_channel="VOICE", contact_allowed=False))
        session.add(CommunicationModel(id=comm_id, purpose="INTAKE", direction="BROWSER", correlation_token_hash=uid(), state="ACTIVE", provenance="SIMULATED"))
        for trade in ("PLUMBING", "ELECTRICAL", "ROOFING", "SCAFFOLDING"):
            name = f"Synthetic {trade} Team"
            existing = (await session.execute(select(ContractorModel).where(ContractorModel.display_name == name))).scalar_one_or_none()
            contractor_id = existing.id if existing else uid()
            if not existing:
                session.add(ContractorModel(id=contractor_id, display_name=name, trades=[trade], service_postcodes=["BS1"], approval_status="APPROVED", connector="MOCK", provenance="SIMULATED"))
            if trade == ("ROOFING" if scaffold else "PLUMBING"):
                selected_contractor_id = contractor_id
    async with session_scope() as session:
        case_id, result = await services.submit_intake(session, communication_id=comm_id, submission=IntakeSubmission(
            communication_id=comm_id, property_id=property_id, tenant_id=tenant_id,
            description=description, location="Reported repair area", source_text=description,
            safety_answers=safety,
            availability=[] if scenario.stage == "missing_availability" else [dict(start_at=now-timedelta(hours=3) if report_stage else now+timedelta(days=2),
                               end_at=now if report_stage else now+timedelta(days=5),
                               timezone="Europe/London", spoken_text="I can provide access throughout this confirmed window.", confirmed_by_speaker=True)],
        ), actor=actor)
    trigger = str(result.event_ids[0])
    report_id = work_order_id = None
    if report_stage or scenario.stage in {"missing_availability", "ready_to_schedule"}:
        async with session_scope() as session:
            triage_result = await services.apply_triage(session, case_id=case_id, action=ApplyTriage(
                risk=RiskAssessment(urgency="ROUTINE", **safety), issue_description=description,
                suggested_trade="ROOFING" if scaffold else "PLUMBING", scope=description,
            ), trigger_event_id=trigger, actor=actor)
        trigger = str(triage_result.event_ids[-1])
        async with session_scope() as session:
            wo = (await session.execute(select(WorkOrderModel).where(WorkOrderModel.case_id == case_id))).scalar_one()
            work_order_id = wo.id
        if not report_stage:
            async with session_scope() as session:
                snapshot = await services.load_case_snapshot(session, case_id)
            return snapshot, trigger, None, work_order_id
        async with session_scope() as session:
            wo = await session.get(WorkOrderModel, work_order_id)
            wo.status = "SCHEDULED"
            wo.contractor_id = selected_contractor_id
            now = datetime.now(timezone.utc)
            appt = AppointmentModel(id=uid(), case_id=case_id, work_order_id=wo.id, contractor_id=selected_contractor_id,
                slot_id="synthetic-slot", start_at=now-timedelta(hours=2), end_at=now-timedelta(hours=1),
                status="CONFIRMED", connector="MOCK", provider_booking_id=f"synthetic-{uid()}", action_id=uid(),
                attempt_number=1, availability_revision=1, provenance="SIMULATED")
            session.add(appt)
            session.add(ActionRecordModel(id=appt.action_id, case_id=case_id, kind="SCHEDULE_VISIT", idempotency_key=uid(), payload_hash="synthetic", proposal={}, state="SUCCEEDED"))
        async with session_scope() as session:
            report_id, result = await services.record_contractor_report(session, submission=ReportSubmission(
                work_order_id=work_order_id, appointment_id=appt.id, contractor_id=selected_contractor_id,
                text=scenario.text, observed_at=now,
            ), source_ref=EvidenceRef(source_type="REPORT", source_id=uid(), observed_at=now, provenance="SIMULATED"),
                provenance="SIMULATED", actor=actor)
            stored_report = await session.get(ContractorReportModel, report_id)
            stored_report.source_ref = {**stored_report.source_ref, "source_id": report_id}
            trigger = str(result.event_ids[0])
    if scenario.stage in {"awaiting_confirmation", "positive_confirmation"}:
        async with session_scope() as session:
            acceptance_id = uid()
            session.add(ActionRecordModel(id=acceptance_id, case_id=case_id, kind="ACCEPT_REPORT",
                idempotency_key=uid(), payload_hash="synthetic", proposal={}, state="SUCCEEDED"))
            await session.flush()
            result = await services.accept_report(session, case_id=case_id,
                action=AcceptReport(report_id=report_id, outcome="COMPLETED"),
                action_id=acceptance_id, trigger_event_id=trigger, actor=actor)
            trigger = str(result.event_ids[-1])
    if scenario.stage == "positive_confirmation":
        async with session_scope() as session:
            result = await services.record_observations(session, case_id=case_id, communication_id=comm_id,
                submission=ObservationSubmission(communication_id=comm_id, tenant_confirms_resolved=True,
                    source_text="Yes, I have checked the repair and the original problem is completely resolved."), actor=actor)
            trigger = str(result.event_ids[-1])
    async with session_scope() as session:
        snapshot = await services.load_case_snapshot(session, case_id)
    return snapshot, trigger, report_id, work_order_id


async def build_safety_probe(scenario: Scenario):
    from dataclasses import replace
    from app.db import session_scope
    from app.domain import services
    from app.domain.services import ActorContext
    from app.models import CommunicationModel, WorkOrderModel, AppointmentModel, ActionRecordModel, AvailabilityWindowModel
    from app.schemas import ObservationSubmission
    stage = "ready_to_schedule" if scenario.stage == "probe_missing_report" else "awaiting_confirmation"
    base = replace(scenario, family="LIFECYCLE", stage=stage)
    snapshot, trigger, report_id, work_id = await build_case(base)
    case_id = str(snapshot.case.id)
    actor = ActorContext("SYSTEM", "synthetic-collection", uid())
    async with session_scope() as session:
        if scenario.stage == "probe_negative_confirmation":
            comm = (await session.execute(select(CommunicationModel).where(CommunicationModel.case_id == case_id))).scalars().first()
            result = await services.record_observations(session, case_id=case_id, communication_id=comm.id,
                submission=ObservationSubmission(communication_id=comm.id, tenant_confirms_resolved=False,
                    source_text="No, the original leak still happens when I use it. Please investigate; the problem is not resolved."), actor=actor)
            trigger = str(result.event_ids[-1])
        elif scenario.stage == "probe_required_removal":
            case = await services.load_case(session, case_id)
            case.status = "ACTIVE"
            work_id = uid()
            session.add(WorkOrderModel(id=work_id, case_id=case_id, issue_id=str(snapshot.issue.id),
                kind="SCAFFOLD_REMOVE", trade="SCAFFOLDING", scope="Remove temporary access scaffold and clear site",
                status="READY", required_for_resolution=True))
            services.bump_version(case)
            event = await services.append_event(session, case_id=case_id, event_type="WORK_ORDER_CREATED",
                payload={"work_order_id": work_id, "kind": "SCAFFOLD_REMOVE", "required_for_resolution": True},
                actor=actor, provenance="SIMULATED", source_event_key=f"probe-removal:{work_id}")
            trigger = event.id
        else:
            wo = await session.get(WorkOrderModel, work_id)
            contractor = next(c for c in snapshot.approved_contractors if "PLUMBING" in c.trades)
            wo.status = "SCHEDULED"
            wo.contractor_id = str(contractor.id)
            now = datetime.now(timezone.utc)
            windows = (await session.execute(select(AvailabilityWindowModel).where(AvailabilityWindowModel.case_id == case_id))).scalars().all()
            for window in windows:
                window.start_at = now - timedelta(hours=3)
                window.end_at = now
            appointment_id, action_id = uid(), uid()
            session.add(ActionRecordModel(id=action_id, case_id=case_id, kind="SCHEDULE_VISIT", idempotency_key=uid(),
                payload_hash="synthetic", proposal={}, state="SUCCEEDED"))
            session.add(AppointmentModel(id=appointment_id, case_id=case_id, work_order_id=work_id,
                contractor_id=str(contractor.id), slot_id="synthetic-past-slot", start_at=now-timedelta(hours=2),
                end_at=now-timedelta(hours=1), status="CONFIRMED", connector="MOCK", provider_booking_id=uid(),
                action_id=action_id, attempt_number=1, availability_revision=1, provenance="SIMULATED"))
            await session.flush()
            result = await services.mark_attendance_window_ended(session, case_id=case_id, appointment_id=appointment_id,
                actor=actor, provenance="SIMULATED")
            trigger = str(result.event_ids[-1])
    async with session_scope() as session:
        snapshot = await services.load_case_snapshot(session, case_id)
    return snapshot, trigger, report_id, work_id


async def run(args):
    settings = Settings()
    if args.live and not settings.mubit_live:
        raise ValueError("Configure the backend MUBIT_API_KEY before live collection")
    if args.dataset == "safety" and args.split != "eval":
        raise ValueError("Safety probes are held out: use --split eval (recording off)")
    dataset = {"legacy": scenarios, "lifecycle": lifecycle_scenarios, "safety": safety_probe_scenarios}[args.dataset]()
    selected = [s for s in dataset if s.split == args.split][args.offset:args.offset+args.limit]
    if not selected:
        raise ValueError("No scenarios selected")
    output = BACKEND_DIR / "data" / "mubit-collections" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8])
    output.mkdir(parents=True, exist_ok=False)
    # Independent process and database: never start the worker or execute proposals.
    os.environ["DATABASE_PATH"] = str(output / "synthetic.db")
    os.environ["DATA_DIR"] = str(output)
    os.environ["FIXI_NO_CONTACT"] = "1"
    os.environ["PYDANTIC_AI_NO_BANNER"] = "1"
    get_settings.cache_clear()
    from app.db import create_all, dispose_engine
    from app.agents.mubit import MubitCoordinator
    settings = settings.model_copy(update={"data_dir": output, "mubit_record": "full" if args.split == "train" else "off"})
    coordinator = None
    try:
        await create_all()
        built = [(s, await build_case(s)) for s in selected]
        (output / "manifest.json").write_text(json.dumps([s.__dict__ for s in selected], indent=2))
        print(f"Prepared {len(built)} {args.split} cases in {output}", flush=True)
        if not args.live:
            return
        coordinator = MubitCoordinator(settings)
        results = []
        failures = 0
        failed_scores = 0
        for scenario, (snapshot, trigger, report_id, work_order_id) in built:
            row = {"scenario": scenario.key, "split": scenario.split, "case_id": str(snapshot.case.id), "expected_action": scenario.expected_action}
            try:
                proposal = await coordinator.decide(snapshot, trigger)
                row["proposal"] = proposal.model_dump(mode="json")
                try:
                    problems = score(proposal, snapshot, trigger, scenario, report_id, work_order_id)
                except Exception as exc:
                    row.update(status="scoring_error", passed=False, error_type=type(exc).__name__)
                    failed_scores += 1
                else:
                    row.update(status="scored", passed=not problems, problems=problems)
                    failed_scores = failed_scores + 1 if problems else 0
                failures = 0
            except Exception as exc:
                row.update(status="error", passed=False, error_type=type(exc).__name__)
                failures += 1
            results.append(row)
            with (output / "results.jsonl").open("a") as stream:
                stream.write(json.dumps(row) + "\n")
            print(f"{len(results)}/{len(built)} {scenario.key}: {row['status']} passed={row['passed']}", flush=True)
            if row["status"] == "scoring_error":
                print("Stopped after evaluator error; proposal saved for offline rescoring.", flush=True)
                break
            if failed_scores >= 3:
                print("Stopped after three consecutive failed scores; inspect cases before spending more.", flush=True)
                break
            if failures >= 3:
                print("Stopped after three consecutive request errors; inspect results before retrying.", flush=True)
                break
        metrics_path = output / "mubit-runs.jsonl"
        metrics = [json.loads(line) for line in metrics_path.read_text().splitlines()] if metrics_path.exists() else []
        summary = {"dataset": args.dataset, "split": args.split, "record_mode": settings.mubit_record, "planned": len(built), "attempted": len(results),
                   "passed": sum(r["passed"] for r in results), "errors": sum(r["status"] == "error" for r in results),
                   "scoring_errors": sum(r["status"] == "scoring_error" for r in results),
                   "model_requests": sum(m.get("requests", 0) for m in metrics),
                   "input_tokens": sum(m.get("input_tokens", 0) for m in metrics), "output_tokens": sum(m.get("output_tokens", 0) for m in metrics),
                   "elapsed_ms": sum(m["elapsed_ms"] for m in metrics), "training_status": "not_verified"}
        summary["usage_scope"] = "successful runs only; failed-run usage is unknown"
        summary["runs_with_unknown_usage"] = sum("requests" not in m for m in metrics)
        (output / "summary.json").write_text(json.dumps(summary, indent=2))
        print(json.dumps(summary), flush=True)
    finally:
        if coordinator:
            await coordinator.aclose()
        await dispose_engine()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=["legacy", "lifecycle", "safety"], default="legacy")
    parser.add_argument("--live", action="store_true", help="Make paid model calls through Mubit")
    parser.add_argument("--split", choices=["train", "eval"], default="train")
    parser.add_argument("--limit", type=int, default=48)
    parser.add_argument("--offset", type=int, default=0)
    args = parser.parse_args()
    if not 1 <= args.limit <= 48 or args.offset < 0:
        parser.error("limit must be 1–48 and offset must be non-negative")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
