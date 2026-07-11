#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image

from src.eval.image_grid_consistency import image_grid_contract


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_audit(data_path: Path) -> dict[str, Any]:
    rows = [json.loads(line) for line in data_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError("image-grid audit data is empty")
    records = []
    path_cache: dict[str, dict[str, object]] = {}
    for row in rows:
        images = row.get("images")
        if not isinstance(images, list) or not images:
            raise ValueError(f"row {row.get('row_index')} has no image path")
        for image_path in images:
            path = str(image_path)
            if path not in path_cache:
                with Image.open(path) as image:
                    width, height = image.size
                path_cache[path] = image_grid_contract(width, height)
            records.append(
                {
                    "row_index": int(row["row_index"]),
                    "image_path": path,
                    **path_cache[path],
                }
            )

    old_mismatches = [record for record in records if record["old_grid_mismatch"]]
    fixed_mismatches = [record for record in records if record["fixed_grid_mismatch"]]
    deltas = Counter(int(record["old_feature_delta"]) for record in old_mismatches)
    checks = {
        "all_rows_have_images": len(records) >= len(rows),
        "old_path_reproduces_grid_drift": bool(old_mismatches),
        "fixed_path_has_zero_grid_drift": not fixed_mismatches,
    }
    return {
        "schema_version": "blind-gains.easyr1-image-grid-audit.v1",
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "data_path": str(data_path),
        "data_sha256": _sha256(data_path),
        "parameters": {
            "easyr1_min_pixels": 262144,
            "easyr1_max_pixels": 4194304,
            "qwen_patch_size": 14,
            "qwen_merge_size": 2,
            "qwen_min_pixels": 3136,
            "qwen_max_pixels": 12845056,
        },
        "n_rows": len(rows),
        "n_images": len(records),
        "n_unique_image_paths": len(path_cache),
        "old_grid_mismatch_count": len(old_mismatches),
        "old_grid_mismatch_rate": len(old_mismatches) / len(records),
        "old_feature_delta_counts": {str(key): value for key, value in sorted(deltas.items())},
        "fixed_grid_mismatch_count": len(fixed_mismatches),
        "examples": old_mismatches[:20],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite image-grid audit: {args.output}")
    payload = build_audit(args.data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "old": payload["old_grid_mismatch_count"], "fixed": payload["fixed_grid_mismatch_count"]}, sort_keys=True))


if __name__ == "__main__":
    main()
