#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.data.virl39k_loader import load_rows
from src.data.virl39k_sample import build_manifest_rows, stratified_sample


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parquet", type=Path, required=True)
    parser.add_argument("--image-root", type=Path, required=True)
    parser.add_argument("--sample-size", type=int, default=4096)
    parser.add_argument("--seed", type=int, default=20260710)
    parser.add_argument("--manifest-output", type=Path, required=True)
    parser.add_argument("--stats-output", type=Path, required=True)
    parser.add_argument("--image-index-dir", type=Path, required=True)
    args = parser.parse_args()
    for path in (args.manifest_output, args.stats_output):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite ViRL39K sample artifact: {path}")
    rows = load_rows(args.parquet, args.image_root)
    selected = stratified_sample(rows, args.sample_size, args.seed)
    manifest_rows, stats = build_manifest_rows(selected, args.image_index_dir)
    stats.update(
        {
            "population_size": len(rows),
            "sample_seed": args.seed,
            "sampling_method": (
                "Hamilton proportional allocation over source, category, answer type, "
                "7B-base pass-rate bin, and image-count bucket; deterministic within-stratum shuffle"
            ),
        }
    )
    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    with args.manifest_output.open("w", encoding="utf-8") as handle:
        for row in manifest_rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
    args.stats_output.parent.mkdir(parents=True, exist_ok=True)
    args.stats_output.write_text(json.dumps(stats, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(stats, sort_keys=True))


if __name__ == "__main__":
    main()
