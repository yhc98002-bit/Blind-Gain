from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.relocate_merged_checkpoint import relocate_merged_checkpoint


def _merged(tmp_path: Path) -> Path:
    source = tmp_path / "global_step_60" / "actor" / "huggingface"
    source.mkdir(parents=True)
    shard = source / "model-00001-of-00001.safetensors"
    shard.write_bytes(b"weights")
    (source / "model.safetensors.index.json").write_text(
        json.dumps({"weight_map": {"weight": shard.name}}) + "\n",
        encoding="utf-8",
    )
    (source / "config.json").write_text("{}\n", encoding="utf-8")
    return source


def test_merged_relocation_verifies_archive_before_source_removal(tmp_path: Path) -> None:
    source = _merged(tmp_path / "source")
    archive = tmp_path / "archive" / "huggingface"

    payload = relocate_merged_checkpoint(source, archive)

    assert not source.exists()
    assert (archive / "model-00001-of-00001.safetensors").read_bytes() == b"weights"
    assert (archive / "merged_checkpoint.source.sha256").is_file()
    marker = json.loads(
        (source.parent / "MERGED_CHECKPOINT_RELOCATED.json").read_text(encoding="utf-8")
    )
    assert marker["checksum_manifest_sha256"] == payload["checksum_manifest_sha256"]


def test_merged_relocation_refuses_existing_destination_without_touching_source(tmp_path: Path) -> None:
    source = _merged(tmp_path / "source")
    archive = tmp_path / "archive" / "huggingface"
    archive.mkdir(parents=True)

    with pytest.raises(FileExistsError, match="overwrite"):
        relocate_merged_checkpoint(source, archive)

    assert source.is_dir()


def test_merged_relocation_rejects_index_path_traversal(tmp_path: Path) -> None:
    source = _merged(tmp_path / "source")
    (source / "model.safetensors.index.json").write_text(
        json.dumps({"weight_map": {"weight": "../outside.safetensors"}}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unsafe shard path"):
        relocate_merged_checkpoint(source, tmp_path / "archive")

    assert source.is_dir()
