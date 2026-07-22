from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.restore_pilot_step60_merged import (
    restore_merged_checkpoint_for_evaluation,
)
from src.ops.storage_guard import evaluate_shared_guard


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    archive = tmp_path / "archive/global_step_60/actor/huggingface"
    archive.mkdir(parents=True)
    index = archive / "model.safetensors.index.json"
    shard = archive / "model-00001-of-00001.safetensors"
    _write_json(index, {"weight_map": {"layer": shard.name}})
    shard.write_bytes(b"registered checkpoint bytes")
    records = [
        {"file": path.name, "sha256": _sha256(path), "size_bytes": path.stat().st_size}
        for path in (index, shard)
    ]
    (archive / "merged_checkpoint.source.sha256").write_text(
        "".join(f"{item['sha256']}  {item['file']}\n" for item in records),
        encoding="utf-8",
    )
    destination = tmp_path / "checkpoints/pilot/run/global_step_60/actor/huggingface"
    relocation = tmp_path / "MERGED_CHECKPOINT_RELOCATED.json"
    _write_json(
        relocation,
        {
            "status": "merged_checkpoint_relocated",
            "source_path": str(destination),
            "archive_path": str(archive),
            "files": records,
        },
    )
    r19 = tmp_path / "step60_fliptrack_complete.json"
    _write_json(
        r19,
        {
            "schema_version": "blind-gains.pilot-step-eval-marker.v1",
            "status": "complete",
            "global_step": 60,
            "checkpoint_path": str(destination),
            "checkpoint_index_sha256": _sha256(index),
        },
    )
    return archive, destination, relocation, r19


def _passing_guard(required_bytes: int):
    return evaluate_shared_guard(
        path=Path("/shared"),
        operation="fixture",
        required_bytes=required_bytes,
        used_bytes=0,
        quota_bytes=1024**3,
        floor_bytes=0,
    )


def test_restore_is_guarded_hash_verified_and_preserves_archive(tmp_path: Path) -> None:
    archive, destination, relocation, r19 = _fixture(tmp_path)
    output = tmp_path / "run/restore.json"

    result = restore_merged_checkpoint_for_evaluation(
        archive=archive,
        destination=destination,
        relocation_marker=relocation,
        r19_marker=r19,
        output=output,
        storage_check=_passing_guard,
    )

    assert result["status"] == "restored_for_registered_evaluation"
    assert result["source_preserved"] is True
    assert archive.is_dir()
    assert destination.is_dir()
    assert _sha256(archive / "model.safetensors.index.json") == _sha256(
        destination / "model.safetensors.index.json"
    )
    assert json.loads(output.read_text())["storage_guard"]["status"] == "pass"


def test_restore_rejects_r19_hash_mismatch_before_destination_creation(
    tmp_path: Path,
) -> None:
    archive, destination, relocation, r19 = _fixture(tmp_path)
    payload = json.loads(r19.read_text())
    payload["checkpoint_index_sha256"] = "0" * 64
    _write_json(r19, payload)

    with pytest.raises(ValueError, match="R19 marker"):
        restore_merged_checkpoint_for_evaluation(
            archive=archive,
            destination=destination,
            relocation_marker=relocation,
            r19_marker=r19,
            output=tmp_path / "run/restore.json",
            storage_check=_passing_guard,
        )

    assert not destination.exists()
