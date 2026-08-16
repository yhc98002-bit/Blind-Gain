"""I10 fixtures for the P0.1 question-operand audit (cue-ladder bug class).

The class-defining failure: a verifier that checks gold against the *target*
while the question names a different entity. Before this round NO generator
had a fixture for it, and the premise-v2 re-checker validated golds against
`verifier_results.target_label` without ever parsing the question — so a
renamed question with a stale target_label passed. The pre-fix state fails
every corruption case below (the checks did not exist).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.audit_question_operands import audit_row, question_named_point

REPO = Path(__file__).resolve().parents[1]

B1_MANIFEST = REPO / "data/b1_geometry_track_v1/manifest.jsonl"
R19_MANIFEST = REPO / "data/fliptrack_v02r19_artifact_expanded_source_manifest.jsonl"
CHART_MANIFEST = REPO / "data/fliptrack_chart_v08_calibration_v1_manifest.jsonl"
DEV_V2 = REPO / "data/track4_premise_v2_dev_v2"


def _point_row(**overrides) -> dict:
    row = {
        "pair_id": "fixture_pair",
        "question": "What is the x-coordinate of point G7?",
        "answer_a": "7",
        "answer_b": "1",
        "verifier_results": {
            "target_label": "G7",
            "target_a": [1, -5],
            "target_b": [7, -5],
            "semantic_side_assignment_swapped": True,
        },
    }
    row.update(overrides)
    return row


def test_renamed_question_is_flagged() -> None:
    """The cue-ladder failure mode itself: question renamed, operand stale."""
    row = _point_row(question="What is the x-coordinate of point Q2?")
    checks, problems = audit_row(row)
    assert "question_names_target_label" in checks
    assert any("names point 'Q2'" in p and "'G7'" in p for p in problems)


def test_stale_gold_is_flagged_by_recompute() -> None:
    row = _point_row(answer_a="3")  # not the swapped target-b x
    checks, problems = audit_row(row)
    assert "coord_register_gold_recompute" in checks
    assert any("recomputed golds" in p for p in problems)


def test_swap_convention_is_honored() -> None:
    clean = _point_row()
    assert audit_row(clean)[1] == []
    unswapped = _point_row(
        answer_a="1",
        answer_b="7",
        verifier_results={
            "target_label": "G7",
            "target_a": [1, -5],
            "target_b": [7, -5],
            "semantic_side_assignment_swapped": False,
        },
    )
    assert audit_row(unswapped)[1] == []


def test_chart_x_mismatch_is_flagged() -> None:
    row = {
        "pair_id": "fixture_chart",
        "question": "What value does the starred series have at x = 3?",
        "verifier_results": {"target_x": 2},
    }
    checks, problems = audit_row(row)
    assert "question_names_target_x" in checks
    assert any("x = 3" in p for p in problems)


def test_row_without_checkable_operands_is_counted_not_passed() -> None:
    checks, problems = audit_row({"pair_id": "p", "question": "how many?",
                                  "verifier_results": {}})
    assert checks == [] and problems == []


def test_question_parser_takes_the_first_named_point() -> None:
    # premise-v2 final questions name the ANCHOR first; the anchor is the
    # registered operand ("Consider the point nearest to point T. ...").
    q = "Consider the point nearest to point T4. What is the x-coordinate of that nearest point?"
    assert question_named_point(q) == "T4"


def test_patched_premise_v2_verifier_refuses_renamed_question(tmp_path: Path) -> None:
    """End-to-end I10 fixture: a dev_v2-shaped batch with ONE renamed question
    must be refused by the patched re-checker (the pre-fix verifier passed it)."""
    if not DEV_V2.exists():
        pytest.skip("dev_v2 batch not on this host")
    corrupt = tmp_path / "batch"
    corrupt.mkdir()
    for name in ("manifest_causal_pairs.jsonl", "manifest_invariance_pairs.jsonl",
                 "manifest_premise_probe.jsonl", "groups_v2.jsonl"):
        rows = [json.loads(l) for l in (DEV_V2 / name).read_text().splitlines() if l.strip()]
        if name == "manifest_causal_pairs.jsonl":
            row = rows[0]
            label = row["verifier_results"]["target_label"]
            row["question"] = row["question"].replace(f"point {label}", "point ZZ9", 1)
        (corrupt / name).write_text(
            "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8"
        )
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts/verify_track4_premise_v2_dev_batch.py"),
         "--data-dir", str(corrupt), "--easy-n-points", "5"],
        capture_output=True, text=True, cwd=str(REPO),
    )
    assert proc.returncode == 1, "renamed question must be refused"
    assert "question-operand mismatch" in proc.stdout


@pytest.mark.skipif(not B1_MANIFEST.exists(), reason="frozen B1 batch not on this host")
def test_frozen_b1_manifest_is_operand_clean() -> None:
    problems = []
    for line in B1_MANIFEST.read_text().splitlines():
        if line.strip():
            problems.extend(audit_row(json.loads(line))[1])
    assert problems == []


@pytest.mark.skipif(not R19_MANIFEST.exists(), reason="frozen R19 manifest not on this host")
def test_frozen_r19_coordinate_register_is_operand_clean() -> None:
    problems = []
    for line in R19_MANIFEST.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if "coordinate_register" in (row.get("template_id") or ""):
            problems.extend(audit_row(row)[1])
    assert problems == []


@pytest.mark.skipif(not CHART_MANIFEST.exists(), reason="chart-v08 batch not on this host")
def test_chart_v08_calibration_is_operand_clean() -> None:
    problems = []
    for line in CHART_MANIFEST.read_text().splitlines():
        if line.strip():
            problems.extend(audit_row(json.loads(line))[1])
    assert problems == []
