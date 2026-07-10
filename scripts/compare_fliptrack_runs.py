#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.eval.fliptrack_metrics import aggregate_pair_metrics, mcnemar_exact


def _index(rows: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        pair_id = str(row["pair_id"])
        if pair_id in indexed:
            raise ValueError(f"{label} contains duplicate pair_id: {pair_id}")
        indexed[pair_id] = row
    if not indexed:
        raise ValueError(f"{label} contains no rows")
    return indexed


def compare_rows(
    left_rows: list[dict[str, Any]],
    right_rows: list[dict[str, Any]],
    left_label: str,
    right_label: str,
) -> dict[str, Any]:
    left = _index(left_rows, left_label)
    right = _index(right_rows, right_label)
    if set(left) != set(right):
        raise ValueError(
            f"pair coverage mismatch: {left_label}={len(left)} {right_label}={len(right)} "
            f"left_only={len(set(left) - set(right))} right_only={len(set(right) - set(left))}"
        )
    pair_ids = sorted(left)
    for pair_id in pair_ids:
        if str(left[pair_id].get("template_id")) != str(right[pair_id].get("template_id")):
            raise ValueError(f"template mismatch for pair_id: {pair_id}")

    left_ordered = [left[pair_id] for pair_id in pair_ids]
    right_ordered = [right[pair_id] for pair_id in pair_ids]
    left_metrics = aggregate_pair_metrics(left_ordered)
    right_metrics = aggregate_pair_metrics(right_ordered)
    result: dict[str, Any] = {
        "schema_version": "blind-gains.fliptrack-paired-comparison.v1",
        "left_label": left_label,
        "right_label": right_label,
        "n_pairs": len(pair_ids),
        "left_pair_accuracy": left_metrics["pair_accuracy"],
        "right_pair_accuracy": right_metrics["pair_accuracy"],
        "pair_accuracy_delta": right_metrics["pair_accuracy"] - left_metrics["pair_accuracy"],
        "mcnemar": mcnemar_exact(left_ordered, right_ordered),
        "per_template": {},
    }
    templates = sorted({str(row.get("template_id")) for row in left_ordered})
    for template in templates:
        template_ids = [
            pair_id for pair_id in pair_ids if str(left[pair_id].get("template_id")) == template
        ]
        left_template = [left[pair_id] for pair_id in template_ids]
        right_template = [right[pair_id] for pair_id in template_ids]
        left_template_metrics = aggregate_pair_metrics(left_template)
        right_template_metrics = aggregate_pair_metrics(right_template)
        result["per_template"][template] = {
            "n_pairs": len(template_ids),
            "left_pair_accuracy": left_template_metrics["pair_accuracy"],
            "right_pair_accuracy": right_template_metrics["pair_accuracy"],
            "pair_accuracy_delta": right_template_metrics["pair_accuracy"]
            - left_template_metrics["pair_accuracy"],
            "mcnemar": mcnemar_exact(left_template, right_template),
        }
    return result


def _load(patterns: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    paths: list[str] = []
    for pattern in patterns:
        for path in sorted(Path().glob(pattern)):
            paths.append(str(path))
            with path.open(encoding="utf-8") as handle:
                rows.extend(json.loads(line) for line in handle if line.strip())
    return rows, paths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--left", nargs="+", required=True)
    parser.add_argument("--right", nargs="+", required=True)
    parser.add_argument("--left-label", required=True)
    parser.add_argument("--right-label", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    left_rows, left_paths = _load(args.left)
    right_rows, right_paths = _load(args.right)
    result = compare_rows(left_rows, right_rows, args.left_label, args.right_label)
    result["left_inputs"] = left_paths
    result["right_inputs"] = right_paths

    args.output.parent.mkdir(parents=True, exist_ok=True)
    partial = Path(f"{args.output}.partial")
    if args.output.exists() or partial.exists():
        raise FileExistsError(f"refusing to overwrite paired comparison: {args.output}")
    partial.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(partial, args.output)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
