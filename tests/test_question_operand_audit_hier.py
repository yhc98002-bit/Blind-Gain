"""Hier gates for the question-operand audit (pre-freeze cleanup): before
2026-08-17 every hier row fell into the unchecked bucket because the audit
keyed on `target_label`/`target_x`, which hier rows do not carry."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "audit_question_operands", ROOT / "scripts/audit_question_operands.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def hier_row(layer, question, label_a="V6", label_b="V6"):
    return {"pair_id": f"hier_test__{layer}", "category": "hier_v1",
            "layer": layer, "question": question,
            "verifier_results": {"target_label_a": label_a,
                                 "target_label_b": label_b}}


def test_l3_withholding_identity_passes():
    checks, problems = AUDIT.audit_row(hier_row(
        "l3", "Consider the point with the smallest y-coordinate. "
              "What is its x-coordinate?"))
    assert "hier_l3_probe_names_no_target" in checks
    assert problems == []


def test_l3_naming_target_is_flagged():
    checks, problems = AUDIT.audit_row(hier_row(
        "l3", "Point V6 has the smallest y-coordinate. What is its "
              "x-coordinate?"))
    assert problems and "names target" in problems[0]


def test_l3_switch_names_neither_side():
    _, problems = AUDIT.audit_row(hier_row(
        "l3", "Consider the series with the highest value at x = 5. "
              "What value does Harbor have at x = 3?",
        label_a="K6", label_b="Harbor"))
    assert problems and "Harbor" in problems[0]


def test_probe_covered_like_l3():
    checks, problems = AUDIT.audit_row(hier_row(
        "probe", "Which labeled point has the smallest y-coordinate?"))
    assert "hier_l3_probe_names_no_target" in checks
    assert problems == []


def test_l2_naming_the_target_passes_coord_and_chart():
    for question, label in (
        ("Point V6 has the smallest y-coordinate. What is the x-coordinate "
         "of point V6?", "V6"),
        ("The series Harbor has the highest value at x = 5. What value does "
         "Harbor have at x = 3?", "Harbor"),
    ):
        checks, problems = AUDIT.audit_row(
            hier_row("l2", question, label_a=label, label_b=label))
        assert "hier_l2_l1_names_target" in checks
        assert problems == []


def test_l2_wrong_label_is_flagged():
    _, problems = AUDIT.audit_row(hier_row(
        "l2", "Point W8 has the smallest y-coordinate. What is the "
              "x-coordinate of point W8?"))
    assert problems and "names 'W8'" in problems[0]


def test_l2_with_differing_side_identities_is_flagged():
    _, problems = AUDIT.audit_row(hier_row(
        "l1", "Point V6 has the smallest y-coordinate. What is the "
              "x-coordinate of point V6?", label_a="V6", label_b="B8"))
    assert problems and "A2" in problems[0]


def test_hier_rows_are_no_longer_unchecked():
    checks, _ = AUDIT.audit_row(hier_row(
        "l3", "Consider the point with the largest y-coordinate. "
              "What is its x-coordinate?"))
    assert checks, "hier rows must not fall into the unchecked bucket"
