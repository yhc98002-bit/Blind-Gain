from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from scripts.audit_caption_store import (
    audit_caption_store,
    audit_raw_caption_rows,
    expected_hashes_from_manifest,
)
from src.captioning.store import sha256_file
from src.captioning.store import CAPTION_DECODING, CAPTION_PROMPT, CAPTION_PROMPT_SHA256


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    image_path = image_dir / "item.png"
    Image.new("RGB", (8, 8), (17, 34, 51)).save(image_path)
    digest = sha256_file(image_path)
    manifest_path = tmp_path / "run_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "run_id": "fixture",
                "status": "complete",
                "exit_code": 0,
                "performance_values_opened": False,
                "expected_unique_image_count": 1,
                "model_id": "Qwen/fixture",
                "model_revision": "revision",
                "max_new_tokens": 384,
                "tensor_parallel_width": 4,
                "decoding": {"temperature": 0, "top_p": 1, "n": 1, "seed": 0},
            }
        ),
        encoding="utf-8",
    )
    source_roots_sha256 = __import__("hashlib").sha256(
        str(image_dir).encode("utf-8")
    ).hexdigest()
    store_path = tmp_path / "captions.jsonl"
    store_path.write_text(
        json.dumps(
            {
                "schema_version": "blind-gains.caption-store.v1",
                "image_sha256": digest,
                "image_path": str(image_path),
                "duplicate_paths": [],
                "caption": "A compact chart.",
                "caption_model_path": "Qwen/fixture",
                "caption_model_revision": "revision",
                "caption_prompt": CAPTION_PROMPT,
                "caption_prompt_sha256": CAPTION_PROMPT_SHA256,
                "max_new_tokens": 384,
                "decoding": CAPTION_DECODING,
                "source_roots_sha256": source_roots_sha256,
                "tensor_parallel_width": 4,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest_path, store_path, image_dir


def test_caption_store_audit_accepts_exact_source_bytes(tmp_path: Path) -> None:
    manifest, store, image_dir = _fixture(tmp_path)
    result = audit_caption_store(
        run_manifest_path=manifest,
        caption_store_path=store,
        input_dirs=[image_dir],
    )
    assert result["status"] == "pass"
    assert result["rows"] == 1


def test_caption_store_audit_rejects_source_mutation_after_captioning(tmp_path: Path) -> None:
    manifest, store, image_dir = _fixture(tmp_path)
    Image.new("RGB", (8, 8), (255, 0, 0)).save(image_dir / "item.png")
    with pytest.raises(ValueError, match="coverage mismatch"):
        audit_caption_store(
            run_manifest_path=manifest,
            caption_store_path=store,
            input_dirs=[image_dir],
        )


def test_legacy_manifest_and_shard_audit_api_remains_available(tmp_path: Path) -> None:
    manifest, store, image_dir = _fixture(tmp_path)
    row = json.loads(store.read_text(encoding="utf-8"))
    legacy_manifest = tmp_path / "manifest.jsonl"
    legacy_manifest.write_text(
        json.dumps({"members": [{"image_sha256": row["image_sha256"]}]}) + "\n",
        encoding="utf-8",
    )
    assert expected_hashes_from_manifest(legacy_manifest) == {row["image_sha256"]}
    audit = audit_raw_caption_rows(
        [store],
        expected_model="Qwen/fixture",
        expected_revision="revision",
        expected_tp=4,
    )
    assert audit["checks"] == {
        "one_row_per_image_hash": True,
        "caption_image_files_match_hashes": True,
        "expected_model_exact": True,
        "expected_revision_exact": True,
        "expected_tensor_parallel_width_exact": True,
    }
