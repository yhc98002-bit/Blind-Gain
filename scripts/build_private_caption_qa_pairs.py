#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.build_caption_qa_pairs import _publish, _read_jsonl, partition_rows
from src.captioning.qa_pairs import build_private_caption_qa_rows


def build_summary(
    rows: list[dict[str, Any]],
    *,
    private_manifest: Path,
    caption_store: Path,
    num_shards: int,
    allow_extra_captions: bool,
) -> dict[str, Any]:
    template_counts: dict[str, int] = {}
    for row in rows:
        template = str(row["template_id"])
        template_counts[template] = template_counts.get(template, 0) + 1
    shards = partition_rows(rows, num_shards)
    return {
        "schema_version": "blind-gains.private-caption-qa-input-summary.v1",
        "n_pairs": len(rows),
        "n_images": len(rows) * 2,
        "n_shards": num_shards,
        "shard_pair_counts": [len(shard) for shard in shards],
        "template_counts": template_counts,
        "private_manifest": str(private_manifest),
        "caption_store": str(caption_store),
        "allow_extra_captions": allow_extra_captions,
        "scope": "internal-calibration-only",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-manifest", type=Path, required=True)
    parser.add_argument("--caption-store", type=Path, required=True)
    parser.add_argument("--output-pattern", required=True)
    parser.add_argument("--num-shards", type=int, default=1)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--allow-extra-captions", action="store_true")
    args = parser.parse_args()
    if "{index}" not in args.output_pattern:
        raise ValueError("--output-pattern must contain {index}")
    private_rows = _read_jsonl(args.private_manifest)
    rows = build_private_caption_qa_rows(
        private_rows,
        _read_jsonl(args.caption_store),
        allow_extra_captions=args.allow_extra_captions,
    )
    shards = partition_rows(rows, args.num_shards)
    outputs = [Path(args.output_pattern.format(index=index)) for index in range(args.num_shards)]
    if len(set(outputs)) != len(outputs):
        raise ValueError("output pattern produced duplicate paths")
    summary = build_summary(
        rows,
        private_manifest=args.private_manifest,
        caption_store=args.caption_store,
        num_shards=args.num_shards,
        allow_extra_captions=args.allow_extra_captions,
    )
    _publish(dict(zip(outputs, shards)), summary, args.summary)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
