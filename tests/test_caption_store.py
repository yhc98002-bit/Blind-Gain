from __future__ import annotations

import json
import os
from pathlib import Path

from PIL import Image
import pytest

from scripts.merge_caption_stores import _publish_artifacts
from src.captioning.store import CAPTION_PROMPT, discover_images, merge_caption_rows, select_shard


def test_caption_store_deduplicates_by_content_hash_and_shards_exactly(tmp_path: Path) -> None:
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    Image.new("RGB", (8, 8), "red").save(image_dir / "first.png")
    Image.new("RGB", (8, 8), "red").save(image_dir / "duplicate.png")
    Image.new("RGB", (8, 8), "blue").save(image_dir / "second.png")
    items = discover_images(image_dir)
    assert len(items) == 2
    assert sorted(len(item["duplicate_paths"]) for item in items) == [0, 1]
    shards = [select_shard(items, 2, index) for index in range(2)]
    assert sorted(item["image_sha256"] for shard in shards for item in shard) == sorted(
        item["image_sha256"] for item in items
    )


def test_caption_prompt_is_question_blind_and_has_no_template_slot() -> None:
    lowered = CAPTION_PROMPT.lower()
    assert "question:" not in lowered
    assert "answer:" not in lowered
    assert "{" not in CAPTION_PROMPT and "}" not in CAPTION_PROMPT


def _caption_row(digest: str, caption: str, model: str = "model") -> dict:
    return {
        "image_sha256": digest,
        "caption": caption,
        "caption_model_path": model,
        "caption_prompt_sha256": "prompt-hash",
        "max_new_tokens": 384,
    }


def test_caption_merge_requires_exact_release_coverage(tmp_path: Path) -> None:
    shard_a = tmp_path / "a.jsonl"
    shard_b = tmp_path / "b.jsonl"
    shard_a.write_text(json.dumps(_caption_row("a", "caption a")) + "\n", encoding="utf-8")
    shard_b.write_text(json.dumps(_caption_row("b", "caption b")) + "\n", encoding="utf-8")
    rows, summary = merge_caption_rows([shard_b, shard_a], {"a", "b"})
    assert [row["image_sha256"] for row in rows] == ["a", "b"]
    assert summary["coverage_complete"] is True
    with pytest.raises(ValueError, match="coverage mismatch"):
        merge_caption_rows([shard_a], {"a", "b"})


def test_caption_merge_rejects_conflicting_duplicate(tmp_path: Path) -> None:
    shard = tmp_path / "captions.jsonl"
    shard.write_text(
        json.dumps(_caption_row("same", "first"))
        + "\n"
        + json.dumps(_caption_row("same", "second"))
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="conflicting captions"):
        merge_caption_rows([shard])


def test_caption_merge_publication_rolls_back_on_second_rename(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "captions.jsonl"
    summary = tmp_path / "summary.json"
    real_replace = os.replace
    calls = 0

    def fail_second_replace(source: str | Path, destination: str | Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected summary publication failure")
        real_replace(source, destination)

    monkeypatch.setattr("scripts.merge_caption_stores.os.replace", fail_second_replace)
    with pytest.raises(OSError, match="injected"):
        _publish_artifacts([_caption_row("a", "caption")], {"n_images": 1}, output, summary)

    assert not output.exists()
    assert not summary.exists()
    assert not Path(f"{output}.partial").exists()
    assert not Path(f"{summary}.partial").exists()
