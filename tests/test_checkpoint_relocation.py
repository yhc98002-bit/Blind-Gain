from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.relocate_easyr1_raw_checkpoint import relocate_raw_checkpoint


def _actor(tmp_path: Path, *, merged: bool = True) -> Path:
    actor = tmp_path / "checkpoint" / "actor"
    actor.mkdir(parents=True)
    for family in ("model", "optim"):
        for rank in range(2):
            (actor / f"{family}_world_size_2_rank_{rank}.pt").write_bytes(
                f"{family}-{rank}".encode("ascii")
            )
    if merged:
        huggingface = actor / "huggingface"
        huggingface.mkdir()
        (huggingface / "model.safetensors.index.json").write_text("{}\n", encoding="ascii")
        (huggingface / "model-00001-of-00001.safetensors").write_bytes(b"merged")
    return actor


def test_relocation_verifies_archive_before_removing_raw_shards(tmp_path: Path) -> None:
    actor = _actor(tmp_path)
    archive = tmp_path / "archive"

    payload = relocate_raw_checkpoint(actor, archive)

    assert payload["status"] == "raw_training_state_relocated_due_to_shared_quota"
    assert len(payload["files"]) == 4
    assert not list(actor.glob("model_world_size_*.pt"))
    assert not list(actor.glob("optim_world_size_*.pt"))
    assert (actor / "huggingface" / "model.safetensors.index.json").is_file()
    marker = json.loads((actor / "RAW_STATE_RELOCATED.json").read_text(encoding="utf-8"))
    assert marker["archive_path"] == str(archive.resolve())
    assert sorted(path.name for path in archive.glob("*.pt")) == sorted(
        record["file"] for record in payload["files"]
    )


def test_relocation_refuses_to_remove_shards_without_merged_checkpoint(tmp_path: Path) -> None:
    actor = _actor(tmp_path, merged=False)

    with pytest.raises(FileNotFoundError, match="merged Hugging Face checkpoint"):
        relocate_raw_checkpoint(actor, tmp_path / "archive")

    assert len(list(actor.glob("*_world_size_*.pt"))) == 4


def test_relocation_rejects_conflicting_archive_file(tmp_path: Path) -> None:
    actor = _actor(tmp_path)
    archive = tmp_path / "archive"
    archive.mkdir()
    (archive / "model_world_size_2_rank_0.pt").write_bytes(b"wrong")

    with pytest.raises(RuntimeError, match="mismatch"):
        relocate_raw_checkpoint(actor, archive)

    assert len(list(actor.glob("*_world_size_*.pt"))) == 4


def test_relocation_rejects_incomplete_rank_set(tmp_path: Path) -> None:
    actor = _actor(tmp_path)
    (actor / "optim_world_size_2_rank_1.pt").unlink()

    with pytest.raises(ValueError, match="incomplete optim shards"):
        relocate_raw_checkpoint(actor, tmp_path / "archive")

    assert len(list(actor.glob("*_world_size_*.pt"))) == 3
