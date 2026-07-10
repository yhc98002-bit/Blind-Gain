#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.analysis.blind_solvability import real_blind_quadrants, summarize_condition
from src.eval.blind_solvability import CONDITIONS


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _parse_runs(values: list[str]) -> dict[str, Path]:
    runs: dict[str, Path] = {}
    for value in values:
        condition, separator, path = value.partition("=")
        if not separator or condition not in CONDITIONS or condition in runs:
            raise ValueError(f"invalid condition=run mapping: {value}")
        runs[condition] = Path(path)
    if set(runs) != set(CONDITIONS):
        raise ValueError(f"expected conditions {CONDITIONS}, found {sorted(runs)}")
    return runs


def build_summary(run_dirs: dict[str, Path], seed: int = 20260710) -> dict[str, Any]:
    rows_by_condition: dict[str, list[dict[str, Any]]] = {}
    manifests = {}
    for condition in CONDITIONS:
        run_dir = run_dirs[condition]
        manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
        if manifest.get("status") != "complete":
            raise ValueError(f"condition {condition} is not complete: {manifest.get('status')}")
        rows = _read_jsonl(run_dir / "per_item.jsonl")
        if any(row["condition"] != condition for row in rows):
            raise ValueError(f"condition mismatch in {run_dir}")
        rows_by_condition[condition] = rows
        manifests[condition] = {
            "run_dir": str(run_dir),
            "run_id": manifest["run_id"],
            "git_hash": manifest["git_hash"],
            "config_hash": manifest["config_hash"],
            "data_manifest_hash": manifest["data_manifest_hash"],
        }

    expected_keys = {
        (str(row["split"]), int(row["row_index"])) for row in rows_by_condition["real"]
    }
    for condition, rows in rows_by_condition.items():
        keys = {(str(row["split"]), int(row["row_index"])) for row in rows}
        if keys != expected_keys or len(rows) != len(keys):
            raise ValueError(f"condition {condition} does not have one row per registered item")

    aggregates = {}
    for condition, rows in rows_by_condition.items():
        aggregates[condition] = {
            "all": summarize_condition(rows, seed=seed),
            **{
                split: summarize_condition([row for row in rows if row["split"] == split], seed=seed + offset)
                for offset, split in enumerate(("train", "test"), start=100)
            },
        }
    quadrants = {}
    for condition in CONDITIONS:
        if condition == "real":
            continue
        quadrants[condition] = {
            "all": real_blind_quadrants(rows_by_condition["real"], rows_by_condition[condition]),
            **{
                split: real_blind_quadrants(
                    [row for row in rows_by_condition["real"] if row["split"] == split],
                    [row for row in rows_by_condition[condition] if row["split"] == split],
                )
                for split in ("train", "test")
            },
        }
    return {
        "schema_version": "blind-gains.blind-solvability-summary.v1",
        "n_items": len(expected_keys),
        "split_counts": {
            split: sum(row["split"] == split for row in rows_by_condition["real"])
            for split in ("train", "test")
        },
        "registered_sampling": {"group_size": 5, "sample_count": 16, "temperature": 1.0},
        "runs": manifests,
        "aggregates": aggregates,
        "real_blind_greedy_quadrants": quadrants,
    }


def _metric_cell(summary: dict[str, Any], condition: str, split: str, field: str) -> str:
    metric = summary["aggregates"][condition][split]["metrics"][field]
    return f"{metric['mean']:.4f} [{metric['ci_low']:.4f}, {metric['ci_high']:.4f}]"


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Geometry3K Blind-Solvability Audit",
        "",
        "Status:",
        f"- Complete over {summary['n_items']} Geometry3K train+test items under all five registered conditions.",
        "- Metrics use the canonical answer parser; intervals are 2,000-draw item-bootstrap 95% confidence intervals.",
        "",
        "Evidence:",
    ]
    for condition in CONDITIONS:
        lines.append(f"- {condition}: `{summary['runs'][condition]['run_dir']}`")
    lines.extend(
        [
            "",
            "Aggregate results:",
            "| Condition | Split | Greedy accuracy | Sample p | pass@G=5 | pass@K=16 | p in [0.2, 0.8] |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for condition in CONDITIONS:
        for split in ("all", "train", "test"):
            mid = summary["aggregates"][condition][split]["p_sample_midband_0p2_0p8"]
            lines.append(
                "| "
                + " | ".join(
                    [
                        condition,
                        split,
                        _metric_cell(summary, condition, split, "p_greedy"),
                        _metric_cell(summary, condition, split, "p_sample"),
                        _metric_cell(summary, condition, split, "pass_at_g"),
                        _metric_cell(summary, condition, split, "pass_at_k16"),
                        f"{mid['mean']:.4f} [{mid['ci_low']:.4f}, {mid['ci_high']:.4f}]",
                    ]
                )
                + " |"
            )
    lines.extend(["", "Greedy real-vs-blind quadrants:", "| Blind condition | Split | Both | Real only | Blind only | Neither |", "| --- | --- | ---: | ---: | ---: | ---: |"])
    for condition, splits in summary["real_blind_greedy_quadrants"].items():
        for split, counts in splits.items():
            lines.append(
                f"| {condition} | {split} | {counts['both_correct']} | {counts['real_only']} | "
                f"{counts['blind_only']} | {counts['neither_correct']} |"
            )
    lines.extend(
        [
            "",
            "Problems:",
            "- These are base-model dataset-property measurements, not training-arm outcomes.",
            "- Caption results use the frozen question-blind 3B caption store; they do not estimate arbitrary question-conditioned descriptions.",
            "",
            "Decision:",
            "- Use per-item blind p and the [0.2, 0.8] band to stratify later mechanical-pilot analysis.",
            "- Keep real, gray, noise, no-image, and caption results separate; do not collapse them into one generic blind score.",
            "",
            "Next actions:",
            "- Run the same registered harness on the stratified ViRL39K sample before the future scientific pilot.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="append", required=True, help="condition=run_directory")
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    for output in (args.json_output, args.markdown_output):
        if output.exists():
            raise FileExistsError(f"refusing to overwrite blind-solvability summary: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
    summary = build_summary(_parse_runs(args.run))
    args.json_output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(summary), encoding="utf-8")
    print(json.dumps({"n_items": summary["n_items"], "conditions": list(CONDITIONS)}, sort_keys=True))


if __name__ == "__main__":
    main()
