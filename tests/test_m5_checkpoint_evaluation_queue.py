from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts import run_m5_checkpoint_evaluation_queue as queue


ROOT = Path(__file__).resolve().parents[1]


def test_parse_gpu_snapshot_requires_structural_free_capacity() -> None:
    snapshot = "0, 2, 0\n1, 1024, 10\n2, 1025, 0\n3, 2, 11\n"

    assert queue.parse_gpu_snapshot(snapshot) == [0, 1]
    with pytest.raises(ValueError, match="invalid nvidia-smi"):
        queue.parse_gpu_snapshot("GPU 0 is free")


def test_capacity_selection_prefers_more_host_headroom(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshots = {
        "an12": {
            "node": "an12",
            "available": True,
            "free_gpus": [4, 5, 6, 7],
            "mem_available_kib": 600_000_000,
        },
        "an29": {
            "node": "an29",
            "available": True,
            "free_gpus": [0, 1, 3, 4],
            "mem_available_kib": 700_000_000,
        },
    }
    monkeypatch.setattr(queue, "node_capacity", lambda node: snapshots[node])

    selected = queue.choose_capacity(["an12", "an29"])

    assert selected is not None
    assert selected["node"] == "an29"
    assert selected["selected_gpus"] == [0, 1, 3, 4]


def test_restart_discovers_exact_existing_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(queue, "ROOT", tmp_path)
    source = tmp_path / "experiments/runs/source"
    checkpoint = tmp_path / "checkpoint"
    child = tmp_path / "experiments/runs/child"
    child.mkdir(parents=True)
    (child / "run_manifest.json").write_text(
        json.dumps(
            {
                "job_type": "m5_geo3k_checkpoint_eval",
                "global_step": 200,
                "source_training_run": str(source),
                "model_revision": str(checkpoint),
                "status": "running",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    discovered = queue.discover_evaluation_run(
        source_run=source,
        checkpoint=checkpoint,
        step=200,
        job_type="m5_geo3k_checkpoint_eval",
    )

    assert discovered == Path("experiments/runs/child")


def test_queue_is_nonpreemptive_and_never_opens_performance_values() -> None:
    source = (ROOT / "scripts/run_m5_checkpoint_evaluation_queue.py").read_text(
        encoding="utf-8"
    )
    assert "os.kill" not in source
    assert "kill -9" not in source
    assert "pair_accuracy" not in source
    assert '"performance_values_opened": False' in source
    assert "valid_evaluation_marker" in source
    assert "stable_polls" in source
    assert "gray" in source and "noise" in source


def test_queue_launcher_and_recovery_wiring_are_fail_closed() -> None:
    subprocess.run(
        ["bash", "-n", str(ROOT / "scripts/launch_m5_checkpoint_evaluation_queue.sh")],
        check=True,
    )
    recovery = (ROOT / "scripts/launch_m5_anchor_recovery150.sh").read_text(
        encoding="utf-8"
    )
    assert "launch_m5_checkpoint_evaluation_queue.sh" in recovery
    assert "200,300,400" in recovery
    assert recovery.index("EVALUATION_QUEUE=") < recovery.index('ssh "${NODE}" "cd')
