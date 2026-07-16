from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.audit_caption_store import (
    audit_raw_caption_rows,
    expected_hashes_from_manifest,
    expected_hashes_from_manifests,
)
from src.captioning.store import CAPTION_DECODING, CAPTION_PROMPT, CAPTION_PROMPT_SHA256


def test_caption_audit_collects_unique_hashes_across_multi_image_rows(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(
        json.dumps({"images": [{"sha256": "a"}, {"sha256": "b"}]})
        + "\n"
        + json.dumps({"images": [{"sha256": "b"}]})
        + "\n",
        encoding="utf-8",
    )

    assert expected_hashes_from_manifest(manifest) == {"a", "b"}


def test_caption_audit_rejects_manifest_without_image_hash(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(json.dumps({"images": [{}]}) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="without SHA256"):
        expected_hashes_from_manifest(manifest)


def test_caption_audit_supports_training_rows_with_string_paths_and_hash_metadata(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "training.jsonl"
    manifest.write_text(
        json.dumps(
            {
                "images": ["first.png", "second.png"],
                "metadata": {"image_sha256": ["first-hash", "second-hash"]},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    assert expected_hashes_from_manifest(manifest) == {"first-hash", "second-hash"}


def test_caption_audit_rejects_string_paths_without_exact_hash_count(tmp_path: Path) -> None:
    manifest = tmp_path / "training.jsonl"
    manifest.write_text(
        json.dumps(
            {
                "images": ["first.png", "second.png"],
                "metadata": {"image_sha256": ["only-one"]},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="lack one SHA256 per image"):
        expected_hashes_from_manifest(manifest)


def test_caption_audit_supports_packaged_pair_members(tmp_path: Path) -> None:
    manifest = tmp_path / "release.jsonl"
    manifest.write_text(
        json.dumps(
            {
                "members": [
                    {"image_sha256": "member-a"},
                    {"image_sha256": "member-b"},
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )

    assert expected_hashes_from_manifest(manifest) == {"member-a", "member-b"}


def test_caption_audit_detects_cross_manifest_overlap(tmp_path: Path) -> None:
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    first.write_text(json.dumps({"members": [{"image_sha256": "same"}]}) + "\n")
    second.write_text(json.dumps({"members": [{"image_sha256": "same"}]}) + "\n")

    hashes, overlaps = expected_hashes_from_manifests([first, second])

    assert hashes == {"same"}
    assert overlaps == {"same": [str(first), str(second)]}


def test_raw_caption_audit_rejects_duplicate_rows_and_wrong_tp(tmp_path: Path) -> None:
    image = tmp_path / "image.bin"
    image.write_bytes(b"image")
    import hashlib

    digest = hashlib.sha256(image.read_bytes()).hexdigest()
    row = {
        "schema_version": "blind-gains.caption-store.v1",
        "image_sha256": digest,
        "image_path": str(image),
        "caption": "visible content",
        "caption_prompt": CAPTION_PROMPT,
        "caption_prompt_sha256": CAPTION_PROMPT_SHA256,
        "decoding": CAPTION_DECODING,
        "max_new_tokens": 384,
        "caption_model_path": "model",
        "caption_model_revision": "revision",
        "tensor_parallel_width": 2,
    }
    shard = tmp_path / "captions.jsonl"
    shard.write_text(json.dumps(row) + "\n" + json.dumps(row) + "\n")

    audit = audit_raw_caption_rows(
        [shard],
        expected_model="model",
        expected_revision="revision",
        expected_tp=4,
    )

    assert audit["checks"]["one_row_per_image_hash"] is False
    assert audit["checks"]["caption_image_files_match_hashes"] is True
    assert audit["checks"]["expected_tensor_parallel_width_exact"] is False
