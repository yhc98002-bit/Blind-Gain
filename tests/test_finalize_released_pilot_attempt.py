from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.finalize_released_pilot_attempt import finalize_released_attempt


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    checkpoint_root = tmp_path / "checkpoints/pilot/mech_a2_gray_resume60"
    checkpoint_root.mkdir(parents=True)
    with (checkpoint_root / "experiment_log.jsonl").open("w", encoding="utf-8") as handle:
        for step in (60, 61, 62, 63, 64):
            handle.write(json.dumps({"step": step, "opaque_metrics": {"do_not_read": step}}) + "\n")
    manifest = tmp_path / "experiments/runs/interrupted/run_manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps(
            {
                "run_id": "interrupted",
                "status": "running",
                "job_type": "l13_mechanical_pilot_arm",
                "arm": "a2_gray",
                "node": "an21",
                "resumed_from_global_step": 60,
                "checkpoint_path": str(checkpoint_root),
                "deviations": [],
            }
        ),
        encoding="utf-8",
    )
    return manifest, tmp_path / "evidence.json", checkpoint_root


def test_finalize_released_attempt_records_discarded_steps(tmp_path: Path) -> None:
    manifest, evidence, _ = _fixture(tmp_path)
    result = finalize_released_attempt(
        manifest,
        evidence,
        "user-confirmed-an21-released",
        project_root=tmp_path,
    )
    finalized = json.loads(manifest.read_text(encoding="utf-8"))
    assert finalized["status"] == "fail"
    assert finalized["termination_reason"]["discarded_uncheckpointed_steps"] == [61, 62, 63, 64]
    assert result["durable_checkpoints"] == []
    assert evidence.is_file()


def test_finalize_released_attempt_rejects_a_durable_checkpoint(tmp_path: Path) -> None:
    manifest, evidence, checkpoint_root = _fixture(tmp_path)
    (checkpoint_root / "global_step_80").mkdir()
    with pytest.raises(ValueError, match="durable resume state"):
        finalize_released_attempt(
            manifest,
            evidence,
            "user-confirmed-an21-released",
            project_root=tmp_path,
        )
    assert json.loads(manifest.read_text(encoding="utf-8"))["status"] == "running"
    assert not evidence.exists()
