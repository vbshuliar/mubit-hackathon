"""Offline invariants for the independently authored fresh training corpus."""
from collections import Counter

import pytest

from app.agents.report_task import ReportDecision, ReportInput
from app.report_training_fresh import fresh_scenarios
from scripts import train_report_task as runner


def test_fresh_corpus_is_balanced_unique_and_training_only():
    cases = fresh_scenarios()
    assert len(cases) == 200
    assert {case.split for case in cases} == {'train'}
    counts = Counter(case.expected for case in cases)
    assert len(counts) == 7
    assert set(counts.values()) <= {28, 29}
    assert len({case.key for case in cases}) == 200
    assert len({(case.scope, case.report) for case in cases}) == 200
    assert len({case.report for case in cases}) == 200
    assert cases == fresh_scenarios()


def test_fresh_evidence_has_valid_frozen_contract_without_answer_leakage():
    for case in fresh_scenarios():
        evidence = ReportInput(work_scope=case.scope, report_text=case.report)
        assert set(evidence.model_dump()) == {'work_scope', 'report_text'}
        assert ReportDecision(classification=case.expected).classification == case.expected


@pytest.mark.asyncio
async def test_fresh_runtime_rejects_eval_even_after_argument_mutation():
    args = runner.parse_args(['--dataset', 'fresh', '--split', 'train'])
    args.split = 'eval'
    with pytest.raises(ValueError, match='training-only'):
        await runner.run(args)


@pytest.mark.asyncio
async def test_fresh_dry_run_selects_expected_cases():
    args = runner.parse_args(['--dataset', 'fresh', '--split', 'train', '--offset', '14', '--limit', '7'])
    result = await runner.run(args)
    assert result['dataset'] == 'fresh'
    assert result['live'] is False
    assert result['keys'] == [case.key for case in fresh_scenarios()[14:21]]
