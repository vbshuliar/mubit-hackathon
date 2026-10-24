"""Bounded proposal-only replay; default offline, --live permits up to four decisions (each may use multiple requests).
Reconstructed states, not exact historical snapshots: current roster, policy,
availability and clock remain; no historical job/agent flags. No worker runs.
"""
from __future__ import annotations
import argparse
import asyncio
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import sys
import uuid

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
CASE = '7ab41737-6346-4c76-b264-2187f3724982'
FOLLOWUP = 'a97dc8a0-2e60-4c6c-992d-7a98c3920438'
STATES = {'negative': (19, 12), 'positive': (27, 18)}


def reconstruct(source: Path, destination: Path, state: str) -> str:
    if source.resolve() == destination.resolve() or destination.exists():
        raise ValueError('Destination must be new and different from source')
    destination.parent.mkdir(parents=True, mode=0o700)
    seq, version = STATES[state]
    with sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True) as src:
        with sqlite3.connect(destination) as db:
            src.backup(db)
    destination.chmod(0o600)
    with sqlite3.connect(destination) as db:
        db.row_factory = sqlite3.Row
        event = db.execute('SELECT * FROM case_events WHERE case_id=? AND seq=?', (CASE, seq)).fetchone()
        if not event or event['type'] != 'TENANT_CONFIRMATION_RECEIVED':
            raise ValueError('Expected confirmation event missing')
        cutoff = event['occurred_at']
        for table in ('jobs', 'orchestration_runs'):
            db.execute(f'DELETE FROM {table} WHERE case_id=?', (CASE,))
        db.execute('DELETE FROM case_events WHERE case_id=? AND seq>?', (CASE, seq))
        keep = {json.loads(row[0]).get('communication_id') for row in db.execute('SELECT payload FROM case_events WHERE case_id=?', (CASE,))}
        for row in db.execute('SELECT id, started_at FROM communications WHERE case_id=?', (CASE,)).fetchall():
            if row['id'] not in keep and (row['started_at'] is None or row['started_at'] > cutoff):
                db.execute('DELETE FROM communications WHERE id=?', (row['id'],))
        if state == 'negative':
            for table in ('mock_reservations', 'contractor_reports', 'appointments'):
                db.execute(f'DELETE FROM {table} WHERE work_order_id=?', (FOLLOWUP,))
            db.execute("UPDATE work_orders SET status='READY', contractor_id=NULL, quote_pence=NULL, completion_report_id=NULL, updated_at=created_at WHERE id=?", (FOLLOWUP,))
        db.execute('DELETE FROM action_records WHERE case_id=? AND created_at>?', (CASE, cutoff))
        db.execute("UPDATE mock_slots SET is_reserved=EXISTS(SELECT 1 FROM mock_reservations r WHERE r.slot_id=mock_slots.slot_id AND r.status='RESERVED')")
        db.execute('UPDATE repair_cases SET status=?, version=?, updated_at=?, last_decision_summary=NULL, next_follow_up_at=NULL WHERE id=?', ('ACTIVE' if state == 'negative' else 'AWAITING_CONFIRMATION', version, cutoff, CASE))
        db.execute('UPDATE repair_issues SET tenant_resolution_confirmed_at=?, unresolved_concerns=? WHERE case_id=?', (None if state == 'negative' else cutoff, json.dumps(['tenant reports issue still unresolved'] if state == 'negative' else []), CASE))
        if db.execute('PRAGMA foreign_key_check').fetchall():
            raise ValueError('Copy contains foreign-key violations')
        return event['id']


def save(path, value):
    with os.fdopen(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'w') as stream:
        json.dump(value, stream, indent=2)


async def run(args):
    from app.config import Settings, get_settings
    from app.db import dispose_engine, session_scope
    from app.domain.services import load_case_snapshot
    from app.agents import coordinator as module
    from app.agents.mubit import MubitCoordinator
    from pydantic_ai import capture_run_messages
    from pydantic_ai.messages import RetryPromptPart
    from app.agents.tracing import validator_failure_code
    settings = Settings()
    if args.live and not settings.mubit_live:
        raise ValueError('Mubit credentials required')
    if args.baseline:
        async def keep_baseline_tool(ctx, tool):
            return tool
        module.prepare_missing_evidence = keep_baseline_tool
        spec = importlib.util.spec_from_file_location('baseline_reads', BACKEND / 'data/limit-audit/read_tools.before.py')
        baseline = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(baseline)
        for name in ('read_report', 'read_communication', 'list_case_events', 'find_appointment_options', 'read_research'):
            setattr(module, name, getattr(baseline, name))
    output = BACKEND / 'data/limit-replays' / uuid.uuid4().hex
    output.mkdir(parents=True, mode=0o700)
    results = []
    for name in args.cases:
        folder = output / name
        trigger = reconstruct(args.source, folder / 'replay.db', name)
        await dispose_engine()
        os.environ.update(DATABASE_PATH=str(folder / 'replay.db'), DATA_DIR=str(folder), FIXI_NO_CONTACT='1')
        get_settings.cache_clear()
        async with session_scope() as session:
            snapshot = await load_case_snapshot(session, CASE)
        save(folder / 'snapshot.private.json', module._redact_snapshot(snapshot))
        for number in range(1, args.rounds + 1):
            row = dict(scenario=name, round=number, mode='baseline_reads' if args.baseline else 'fixed_reads', snapshot_version=snapshot.snapshot_version, record_mode='off', status='prepared')
            if args.live:
                coordinator = MubitCoordinator(settings.model_copy(update={'data_dir': folder, 'mubit_record': 'off'}))
                messages = []
                try:
                    with capture_run_messages() as messages:
                        proposal = await coordinator.decide(snapshot, trigger)
                    expected = 'SCHEDULE_VISIT' if name == 'negative' else 'RESOLVE_CASE'
                    row.update(status='validated_proposal', action=proposal.action.kind, expected_action=expected, expected_action_match=proposal.action.kind == expected)
                    save(folder / f'proposal-{number}.private.json', proposal.model_dump(mode='json'))
                except Exception as exc:
                    row.update(status='error', error_type=type(exc).__name__)
                finally:
                    row['captured_retry_count'] = sum(isinstance(part, RetryPromptPart) for message in messages for part in message.parts)
                    row['last_observed_validation_code'] = validator_failure_code(messages)
                    await coordinator.aclose()
                metrics = folder / 'mubit-runs.jsonl'
                if metrics.exists():
                    row['metrics'] = json.loads(metrics.read_text().splitlines()[-1])
            results.append(row)
            print(json.dumps(row), flush=True)
        await dispose_engine()
    save(output / 'results.json', {'reconstruction': __doc__, 'results': results})
    print(f'Artifacts: {output}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=BACKEND / 'data/demo-workspace/repairflow.db')
    parser.add_argument('--cases', nargs='+', choices=list(STATES), default=list(STATES))
    parser.add_argument('--rounds', type=int, choices=(1, 2), default=1)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--baseline', action='store_true')
    args = parser.parse_args()
    if len(args.cases) != len(set(args.cases)):
        parser.error('Duplicate cases not allowed')
    asyncio.run(run(args))


if __name__ == '__main__':
    main()
