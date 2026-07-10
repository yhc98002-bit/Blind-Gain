#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.decon.core import read_jsonl
from src.decon.embedding_compare import load_embeddings, merge_embedding_signals, write_comparison


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--train-records", type=Path, required=True)
    parser.add_argument("--eval-records", type=Path, required=True)
    parser.add_argument("--image-embeddings", type=Path, required=True)
    parser.add_argument("--text-embeddings", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite embedding comparison: {args.output}")
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    result = merge_embedding_signals(
        baseline,
        read_jsonl(args.train_records),
        read_jsonl(args.eval_records),
        load_embeddings(args.image_embeddings),
        load_embeddings(args.text_embeddings),
    )
    write_comparison(result, args.output)
    print(json.dumps({key: result[key] for key in ("n_candidate_edges", "action_counts")}, sort_keys=True))


if __name__ == "__main__":
    main()
