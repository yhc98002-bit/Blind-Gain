from __future__ import annotations

import pytest

from scripts.compare_fliptrack_runs import compare_rows


def _row(pair_id: str, template: str, correct: bool) -> dict:
    return {
        "pair_id": pair_id,
        "template_id": template,
        "answer_a": "left",
        "answer_b": "right",
        "prediction_a": "left",
        "prediction_b": "right" if correct else "left",
    }


def test_compare_rows_reports_paired_delta_and_mcnemar_counts() -> None:
    left = [_row("p1", "t", False), _row("p2", "t", True)]
    right = [_row("p1", "t", True), _row("p2", "t", True)]
    result = compare_rows(left, right, "3b", "7b")
    assert result["pair_accuracy_delta"] == 0.5
    assert result["mcnemar"]["b01"] == 1
    assert result["mcnemar"]["b10"] == 0
    assert result["per_template"]["t"]["n_pairs"] == 2


def test_compare_rows_requires_exact_pair_coverage() -> None:
    with pytest.raises(ValueError, match="coverage mismatch"):
        compare_rows([_row("p1", "t", True)], [_row("p2", "t", True)], "left", "right")


def test_compare_rows_rejects_template_mismatch() -> None:
    with pytest.raises(ValueError, match="template mismatch"):
        compare_rows([_row("p1", "a", True)], [_row("p1", "b", True)], "left", "right")
