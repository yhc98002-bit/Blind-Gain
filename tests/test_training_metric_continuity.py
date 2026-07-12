from __future__ import annotations

import json
from pathlib import Path

from scripts.audit_training_metric_continuity import audit_metric_continuity


def _training_row(step: int, *, validation: bool = False) -> dict:
    row = {
        "step": step,
        "reward": {"overall": 0.5, "format": 0.75, "accuracy": 0.25},
        "actor": {"kl_loss": 0.01, "ppo_kl": 0.001},
        "perf": {"time_per_step": 1.0},
        "response_length": {"mean": 10.0},
    }
    if validation:
        row["val"] = {"accuracy_reward": 0.25}
    return row


def _write(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )


def test_continuity_accepts_complete_immutable_resume_segments(tmp_path: Path) -> None:
    first = tmp_path / "steps_0_2.jsonl"
    second = tmp_path / "steps_3_4.jsonl"
    _write(first, [{"step": 0, "val": {}}, _training_row(1), _training_row(2, validation=True)])
    _write(second, [_training_row(3), _training_row(4, validation=True)])

    result = audit_metric_continuity(
        [first, second], expected_steps=4, validation_cadence=2
    )

    assert result["status"] == "pass"
    assert all(result["checks"].values())


def test_continuity_rejects_resume_truncation_pattern(tmp_path: Path) -> None:
    overwritten = tmp_path / "experiment_log.jsonl"
    _write(
        overwritten,
        [
            {"step": 2, "val": {}},
            _training_row(3),
            _training_row(4, validation=True),
        ],
    )

    result = audit_metric_continuity(
        [overwritten], expected_steps=4, validation_cadence=2
    )

    assert result["status"] == "fail"
    assert result["missing_training_steps"] == [1, 2]
    assert result["missing_validation_steps"] == [0]
    assert result["checks"]["all_training_steps_present_once"] is False
    assert result["checks"]["all_validation_steps_present_once"] is False


def test_continuity_rejects_duplicate_boundary_training_row(tmp_path: Path) -> None:
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    _write(first, [{"step": 0, "val": {}}, _training_row(1), _training_row(2, validation=True)])
    _write(second, [_training_row(2), _training_row(3), _training_row(4, validation=True)])

    result = audit_metric_continuity(
        [first, second], expected_steps=4, validation_cadence=2
    )

    assert result["status"] == "fail"
    assert result["duplicate_training_steps"] == [2]
