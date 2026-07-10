#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.eval.parser_agreement import agreement_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, nargs="+", required=True)
    parser.add_argument("--rows-output", type=Path, required=True)
    parser.add_argument("--metrics-output", type=Path, required=True)
    args = parser.parse_args()
    if args.rows_output.exists() or args.metrics_output.exists():
        raise FileExistsError("refusing to overwrite parser agreement outputs")

    from examples.reward_function.r1v import accuracy_reward

    generations = []
    for path in args.inputs:
        with path.open(encoding="utf-8") as handle:
            generations.extend(json.loads(line) for line in handle if line.strip())
    generations.sort(key=lambda row: int(row["source_row_index"]))
    rows, metrics = agreement_rows(generations, accuracy_reward)
    args.rows_output.parent.mkdir(parents=True, exist_ok=True)
    with args.rows_output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
    args.metrics_output.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(metrics, sort_keys=True))


if __name__ == "__main__":
    main()
