"""Offline invariants for additional training evidence; no model calls."""
from collections import Counter
from dataclasses import FrozenInstanceError

import pytest

from app.agents.report_task import ReportDecision, ReportInput
from app.report_training_expansion import expansion_scenarios


def test_balanced_training_only_expansion():
    cases = expansion_scenarios()
    assert len(cases) == 49
    assert {case.split for case in cases} == {'train'}
    assert Counter(case.expected for case in cases) == {
        'COMPLETED': 7, 'NO_ACCESS': 7, 'NO_SHOW': 7, 'FAILED': 7,
        'SCAFFOLD_REQUIRED': 7, 'CLARIFY': 7, 'ESCALATE': 7,
    }


def test_keys_and_evidence_are_unique_and_stable():
    cases = expansion_scenarios()
    assert cases == expansion_scenarios()
    assert len({case.key for case in cases}) == len(cases)
    assert len({(case.scope, case.report) for case in cases}) == len(cases)
    assert len({case.report for case in cases}) == len(cases)
    assert all(case.key.startswith('expand-v2-') for case in cases)


def test_every_case_conforms_to_frozen_input_and_output_contract():
    for case in expansion_scenarios():
        evidence = ReportInput(work_scope=case.scope, report_text=case.report)
        assert set(evidence.model_dump()) == {'work_scope', 'report_text'}
        assert 'expected' not in evidence.model_dump()
        assert ReportDecision(classification=case.expected).classification == case.expected
        assert len(case.scope) + len(case.report) < 6000


def test_scenarios_are_immutable():
    with pytest.raises(FrozenInstanceError):
        expansion_scenarios()[0].expected = 'FAILED'


def test_each_small_batch_covers_every_category():
    cases = expansion_scenarios()
    for offset in range(0, 49, 7):
        assert len({case.expected for case in cases[offset:offset + 7]}) == 7
