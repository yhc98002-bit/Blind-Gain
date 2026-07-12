from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.rescore_blind_solvability_v2_guarded import (
    GUARDED_RESCORE_VERSION,
    rescore_rows,
)
from src.eval.blind_solvability import PILOT_ROW_SCHEMA_VERSION
from src.rewards.pilot_reward import SYMBOLIC_GRADER_GUARD_VERSION


def _legacy_row(row_index: int = 4) -> str:
    correct = "<answer>3</answer>"
    row = {
        "schema_version": PILOT_ROW_SCHEMA_VERSION,
        "condition": "none",
        "split": "train",
        "row_index": row_index,
        "ground_truth": "3",
        "greedy_response": correct,
        "sampled_responses": [correct] * 8 + ["<answer>9</answer>"] * 8,
        "legacy_score_marker": "preserve-me",
    }
    return json.dumps(row, sort_keys=True)


def test_guarded_rescore_upgrades_legacy_row_without_regenerating_responses() -> None:
    raw = _legacy_row()
    lines, stats = rescore_rows(
        [raw],
        condition="none",
        source_run="experiments/runs/legacy-none",
    )
    row = json.loads(lines[0])

    assert row["greedy_response"] == "<answer>3</answer>"
    assert len(row["sampled_responses"]) == 16
    assert row["legacy_score_marker"] == "preserve-me"
    assert row["guarded_rescore_version"] == GUARDED_RESCORE_VERSION
    assert row["symbolic_grader_guard_version"] == SYMBOLIC_GRADER_GUARD_VERSION
    assert row["symbolic_grader_timeout_seconds"] == 5.0
    assert row["greedy_native_r1v_shadow_valid"] is True
    assert all(row["sampled_native_r1v_shadow_valid"])
    assert len(row["guarded_rescore_source_row_sha256"]) == 64
    assert stats["n_responses"] == 17


def test_guarded_rescore_rejects_duplicate_source_identity() -> None:
    raw = _legacy_row()
    with pytest.raises(ValueError, match="duplicate source row identity"):
        rescore_rows(
            [raw, raw],
            condition="none",
            source_run="experiments/runs/legacy-none",
        )


def test_guarded_rescore_launcher_records_immutable_source_hashes() -> None:
    launcher = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "launch_guarded_l7_rescore.sh"
    ).read_text(encoding="utf-8")

    assert "rescore_source_output_sha256: $source_output_hash" in launcher
    assert "rescore_source_manifest_sha256: $source_manifest_hash" in launcher
    assert "l7_blind_solvability_geo3k_v2_guarded_rescore" in launcher
    assert "scripts/storage_guard.py --tier S" in launcher
    assert "gpu_ids: []" in launcher
    assert "one direct immutable run directory" in launcher
    assert "nohup setsid .venv/bin/python scripts/run_manifest_job.py" in launcher
