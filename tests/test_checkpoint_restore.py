from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.ops.checkpoint_restore import RESTORE_MARKER, restore_raw_checkpoint


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    actor = tmp_path / "shared" / "global_step_80" / "actor"
    archive = tmp_path / "archive" / "global_step_80" / "actor"
    actor.mkdir(parents=True)
    archive.mkdir(parents=True)
    checksums = []
    for family in ("model", "optim"):
        for rank in range(2):
            path = archive / f"{family}_world_size_2_rank_{rank}.pt"
            path.write_bytes(f"{family}-{rank}".encode("ascii"))
            checksums.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n")
    (archive / "raw_training_state.source.sha256").write_text(
        "".join(checksums), encoding="ascii"
    )
    (actor / "RAW_STATE_RELOCATED.json").write_text(
        json.dumps({"archive_path": str(archive.resolve())}), encoding="utf-8"
    )
    return actor, archive


def test_restore_rehydrates_and_reverifies_every_raw_shard(tmp_path: Path) -> None:
    actor, archive = _fixture(tmp_path)
    guarded: list[int] = []

    payload = restore_raw_checkpoint(actor, archive, guard=guarded.append)

    assert payload["status"] == "restored_for_optimizer_resume"
    assert len(payload["restored_files"]) == 4
    assert guarded == [sum(path.stat().st_size for path in archive.glob("*.pt"))]
    assert (actor / RESTORE_MARKER).is_file()
    assert len(list(actor.glob("*_world_size_*.pt"))) == 4
    assert len(list(archive.glob("*_world_size_*.pt"))) == 4


def test_restore_rejects_archive_checksum_drift_before_guard_or_copy(tmp_path: Path) -> None:
    actor, archive = _fixture(tmp_path)
    (archive / "model_world_size_2_rank_0.pt").write_bytes(b"corrupt")
    guarded: list[int] = []

    with pytest.raises(RuntimeError, match="checksum mismatch"):
        restore_raw_checkpoint(actor, archive, guard=guarded.append)

    assert guarded == []
    assert not list(actor.glob("*_world_size_*.pt"))


def test_restore_refuses_to_overwrite_conflicting_shared_shard(tmp_path: Path) -> None:
    actor, archive = _fixture(tmp_path)
    (actor / "model_world_size_2_rank_0.pt").write_bytes(b"different")

    with pytest.raises(RuntimeError, match="conflicts with archive"):
        restore_raw_checkpoint(actor, archive)
