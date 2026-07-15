from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.watch_pilot_step_evaluation import find_existing_aggregate, validate_evaluation
from scripts.finalize_pilot_step_evaluation import R19_MANIFEST_SHA256
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT


ROOT = Path(__file__).resolve().parents[1]


def _evaluation(training: Path, checkpoint: Path) -> dict:
    return {
        "job_type": "fliptrack_v02_image_evaluation",
        "source_training_run": str(training),
        "model_revision": str(checkpoint),
        "global_step": 60,
        "image_mode": "real",
        "max_new_tokens": 32,
        "decoding": {"temperature": 0.0, "top_p": 1.0, "n": 1},
        "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
        "data_manifest_hash": R19_MANIFEST_SHA256,
    }


def test_evaluation_contract_rejects_a_different_checkpoint(tmp_path: Path) -> None:
    training = tmp_path / "training"
    checkpoint = tmp_path / "checkpoint"
    payload = _evaluation(training, checkpoint)
    payload["model_revision"] = str(tmp_path / "other-checkpoint")
    with pytest.raises(ValueError, match="evaluation contract mismatch"):
        validate_evaluation(
            payload,
            evaluation_run=tmp_path / "evaluation",
            training_run=training,
            checkpoint_path=checkpoint,
            global_step=60,
        )


def test_duplicate_aggregate_lineage_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "experiments/runs/eval"
    source.mkdir(parents=True)
    for suffix in ("one", "two"):
        run = tmp_path / f"experiments/runs/fliptrack_aggregate_fixed_{suffix}"
        run.mkdir()
        (run / "run_manifest.json").write_text(
            json.dumps({"source_run": str(source)}), encoding="utf-8"
        )
    with pytest.raises(ValueError, match="multiple aggregate runs"):
        find_existing_aggregate("fixed", source, tmp_path)


def test_launcher_is_valid_and_binds_marker_to_training_step() -> None:
    launcher = ROOT / "scripts/launch_pilot_step_evaluation_watch.sh"
    subprocess.run(["bash", "-n", str(launcher)], check=True)
    source = launcher.read_text(encoding="utf-8")
    assert 'EXPECTED_MARKER="${TRAINING_RUN}/step${GLOBAL_STEP}_fliptrack_complete.json"' in source
    assert "pilot evaluation watcher code differs from HEAD" in source
    assert "active finalization watcher already owns marker" in source
    assert 'job_type: "pilot_step_evaluation_finalize_watch"' in source
    assert "scientific_gate_decision: null" in source
