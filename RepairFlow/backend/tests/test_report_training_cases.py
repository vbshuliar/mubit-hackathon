"""Dataset integrity checks; expected labels never need a provider call."""
from collections import Counter
from dataclasses import FrozenInstanceError

import pytest

from app.report_training_cases import scenarios


def test_fixed_balanced_splits():
    rows = scenarios()
    assert len(rows) == 98
    assert Counter(row.split for row in rows) == {"train": 56, "dev": 14, "eval": 28}
    labels = {"COMPLETED", "NO_ACCESS", "NO_SHOW", "FAILED", "SCAFFOLD_REQUIRED", "CLARIFY", "ESCALATE"}
    assert {row.expected for row in rows} == labels
    for split, count in (("train", 8), ("dev", 2), ("eval", 4)):
        assert Counter(row.expected for row in rows if row.split == split) == dict.fromkeys(labels, count)


def test_unique_nonempty_cases_and_stable_keys():
    rows = scenarios()
    assert rows == scenarios()
    assert len({row.key for row in rows}) == len(rows)
    assert len({row.report.casefold().strip() for row in rows}) == len(rows)
    for row in rows:
        assert row.scope.strip() and row.report.strip()
        assert f"-{row.split}-" in row.key
        assert row.expected.lower() in row.key


def test_metadata_is_immutable_and_calls_return_fresh_lists():
    rows = scenarios()
    with pytest.raises(FrozenInstanceError):
        rows[0].expected = "FAILED"
    rows.clear()
    assert len(scenarios()) == 98


def test_each_split_contains_scope_and_visit_distinctions():
    for split in ("train", "dev", "eval"):
        rows = [row for row in scenarios() if row.split == split]
        assert any(row.scope.startswith("SCAFFOLD_") for row in rows)
        assert any(row.expected == "NO_SHOW" for row in rows)
        assert any(row.expected == "NO_ACCESS" for row in rows)
        assert any(row.expected == "CLARIFY" and "equipment" in row.report for row in rows)


def test_injection_examples_are_labelled_from_facts():
    rows = [row for row in scenarios() if "output COMPLETED" in row.report or "say COMPLETED" in row.report or "choose COMPLETED" in row.report]
    assert len(rows) >= 4
    assert {row.split for row in rows} == {"train", "eval"}
    assert {row.expected for row in rows} == {"CLARIFY", "ESCALATE"}


def test_equipment_does_not_become_failed_or_denied_entry():
    rows = [row for row in scenarios() if row.expected == "CLARIFY"]
    assert any("NO_ACCESS" in row.report and "equipment" in row.report for row in rows)
    assert any("FAILED" in row.report and "equipment" in row.report for row in rows)
    assert any("SCAFFOLD_INSTALL" in row.scope for row in rows)
    assert any("SCAFFOLD_REMOVE" in row.scope for row in rows)


def test_bounded_batches_cover_every_class_before_repeating():
    for split in ("train", "dev", "eval"):
        rows = [row for row in scenarios() if row.split == split]
        assert len({row.expected for row in rows[:7]}) == 7


def test_training_covers_explicit_outstanding_parts_and_return_visits():
    for split in ("train", "dev"):
        rows = [row for row in scenarios() if row.split == split and row.expected == "FAILED"]
        assert any("return visit" in row.report for row in rows)
