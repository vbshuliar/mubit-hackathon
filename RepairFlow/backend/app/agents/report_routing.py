"""Opt-in report shadow measurement; never proposes or applies domain actions."""
from __future__ import annotations

from pydantic import ValidationError

from app.agents.report_task import ReportInput, ReportTask
from app.config import Settings
from app.schemas import CaseSnapshot, ContractorReport


def select_report(snapshot: CaseSnapshot) -> tuple[ContractorReport, ReportInput] | None:
    """Select unambiguous scoped evidence; uncertain snapshots stay coordinator-only."""
    if snapshot.case.status in ('RESOLVED', 'CLOSED', 'ESCALATED'):
        return None
    pending = [r for r in snapshot.latest_reports if r.interpretation_status == 'PENDING']
    if len(pending) != 1:
        return None
    report = pending[0]
    work = next((w for w in snapshot.work_orders if w.id == report.work_order_id), None)
    appointment = next((a for a in snapshot.appointments if a.id == report.appointment_id), None)
    if (work is None or appointment is None or
            report.case_id != snapshot.case.id or work.case_id != snapshot.case.id or
            appointment.case_id != snapshot.case.id or appointment.work_order_id != work.id or
            appointment.contractor_id != report.contractor_id or
            work.status in ('COMPLETED', 'CANCELLED') or appointment.status == 'CANCELLED'):
        return None
    if work.contractor_id is not None and work.contractor_id != report.contractor_id:
        return None
    if any(a.work_order_id == work.id and a.id != appointment.id and
           a.attempt_number >= appointment.attempt_number for a in snapshot.appointments):
        return None
    try:
        evidence = ReportInput(work_scope=work.scope, report_text=report.text)
    except ValidationError:
        return None
    return report, evidence


async def observe_report(snapshot: CaseSnapshot, settings: Settings) -> dict[str, object]:
    """Errors are diagnostic only; cancellation still propagates to the caller.

    Record mode is off: operational shadow calls must not contaminate training.
    Gateway request IDs are traceability, not proof an adapter served the call.
    """
    if not settings.mubit_report_shadow_enabled:
        return {'status': 'disabled'}
    selected = select_report(snapshot)
    if selected is None:
        return {'status': 'ineligible'}
    report, evidence = selected
    diagnostic: dict[str, object] = {'status': 'error', 'mode': 'shadow', 'serving_provenance': 'unknown',
                  'report_id': str(report.id), 'case_version': snapshot.case.version,
                  'evidence_provenance': report.provenance.value}
    task = None
    try:
        task = ReportTask(settings)
        decision, metrics = await task.infer(evidence, split='dev')
        diagnostic.update(status='classified', classification=decision.classification,
                          metrics=metrics)
    except Exception as exc:
        diagnostic['error_type'] = type(exc).__name__
        if task is not None:
            diagnostic['metrics'] = task.last_metrics
    finally:
        if task is not None:
            try:
                await task.aclose()
            except Exception as exc:
                diagnostic['close_error_type'] = type(exc).__name__
    return diagnostic
