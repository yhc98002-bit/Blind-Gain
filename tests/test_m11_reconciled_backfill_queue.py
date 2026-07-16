from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.run_m11_reconciled_backfill_queue import (
    initial_state,
    target_running_gpus,
    validate_reconciled_run,
)


def _cell() -> dict:
    return {
        "id": "blind_internvl3_virl4096_real",
        "kind": "blind",
        "backend": "internvl3",
        "condition": "real",
        "limit": None,
    }


def _run(tmp_path: Path, *, condition: str = "real", node: str = "an12") -> str:
    run = tmp_path / "experiments/runs/fixture"
    run.mkdir(parents=True)
    metrics = run / "metrics.json"
    metrics.write_text("{}\n", encoding="utf-8")
    (run / "run_manifest.json").write_text(
        json.dumps(
            {
                "status": "complete",
                "exit_code": 0,
                "job_type": "m11_nonqwen_blind_sample_evaluation",
                "model_backend": "internvl3",
                "condition": condition,
                "dataset_id": None,
                "node": node,
                "gpu_ids": [4],
                "expected_artifacts": [str(metrics.relative_to(tmp_path))],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return str(run.relative_to(tmp_path))


def test_reconciled_run_rejects_identity_drift(tmp_path: Path) -> None:
    run = _run(tmp_path, condition="caption")

    with pytest.raises(ValueError, match="identity mismatch"):
        validate_reconciled_run(_cell(), run, tmp_path)


def test_target_gpu_reservation_ignores_same_index_on_other_node() -> None:
    state = {
        "cells": {
            "remote": {"status": "running", "node": "an12", "gpu": 4},
            "local": {"status": "running", "node": "an29", "gpu": 1},
        }
    }

    assert target_running_gpus(state, "an29") == {1}


def test_registered_config_reconciles_ten_and_leaves_only_gemma_pending() -> None:
    root = Path(__file__).resolve().parents[1]
    config = json.loads(
        (root / "configs/eval/m11_generalization_reconciled_backfill_v1.json").read_text(
            encoding="utf-8"
        )
    )

    state = initial_state(config, root)
    pending = [cell for cell in state["cells"].values() if cell["status"] == "pending"]

    assert len(state["cells"]) == 18
    assert len(pending) == 8
    assert all(cell["backend"] == "gemma3" for cell in pending)


def test_launcher_is_login_only_and_never_reads_performance_values() -> None:
    root = Path(__file__).resolve().parents[1]
    source = (root / "scripts/launch_m11_reconciled_backfill_queue.sh").read_text(
        encoding="utf-8"
    )

    assert 'job_type: "m11_generalization_reconciled_backfill_queue"' in source
    assert 'node: "login"' in source
    assert "--preflight-only" in source
    assert "critical M11 backfill code or config differs from HEAD" in source
    assert "metrics.json" not in source
    assert "build_generalization_audits" not in source
