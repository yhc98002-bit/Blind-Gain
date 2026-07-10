#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.decon.core import read_jsonl
from src.decon.embedding_compare import write_comparison
from src.decon.ocr import merge_ocr_signals


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--train-records", type=Path, required=True)
    parser.add_argument("--eval-records", type=Path, required=True)
    parser.add_argument("--ocr-shards", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite OCR comparison: {args.output}")
    entries = [row for shard in args.ocr_shards for row in read_jsonl(shard)]
    result = merge_ocr_signals(
        json.loads(args.baseline.read_text(encoding="utf-8")),
        read_jsonl(args.train_records),
        read_jsonl(args.eval_records),
        entries,
    )
    write_comparison(result, args.output)
    print(
        json.dumps(
            {
                "n_candidate_edges": result["n_candidate_edges"],
                "action_counts": result["action_counts"],
                "ocr_coverage": result["ocr_coverage"],
                "pending_layers": result["pending_layers"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
