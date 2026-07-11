#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.captioning.qa_pairs import build_caption_qa_rows


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def partition_rows(rows: list[dict[str, Any]], num_shards: int) -> list[list[dict[str, Any]]]:
    if num_shards < 1:
        raise ValueError("num_shards must be positive")
    return [rows[index::num_shards] for index in range(num_shards)]


def _publish(
    shards: dict[Path, list[dict[str, Any]]], summary: dict[str, Any], summary_path: Path
) -> None:
    final_paths = [*shards, summary_path]
    for final_path in final_paths:
        final_path.parent.mkdir(parents=True, exist_ok=True)
        if final_path.exists():
            raise FileExistsError(f"refusing to overwrite caption-QA artifact: {final_path}")
    partials = {final_path: Path(f"{final_path}.partial") for final_path in final_paths}
    for partial_path in partials.values():
        if partial_path.exists():
            raise FileExistsError(f"stale caption-QA partial requires inspection: {partial_path}")

    published: list[Path] = []
    try:
        for output, rows in shards.items():
            with partials[output].open("w", encoding="utf-8") as handle:
                for row in rows:
                    handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
        partials[summary_path].write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        for final_path in final_paths:
            os.replace(partials[final_path], final_path)
            published.append(final_path)
    except BaseException:
        for partial_path in partials.values():
            partial_path.unlink(missing_ok=True)
        for final_path in published:
            final_path.unlink(missing_ok=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-manifest", type=Path, required=True)
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument("--caption-store", type=Path, required=True)
    outputs = parser.add_mutually_exclusive_group(required=True)
    outputs.add_argument("--output", type=Path)
    outputs.add_argument("--output-pattern")
    parser.add_argument("--num-shards", type=int, default=1)
    parser.add_argument("--allow-extra-captions", action="store_true")
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    if args.num_shards < 1:
        raise ValueError("num_shards must be positive")
    if args.output is not None and args.num_shards != 1:
        raise ValueError("--output supports exactly one shard; use --output-pattern")
    if args.output_pattern is not None and "{index}" not in args.output_pattern:
        raise ValueError("--output-pattern must contain {index}")
    rows = build_caption_qa_rows(
        _read_jsonl(args.release_manifest),
        _read_jsonl(args.key_file),
        _read_jsonl(args.caption_store),
        args.release_manifest.parent,
        allow_extra_captions=args.allow_extra_captions,
    )
    template_counts: dict[str, int] = {}
    for row in rows:
        template = str(row["template_id"])
        template_counts[template] = template_counts.get(template, 0) + 1
    summary = {
        "schema_version": "blind-gains.fliptrack-caption-qa-input-summary.v1",
        "n_pairs": len(rows),
        "n_images": len(rows) * 2,
        "n_shards": args.num_shards,
        "shard_pair_counts": [len(shard) for shard in partition_rows(rows, args.num_shards)],
        "template_counts": template_counts,
        "release_manifest": str(args.release_manifest),
        "key_file": str(args.key_file),
        "caption_store": str(args.caption_store),
        "allow_extra_captions": args.allow_extra_captions,
    }
    partitioned = partition_rows(rows, args.num_shards)
    if args.output is not None:
        output_paths = [args.output]
    else:
        output_paths = [Path(args.output_pattern.format(index=index)) for index in range(args.num_shards)]
    if len(set(output_paths)) != len(output_paths):
        raise ValueError("output pattern produced duplicate paths")
    _publish(dict(zip(output_paths, partitioned)), summary, args.summary)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
