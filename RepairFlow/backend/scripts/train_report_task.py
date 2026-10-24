"""Bounded standalone experiment. Dry by default; no operational database access."""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agents.report_task import PROMPT_VERSION, ReportInput, ReportTask
from app.agents.mubit import MubitBudgetExceeded
from app.config import Settings


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--split', choices=['train', 'dev', 'eval'], default='dev')
    parser.add_argument('--dataset', choices=['base', 'expansion', 'bulk', 'fresh'], default='base')
    parser.add_argument('--limit', type=int, default=7)
    parser.add_argument('--offset', type=int, default=0)
    parser.add_argument('--max-runs', type=int, help='Explicit shared cumulative reservation ceiling (does not reset ledger)')
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args(argv)
    if args.dataset in ('expansion', 'bulk', 'fresh') and args.split != 'train':
        parser.error('Additional datasets require --split train')
    if not 1 <= args.limit <= 64:
        parser.error('--limit must be 1..64')
    if args.offset < 0:
        parser.error('--offset must be nonnegative')
    if args.max_runs is not None and not 0 <= args.max_runs <= 1000:
        parser.error('--max-runs must be 0..1000')
    return args


def summarize_rows(rows: list[dict]) -> dict:
    """Summarize attempts without claiming that serving used a trained adapter.

    Errors remain in the accuracy denominator and have an ERROR prediction.
    Confusion matrix rows are expected labels and columns are predictions.
    """
    per_class = {}
    confusion_matrix = {}
    passed = errors = unsafe_false_completion = 0
    for row in rows:
        expected = row['expected']
        is_error = 'error_type' in row or row.get('predicted') is None
        predicted = 'ERROR' if is_error else row['predicted']
        correct = not is_error and predicted == expected
        passed += int(correct)
        errors += int(is_error)
        counts = per_class.setdefault(expected, {'total': 0, 'correct': 0})
        counts['total'] += 1
        counts['correct'] += int(correct)
        matrix_row = confusion_matrix.setdefault(expected, {})
        matrix_row[predicted] = matrix_row.get(predicted, 0) + 1
        unsafe_false_completion += int(expected == 'ESCALATE' and predicted == 'COMPLETED')
    return {
        'evaluation_scope': 'teacher_or_unverified_serving',
        'attempted': len(rows), 'passed': passed, 'errors': errors,
        'accuracy': passed / len(rows) if rows else None,
        'per_class': per_class, 'confusion_matrix': confusion_matrix,
        'unsafe_false_completion': unsafe_false_completion,
        **{key: sum(row.get('metrics', {}).get(key, 0) for row in rows)
           for key in ('requests', 'input_tokens', 'output_tokens')},
    }


async def run(args):
    if args.dataset in ('expansion', 'bulk', 'fresh'):
        if args.split != 'train':
            raise ValueError('Additional dataset is training-only')
        if args.dataset == 'fresh':
            from app.report_training_fresh import fresh_scenarios as scenarios
        elif args.dataset == 'bulk':
            from app.report_training_bulk import bulk_scenarios as scenarios
        else:
            from app.report_training_expansion import expansion_scenarios as scenarios
    else:
        from app.report_training_cases import scenarios
    cases = [case for case in scenarios() if case.split == args.split][args.offset:args.offset + args.limit]
    if not cases:
        raise ValueError('Selection contains no cases')
    # Reject malformed evidence before reserving any paid calls.
    evidence = [ReportInput(work_scope=case.scope, report_text=case.report) for case in cases]
    manifest = {'prompt_version': PROMPT_VERSION, 'dataset': args.dataset, 'split': args.split, 'live': args.live,
                'count': len(cases), 'keys': [case.key for case in cases]}
    if not args.live:
        print(json.dumps(manifest, indent=2))
        return manifest
    settings = Settings()
    if args.max_runs is not None:
        settings = settings.model_copy(update={'mubit_max_runs': args.max_runs})
    output = args.output_dir or settings.data_dir / 'report-task-runs' / (
        datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:8])
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    task = ReportTask(settings)
    rows = []
    consecutive_errors = 0
    try:
        with (output / 'results.jsonl').open('x') as stream:
            for case, source in zip(cases, evidence, strict=True):
                row = {'key': case.key, 'expected': case.expected}
                try:
                    decision, metrics = await task.infer(source, split=args.split)
                    row.update(predicted=decision.classification, passed=decision.classification == case.expected, metrics=metrics)
                    consecutive_errors = 0
                except Exception as exc:
                    row.update(passed=False, error_type=type(exc).__name__, metrics=task.last_metrics)
                    consecutive_errors += 1
                rows.append(row)
                stream.write(json.dumps(row) + '\n')
                stream.flush()
                print(json.dumps({'key': case.key, 'passed': row['passed'], 'error_type': row.get('error_type')}), flush=True)
                if consecutive_errors >= 3 or row.get('error_type') == MubitBudgetExceeded.__name__:
                    break
    finally:
        await task.aclose()
    summary = {**manifest, **summarize_rows(rows)}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps({'output': str(output), **summary}, indent=2))
    return summary


if __name__ == '__main__':
    asyncio.run(run(parse_args()))
