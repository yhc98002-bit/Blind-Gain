#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_filter_manifest(comparison: dict[str, Any]) -> dict[str, Any]:
    edges = comparison["candidate_edges"]
    remove_edges = [edge for edge in edges if edge["action"] == "remove"]
    inspect_edges = [edge for edge in edges if edge["action"] == "inspect"]
    remove_ids = sorted({edge["train_record_id"] for edge in remove_edges})
    inspect_only_ids = sorted({edge["train_record_id"] for edge in inspect_edges} - set(remove_ids))
    pending = list(comparison.get("pending_layers", []))
    return {
        "schema_version": "blind-gains.decon-filter-manifest.v1",
        "complete": not pending,
        "completed_layers": comparison.get("completed_layers", []),
        "pending_layers": pending,
        "thresholds": comparison["thresholds"],
        "auto_remove_rule": "drop a Geometry3K train record if any candidate edge has action=remove",
        "manual_review_rule": "inspect-only records are not auto-dropped because calibrated inspect thresholds admit false positives",
        "n_train_records": comparison["n_train_records"],
        "n_eval_records": comparison["n_eval_records"],
        "n_remove_edges": len(remove_edges),
        "n_inspect_edges": len(inspect_edges),
        "n_remove_train_records": len(remove_ids),
        "n_inspect_only_train_records": len(inspect_only_ids),
        "remove_train_record_ids": remove_ids,
        "inspect_only_train_record_ids": inspect_only_ids,
        "remove_edges_by_eval_dataset": dict(sorted(Counter(edge["eval_dataset"] for edge in remove_edges).items())),
        "remove_train_records_by_eval_dataset": {
            dataset: len({edge["train_record_id"] for edge in remove_edges if edge["eval_dataset"] == dataset})
            for dataset in sorted({edge["eval_dataset"] for edge in remove_edges})
        },
        "remove_eval_records_by_dataset": {
            dataset: len({edge["eval_record_id"] for edge in remove_edges if edge["eval_dataset"] == dataset})
            for dataset in sorted({edge["eval_dataset"] for edge in remove_edges})
        },
        "template_disjointness_rule": comparison["template_disjointness_rule"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite decontamination filter manifest: {args.output}")
    comparison = json.loads(args.comparison.read_text(encoding="utf-8"))
    result = build_filter_manifest(comparison)
    result["comparison_path"] = str(args.comparison)
    result["comparison_sha256"] = _sha256(args.comparison)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "complete": result["complete"],
                "n_remove_train_records": result["n_remove_train_records"],
                "n_inspect_only_train_records": result["n_inspect_only_train_records"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
