#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.decon.core import read_jsonl
from src.decon.ocr_calibration import calibrate_ocr_pairs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--full-ocr-shards", type=Path, nargs="+", required=True)
    parser.add_argument("--transformed-ocr-shards", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite OCR calibration: {args.output}")
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    entries = [
        row
        for shard in [*args.full_ocr_shards, *args.transformed_ocr_shards]
        for row in read_jsonl(shard)
    ]
    result = calibrate_ocr_pairs(plan["pairs"], entries)
    result.update(
        {
            "plan": str(args.plan),
            "seed": plan["seed"],
            "model_revision": "rapidocr_onnxruntime==1.4.4 bundled PP-OCR models",
        }
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["ocr_char5_jaccard"], sort_keys=True))


if __name__ == "__main__":
    main()
