#!/usr/bin/env python3
"""Build the remaining-entity record file for resuming the quota-crashed ViRL39K OCR run.

Reads the exact same input record files as the crashed v2 extraction, replicates
extract_decon_ocr._entities() dedup/order semantics, subtracts entities already
completed in the v2 shards (validating shard integrity line by line), and writes
a records file that the unmodified extract_decon_ocr.py can consume.

A hash is treated as completed only when its v2 row parses as JSON and its
error field does not indicate the disk-quota failure that killed the run.
Truncated final lines (mid-write crash) are excluded from the done set.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def entities(paths: list[Path]) -> list[tuple[str, str]]:
    by_hash: dict[str, str] = {}
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get("image_applicable", True):
                    by_hash.setdefault(str(row["image_sha256"]), str(row["image_path"]))
    return sorted(by_hash.items())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, nargs="+", required=True)
    parser.add_argument("--prior-shards", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.summary.exists():
        raise FileExistsError("refusing to overwrite resume records or summary")

    all_entities = entities(args.inputs)
    done: set[str] = set()
    truncated_lines = 0
    quota_error_rows = 0
    ocr_failure_rows_kept = 0
    for shard in sorted(args.prior_shards):
        lines = shard.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                if index == len(lines) - 1:
                    truncated_lines += 1
                    continue
                raise ValueError(f"corrupt non-final line {index} in {shard}")
            error = row.get("error") or ""
            if "Errno 122" in error or "Disk quota" in error:
                quota_error_rows += 1
                continue
            if error:
                ocr_failure_rows_kept += 1
            done.add(str(row["image_sha256"]))

    remaining = [(h, p) for h, p in all_entities if h not in done]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for digest, image_path in remaining:
            handle.write(
                json.dumps(
                    {
                        "image_applicable": True,
                        "image_path": image_path,
                        "image_sha256": digest,
                        "schema_version": "blind-gains.decon-ocr-resume.v1",
                    },
                    sort_keys=True,
                )
                + "\n"
            )
    summary = {
        "inputs": [str(p) for p in args.inputs],
        "prior_shards": [str(p) for p in sorted(args.prior_shards)],
        "total_entities": len(all_entities),
        "completed_in_prior_shards": len(done),
        "remaining_entities": len(remaining),
        "truncated_final_lines_excluded": truncated_lines,
        "quota_error_rows_requeued": quota_error_rows,
        "genuine_ocr_failure_rows_kept_done": ocr_failure_rows_kept,
        "output": str(args.output),
    }
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
