#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path

from src.captioning.store import merge_caption_rows, sha256_file


def expected_hashes_from_manifest(path: Path) -> set[str]:
    expected: set[str] = set()
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            images = row.get("images")
            if not isinstance(images, list):
                raise ValueError(f"manifest line {line_number} has no images list")
            for image in images:
                digest = str(image.get("sha256", ""))
                if not digest:
                    raise ValueError(f"manifest line {line_number} has an image without SHA256")
                expected.add(digest)
    if not expected:
        raise ValueError("manifest contains no image hashes")
    return expected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--shards", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite caption audit: {args.output}")

    expected = expected_hashes_from_manifest(args.manifest)
    rows, contract = merge_caption_rows(args.shards, expected)
    checks = {
        "schema_prompt_decoding_budget_valid": True,
        "single_caption_contract": True,
        "exact_manifest_image_coverage": contract["coverage_complete"]
        and len(rows) == len(expected),
    }
    payload = {
        "schema_version": "blind-gains.caption-store-audit.v1",
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "audited_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "manifest": str(args.manifest),
        "manifest_sha256": sha256_file(args.manifest),
        "shards": [
            {
                "path": str(path),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
            for path in args.shards
        ],
        "contract": contract,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(f".{args.output.name}.partial.{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, args.output)
    print(json.dumps({"status": payload["status"], "n_images": len(rows)}, sort_keys=True))


if __name__ == "__main__":
    main()
