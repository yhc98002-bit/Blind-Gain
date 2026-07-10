from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.audit_caption_store import expected_hashes_from_manifest


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
