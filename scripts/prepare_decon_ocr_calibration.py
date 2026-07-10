#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from src.decon.calibration import select_distinct_negatives
from src.decon.core import read_jsonl, sha256_file, write_jsonl


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--transform-dir", type=Path, required=True)
    parser.add_argument("--plan-output", type=Path, required=True)
    parser.add_argument("--transform-records-output", type=Path, required=True)
    parser.add_argument("--sample-size", type=int, default=64)
    parser.add_argument("--seed", type=int, default=20260710)
    args = parser.parse_args()
    if args.plan_output.exists() or args.transform_records_output.exists():
        raise FileExistsError("refusing to overwrite OCR calibration plan")

    rows = read_jsonl(args.records)
    by_hash = {}
    for row in rows:
        by_hash.setdefault(row["image_sha256"], row)
    candidates = list(by_hash.values())
    selected = random.Random(args.seed).sample(candidates, min(args.sample_size, len(candidates)))
    negatives = select_distinct_negatives(selected, candidates, args.seed + 1)
    pairs = []
    transform_rows = []
    for index, (source, negative) in enumerate(zip(selected, negatives)):
        transformed = args.transform_dir / f"near_duplicate_{index:04d}.png"
        if not transformed.is_file():
            raise FileNotFoundError(transformed)
        transformed_hash = sha256_file(transformed)
        pairs.append(
            {
                "index": index,
                "source_record_id": source["record_id"],
                "source_image_sha256": source["image_sha256"],
                "source_image_path": source["image_path"],
                "transformed_image_sha256": transformed_hash,
                "transformed_image_path": str(transformed),
                "negative_record_id": negative["record_id"],
                "negative_image_sha256": negative["image_sha256"],
                "negative_image_path": negative["image_path"],
            }
        )
        transform_rows.append(
            {
                "record_id": f"ocr-calibration:transformed:{index}",
                "image_sha256": transformed_hash,
                "image_path": str(transformed),
                "image_applicable": True,
            }
        )
    args.plan_output.parent.mkdir(parents=True, exist_ok=True)
    args.plan_output.write_text(
        json.dumps(
            {
                "schema_version": "blind-gains.decon-ocr-calibration-plan.v1",
                "seed": args.seed,
                "sample_size": len(pairs),
                "source_records": str(args.records),
                "transform_dir": str(args.transform_dir),
                "pairs": pairs,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    write_jsonl(transform_rows, args.transform_records_output)
    print(json.dumps({"pairs": len(pairs), "transforms": len(transform_rows)}, sort_keys=True))


if __name__ == "__main__":
    main()
