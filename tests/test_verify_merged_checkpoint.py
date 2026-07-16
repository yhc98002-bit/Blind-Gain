from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.verify_merged_checkpoint import verify_checkpoint


def _checkpoint(tmp_path: Path) -> Path:
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()
    (checkpoint / "model-00001-of-00002.safetensors").write_bytes(b"first")
    (checkpoint / "model-00002-of-00002.safetensors").write_bytes(b"second")
    (checkpoint / "model.safetensors.index.json").write_text(
        json.dumps(
            {
                "weight_map": {
                    "layer.0": "model-00001-of-00002.safetensors",
                    "layer.1": "model-00002-of-00002.safetensors",
                }
            }
        ),
        encoding="utf-8",
    )
    return checkpoint


def test_verifier_hashes_exact_index_and_shard_set(tmp_path: Path) -> None:
    payload, checksums = verify_checkpoint(_checkpoint(tmp_path))

    assert payload["status"] == "pass"
    assert payload["shard_count"] == 2
    assert payload["files_stable_during_hash"] is True
    assert checksums.count("\n") == 3


def test_verifier_rejects_missing_referenced_shard(tmp_path: Path) -> None:
    checkpoint = _checkpoint(tmp_path)
    (checkpoint / "model-00002-of-00002.safetensors").unlink()

    with pytest.raises(ValueError, match="shard set mismatch"):
        verify_checkpoint(checkpoint)


def test_verifier_rejects_index_path_traversal(tmp_path: Path) -> None:
    checkpoint = _checkpoint(tmp_path)
    (checkpoint / "model.safetensors.index.json").write_text(
        json.dumps({"weight_map": {"layer.0": "../outside.safetensors"}}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unsafe shard path"):
        verify_checkpoint(checkpoint)
