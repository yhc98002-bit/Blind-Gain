from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "blind-gains.caption-store.v1"
CAPTION_PROMPT = (
    "Describe the image in one concise paragraph. Include visible text, labels, "
    "numbers, colors, shapes, counts, and spatial relations that could matter for answering questions."
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def discover_images(input_dir: str | Path) -> list[dict[str, Any]]:
    input_dir = Path(input_dir)
    by_hash: dict[str, list[Path]] = {}
    for path in sorted(item for item in input_dir.rglob("*") if item.is_file()):
        try:
            digest = sha256_file(path)
        except OSError:
            continue
        by_hash.setdefault(digest, []).append(path)
    return [
        {
            "image_sha256": digest,
            "image_path": str(paths[0]),
            "duplicate_paths": [str(path) for path in paths[1:]],
        }
        for digest, paths in sorted(by_hash.items())
    ]


def select_shard(items: list[dict[str, Any]], num_shards: int, shard_index: int) -> list[dict[str, Any]]:
    if num_shards < 1:
        raise ValueError("num_shards must be positive")
    if not 0 <= shard_index < num_shards:
        raise ValueError("shard_index must be in [0, num_shards)")
    return [item for index, item in enumerate(items) if index % num_shards == shard_index]
