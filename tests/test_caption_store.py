from __future__ import annotations

from pathlib import Path

from PIL import Image

from src.captioning.store import CAPTION_PROMPT, discover_images, select_shard


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
