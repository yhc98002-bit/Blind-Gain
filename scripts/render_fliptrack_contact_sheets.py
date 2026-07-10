#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.fliptrack.build_v02 import write_contact_sheets


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--n-per-template", type=int, default=20)
    args = parser.parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite contact sheets: {args.output_dir}")
    with args.manifest.open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    outputs = write_contact_sheets(rows, args.output_dir, n_per_template=args.n_per_template)
    print(json.dumps({"n_pairs": len(rows), "outputs": [str(path) for path in outputs]}, sort_keys=True))


if __name__ == "__main__":
    main()
