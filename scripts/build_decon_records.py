#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from src.decon.core import (
    enrich_records,
    load_geometry3k_records,
    load_layer1_records,
    sha256_file,
    write_jsonl,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--geometry-manifest", type=Path, required=True)
    parser.add_argument("--mmstar-tsv", type=Path, required=True)
    parser.add_argument("--mmstar-image-root", type=Path, required=True)
    parser.add_argument("--mathvista-tsv", type=Path, required=True)
    parser.add_argument("--blink-tsv", type=Path, required=True)
    parser.add_argument("--mmvp-tsv", type=Path)
    parser.add_argument("--hallusion-tsv", type=Path)
    parser.add_argument("--train-output", type=Path, required=True)
    parser.add_argument("--eval-output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    args = parser.parse_args()
    for output in (args.train_output, args.eval_output, args.summary_output):
        if output.exists():
            raise FileExistsError(f"refusing to overwrite decontamination artifact: {output}")

    train_rows = enrich_records(load_geometry3k_records(args.geometry_manifest, split="train"))
    eval_rows = enrich_records(
        load_layer1_records(
            args.mmstar_tsv,
            args.mmstar_image_root,
            args.mathvista_tsv,
            args.blink_tsv,
            mmvp_tsv=args.mmvp_tsv,
            hallusion_tsv=args.hallusion_tsv,
        )
    )
    write_jsonl(train_rows, args.train_output)
    write_jsonl(eval_rows, args.eval_output)
    summary = {
        "schema_version": "blind-gains.decon-record-summary.v1",
        "train_output": str(args.train_output),
        "train_sha256": sha256_file(args.train_output),
        "eval_output": str(args.eval_output),
        "eval_sha256": sha256_file(args.eval_output),
        "n_train_records": len(train_rows),
        "n_eval_records": len(eval_rows),
        "train_dataset_counts": dict(sorted(Counter(row["dataset"] for row in train_rows).items())),
        "eval_dataset_counts": dict(sorted(Counter(row["dataset"] for row in eval_rows).items())),
        "source_hashes": {
            str(path): sha256_file(path)
            for path in (
                args.geometry_manifest,
                args.mmstar_tsv,
                args.mathvista_tsv,
                args.blink_tsv,
                args.mmvp_tsv,
                args.hallusion_tsv,
            )
            if path is not None
        },
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"n_train_records": len(train_rows), "n_eval_records": len(eval_rows)}, sort_keys=True))


if __name__ == "__main__":
    main()
