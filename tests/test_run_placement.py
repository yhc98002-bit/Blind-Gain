from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.run_placement import RunPlacement, record_run_placement


def test_tp1_replica_placement_is_recorded_atomically(tmp_path: Path) -> None:
    manifest = tmp_path / "run_manifest.json"
    manifest.write_text(
        json.dumps({"run_id": "run", "node": "an29", "status": "running"}),
        encoding="utf-8",
    )

    result = record_run_placement(
        manifest,
        RunPlacement("an29", (1,), 1, 1, "Independent TP1 evaluation replica."),
    )

    assert result["gpu_ids"] == [1]
    assert result["tensor_parallel_width"] == 1
    assert result["replica_count"] == 1
    assert json.loads(manifest.read_text(encoding="utf-8")) == result


def test_colocated_fsdp_training_records_tp1_without_fake_replicas() -> None:
    placement = RunPlacement(
        "an12", (0, 1, 2, 3), 1, 1, "One synchronous FSDP/GRPO job on one node."
    )

    assert placement.fields()["tensor_parallel_width"] == 1
    assert placement.fields()["replica_count"] == 1


@pytest.mark.parametrize(
    "placement, message",
    [
        (RunPlacement("an12,an29", (0,), 1, 1, "split"), "one host"),
        (RunPlacement("an12", (0,), 2, 1, "too wide"), "exceeds"),
        (RunPlacement("login", (0,), 1, 1, "invalid CPU record"), "TP0"),
    ],
)
def test_invalid_or_cross_node_placement_is_rejected(
    placement: RunPlacement, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        placement.validate()


def test_existing_conflicting_placement_cannot_be_rewritten(tmp_path: Path) -> None:
    manifest = tmp_path / "run_manifest.json"
    manifest.write_text(
        json.dumps({"run_id": "run", "node": "an12", "gpu_ids": [4]}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="gpu_ids"):
        record_run_placement(
            manifest,
            RunPlacement("an12", (5,), 1, 1, "Conflicting GPU placement."),
        )
