from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.captioning.store import (
    CAPTION_DECODING,
    CAPTION_PROMPT,
    SCHEMA_VERSION,
    load_validated_caption_prefix,
)


def _items() -> list[dict[str, object]]:
    return [
        {
            "image_sha256": f"sha-{index}",
            "image_path": f"images/{index}.png",
            "duplicate_paths": [],
        }
        for index in range(3)
    ]


def _row(item: dict[str, object], model: str = "model") -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        **item,
        "caption": "A question-blind caption.",
        "caption_model_path": model,
        "caption_model_revision": "revision",
        "caption_prompt": CAPTION_PROMPT,
        "caption_prompt_sha256": hashlib.sha256(CAPTION_PROMPT.encode("utf-8")).hexdigest(),
        "max_new_tokens": 384,
        "decoding": CAPTION_DECODING,
        "tensor_parallel_width": 1,
    }


def _write(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_caption_resume_accepts_canonical_prefix(tmp_path: Path) -> None:
    items = _items()
    source = tmp_path / "partial.jsonl"
    _write(source, [_row(item) for item in items[:2]])

    lines = load_validated_caption_prefix(
        source,
        items,
        model_path="model",
        max_new_tokens=384,
        model_revision="revision",
        tensor_parallel_width=1,
    )

    assert len(lines) == 2


def test_caption_resume_rejects_reordered_images(tmp_path: Path) -> None:
    items = _items()
    source = tmp_path / "partial.jsonl"
    _write(source, [_row(items[1]), _row(items[0])])

    with pytest.raises(ValueError, match="image_sha256"):
        load_validated_caption_prefix(source, items, model_path="model", max_new_tokens=384)


def test_caption_resume_rejects_model_contract_drift(tmp_path: Path) -> None:
    items = _items()
    source = tmp_path / "partial.jsonl"
    _write(source, [_row(items[0], model="other-model")])

    with pytest.raises(ValueError, match="caption_model_path"):
        load_validated_caption_prefix(source, items, model_path="model", max_new_tokens=384)


def test_caption_resume_rejects_revision_contract_drift(tmp_path: Path) -> None:
    items = _items()
    source = tmp_path / "partial.jsonl"
    row = _row(items[0])
    row["caption_model_revision"] = "other-revision"
    _write(source, [row])

    with pytest.raises(ValueError, match="caption_model_revision"):
        load_validated_caption_prefix(
            source,
            items,
            model_path="model",
            max_new_tokens=384,
            model_revision="revision",
            tensor_parallel_width=1,
        )
