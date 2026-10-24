"""Offline metrics and training-only dataset selection checks."""
import sys
from types import SimpleNamespace

import pytest

from scripts import train_report_task as runner


def test_metrics_count_errors_in_denominator_and_show_confusion():
    rows = [
        {'expected': 'COMPLETED', 'predicted': 'COMPLETED', 'metrics': {'requests': 1}},
        {'expected': 'ESCALATE', 'predicted': 'COMPLETED', 'metrics': {'input_tokens': 20}},
        {'expected': 'ESCALATE', 'error_type': 'TimeoutError', 'metrics': {'requests': 2}},
        {'expected': 'NO_ACCESS', 'predicted': 'NO_ACCESS', 'metrics': {'output_tokens': 5}},
    ]
    summary = runner.summarize_rows(rows)
    assert summary['accuracy'] == 0.5
    assert summary['attempted'] == 4
    assert summary['passed'] == 2
    assert summary['errors'] == 1
    assert summary['unsafe_false_completion'] == 1
    assert summary['per_class']['ESCALATE'] == {'total': 2, 'correct': 0}
    assert summary['confusion_matrix']['ESCALATE'] == {'COMPLETED': 1, 'ERROR': 1}
    assert summary['evaluation_scope'] == 'teacher_or_unverified_serving'
    assert summary['requests'] == 3
    assert summary['input_tokens'] == 20
    assert summary['output_tokens'] == 5


def test_metrics_do_not_trust_passed_flag_or_error_prediction():
    summary = runner.summarize_rows([
        {'expected': 'ESCALATE', 'predicted': 'ESCALATE', 'passed': True, 'error_type': 'Error'},
        {'expected': 'FAILED', 'passed': True},
    ])
    assert summary['accuracy'] == 0
    assert summary['errors'] == 2
    assert summary['confusion_matrix']['ESCALATE'] == {'ERROR': 1}


def test_empty_metrics_have_no_accuracy():
    summary = runner.summarize_rows([])
    assert summary['accuracy'] is None
    assert summary['attempted'] == summary['errors'] == summary['passed'] == 0
    assert summary['per_class'] == summary['confusion_matrix'] == {}


@pytest.mark.parametrize('dataset', ['expansion', 'bulk', 'fresh'])
@pytest.mark.parametrize('split', ['dev', 'eval'])
def test_expansion_rejects_nontraining_splits(split, dataset):
    with pytest.raises(SystemExit):
        runner.parse_args(['--dataset', dataset, '--split', split])


@pytest.mark.asyncio
async def test_expansion_run_also_rejects_eval_before_import_or_calls():
    args = runner.parse_args(['--dataset', 'expansion', '--split', 'train'])
    args.split = 'eval'
    with pytest.raises(ValueError, match='training-only'):
        await runner.run(args)


@pytest.mark.asyncio
async def test_expansion_dry_run_uses_distinct_source(monkeypatch):
    case = SimpleNamespace(key='expansion-1', split='train', scope='Repair tap', report='Fixed tap', expected='COMPLETED')
    monkeypatch.setitem(sys.modules, 'app.report_training_expansion',
                        SimpleNamespace(expansion_scenarios=lambda: [case]))
    args = runner.parse_args(['--dataset', 'expansion', '--split', 'train'])
    result = await runner.run(args)
    assert result['dataset'] == 'expansion'
    assert result['keys'] == ['expansion-1']
    assert result['live'] is False


def test_base_remains_default():
    assert runner.parse_args([]).dataset == 'base'
