#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.decon.core import compare_hash_and_text, read_jsonl


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-records", type=Path, required=True)
    parser.add_argument("--eval-records", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite comparison: {args.output}")
    result = compare_hash_and_text(read_jsonl(args.train_records), read_jsonl(args.eval_records))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("n_candidate_edges", "action_counts")}, sort_keys=True))


if __name__ == "__main__":
    main()
