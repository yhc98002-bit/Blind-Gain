from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


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


def merge_caption_rows(
    shard_paths: Iterable[str | Path],
    expected_hashes: set[str] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_hash: dict[str, dict[str, Any]] = {}
    model_paths: set[str] = set()
    prompt_hashes: set[str] = set()
    token_budgets: set[int] = set()
    for shard_path in shard_paths:
        with Path(shard_path).open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                digest = str(row["image_sha256"])
                caption = str(row["caption"]).strip()
                if digest in by_hash and str(by_hash[digest]["caption"]).strip() != caption:
                    raise ValueError(f"conflicting captions for image hash {digest}")
                by_hash.setdefault(digest, row)
                model_paths.add(str(row["caption_model_path"]))
                prompt_hashes.add(str(row["caption_prompt_sha256"]))
                token_budgets.add(int(row["max_new_tokens"]))
    if not by_hash:
        raise ValueError("caption shards contain no rows")
    if len(model_paths) != 1 or len(prompt_hashes) != 1 or len(token_budgets) != 1:
        raise ValueError("caption shards mix model, prompt, or token-budget contracts")
    found = set(by_hash)
    missing = sorted((expected_hashes or set()) - found)
    extra = sorted(found - expected_hashes) if expected_hashes is not None else []
    if missing or extra:
        raise ValueError(f"caption hash coverage mismatch: missing={len(missing)} extra={len(extra)}")
    rows = [by_hash[digest] for digest in sorted(by_hash)]
    summary = {
        "schema_version": "blind-gains.caption-store-merge.v1",
        "n_images": len(rows),
        "caption_model_path": next(iter(model_paths)),
        "caption_prompt_sha256": next(iter(prompt_hashes)),
        "max_new_tokens": next(iter(token_budgets)),
        "expected_hashes": len(expected_hashes) if expected_hashes is not None else None,
        "coverage_complete": expected_hashes is None or found == expected_hashes,
    }
    return rows, summary
