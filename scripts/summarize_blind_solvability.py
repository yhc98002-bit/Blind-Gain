#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from src.analysis.blind_solvability import real_blind_quadrants, summarize_condition
from src.eval.blind_solvability import CONDITIONS, score_item
from src.eval.prompt_contract import PromptContract, load_prompt_contract_from_run_manifest
from src.rewards.answer_reward import PARSER_VERSION


_SCORE_FIELDS = (
    "p_greedy",
    "greedy_correct",
    "greedy_extracted_answer",
    "greedy_format_valid",
    "greedy_extractor_valid",
    "greedy_contract_valid",
    "greedy_acc_strict",
    "sampled_extractor_valid",
    "sampled_contract_valid",
    "parser_version",
    "prompt_contract_id",
    "prompt_contract_sha256",
    "sample_count",
    "sample_correct_count",
    "sample_correct",
    "p_sample",
    "pass_at_g",
    "pass_at_k16",
    "variance_proxy",
)


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


def _item_contract(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "qid": row.get("qid"),
        "problem": row.get("problem"),
        "ground_truth": row.get("ground_truth"),
        "image_sha256": row.get("image_sha256"),
        "source_metadata": row.get("source_metadata"),
    }


def _values_match(actual: Any, expected: Any) -> bool:
    if isinstance(expected, float):
        return isinstance(actual, (int, float)) and math.isclose(
            float(actual), expected, rel_tol=1e-12, abs_tol=1e-12
        )
    return actual == expected


def _validate_scored_row(
    row: dict[str, Any],
    *,
    condition: str,
    group_size: int,
    sample_count: int,
    prompt_contract: PromptContract,
) -> None:
    key = (row.get("split"), row.get("row_index"))
    if row.get("schema_version") != "blind-gains.blind-solvability.v2":
        raise ValueError(f"unsupported row schema for {condition} at {key}")
    if row.get("condition") != condition:
        raise ValueError(f"condition mismatch for {condition} at {key}")
    sampled = row.get("sampled_responses")
    if not isinstance(sampled, list) or len(sampled) != sample_count:
        raise ValueError(f"sample count mismatch for {condition} at {key}")
    expected = score_item(
        str(row["ground_truth"]),
        str(row.get("greedy_response", "")),
        [str(response) for response in sampled],
        group_size,
        prompt_contract,
    )
    for field in _SCORE_FIELDS:
        if field not in row or not _values_match(row[field], expected[field]):
            raise ValueError(
                f"stored score mismatch for {condition} at {key}: field={field}, "
                f"stored={row.get(field)!r}, recomputed={expected[field]!r}"
            )


def _validate_decoding_contract(
    decoding: Any,
    *,
    condition: str,
    row_index: Any,
    sample_count: int,
    sample_temperature: float,
) -> None:
    expected_greedy = {"temperature": 0.0, "top_p": 1.0, "n": 1}
    expected_sampled = {
        "temperature": sample_temperature,
        "top_p": 1.0,
        "n": sample_count,
    }
    valid = bool(
        isinstance(decoding, dict)
        and decoding.get("greedy") == expected_greedy
        and decoding.get("sampled") == expected_sampled
        and isinstance(decoding.get("max_tokens"), int)
        and decoding["max_tokens"] > 0
        and isinstance(decoding.get("seed"), int)
    )
    if not valid:
        raise ValueError(
            f"unregistered decoding contract for {condition} at row {row_index}: {decoding!r}"
        )


def build_summary(
    run_dirs: dict[str, Path],
    seed: int = 20260710,
    dataset_name: str = "Geometry3K",
    splits: tuple[str, ...] = ("train", "test"),
) -> dict[str, Any]:
    if not splits or len(set(splits)) != len(splits):
        raise ValueError("splits must be a non-empty unique sequence")
    rows_by_condition: dict[str, list[dict[str, Any]]] = {}
    manifests = {}
    shared_manifest_contract: dict[str, Any] | None = None
    shared_decoding_contract: dict[str, Any] | None = None
    for condition in CONDITIONS:
        run_dir = run_dirs[condition]
        manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
        if manifest.get("status") != "complete":
            raise ValueError(f"condition {condition} is not complete: {manifest.get('status')}")
        prompt_contract = load_prompt_contract_from_run_manifest(run_dir / "run_manifest.json")
        manifest_contract = {
            "model_revision": manifest.get("model_revision"),
            "data_manifest": manifest.get("data_manifest"),
            "group_size": manifest.get("group_size"),
            "sample_count": manifest.get("sample_count"),
            "sample_temperature": manifest.get("sample_temperature"),
            "prompt_contract_sha256": prompt_contract.sha256,
            "parser_version": manifest.get("parser_version"),
        }
        if manifest.get("condition") != condition:
            raise ValueError(f"run manifest condition mismatch for {condition}")
        if shared_manifest_contract is None:
            shared_manifest_contract = manifest_contract
        elif manifest_contract != shared_manifest_contract:
            raise ValueError(
                f"run manifest contract mismatch for {condition}: "
                f"expected {shared_manifest_contract!r}, found {manifest_contract!r}"
            )
        try:
            group_size = int(manifest_contract["group_size"])
            sample_count = int(manifest_contract["sample_count"])
        except (TypeError, ValueError) as error:
            raise ValueError(f"missing sampling contract for {condition}") from error
        if group_size != 5 or sample_count != 16 or manifest_contract["sample_temperature"] != 1.0:
            raise ValueError(f"unregistered sampling contract for {condition}: {manifest_contract!r}")
        if manifest_contract["parser_version"] != PARSER_VERSION:
            raise ValueError(f"parser version mismatch for {condition}: {manifest_contract!r}")
        rows = _read_jsonl(run_dir / "per_item.jsonl")
        for row in rows:
            _validate_scored_row(
                row,
                condition=condition,
                group_size=group_size,
                sample_count=sample_count,
                prompt_contract=prompt_contract,
            )
            decoding = row.get("decoding")
            _validate_decoding_contract(
                decoding,
                condition=condition,
                row_index=row.get("row_index"),
                sample_count=sample_count,
                sample_temperature=float(manifest_contract["sample_temperature"]),
            )
            if shared_decoding_contract is None:
                shared_decoding_contract = decoding
            elif decoding != shared_decoding_contract:
                raise ValueError(
                    f"decoding contract mismatch for {condition} at row {row.get('row_index')}"
                )
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
    expected_items = {
        (str(row["split"]), int(row["row_index"])): _item_contract(row)
        for row in rows_by_condition["real"]
    }
    for condition, rows in rows_by_condition.items():
        keys = {(str(row["split"]), int(row["row_index"])) for row in rows}
        if keys != expected_keys or len(rows) != len(keys):
            raise ValueError(f"condition {condition} does not have one row per registered item")
        for row in rows:
            key = (str(row["split"]), int(row["row_index"]))
            if _item_contract(row) != expected_items[key]:
                raise ValueError(f"item contract mismatch for {condition} at {key}")

    aggregates = {}
    for condition, rows in rows_by_condition.items():
        aggregates[condition] = {
            "all": summarize_condition(rows, seed=seed),
            **{
                split: summarize_condition([row for row in rows if row["split"] == split], seed=seed + offset)
                for offset, split in enumerate(splits, start=100)
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
                for split in splits
            },
        }
    return {
        "schema_version": "blind-gains.blind-solvability-summary.v4",
        "dataset_name": dataset_name,
        "splits": list(splits),
        "n_items": len(expected_keys),
        "split_counts": {
            split: sum(row["split"] == split for row in rows_by_condition["real"])
            for split in splits
        },
        "evaluation_contract": {
            **(shared_manifest_contract or {}),
            "decoding": shared_decoding_contract,
        },
        "parser_version": PARSER_VERSION,
        "registered_sampling": {"group_size": 5, "sample_count": 16, "temperature": 1.0},
        "runs": manifests,
        "aggregates": aggregates,
        "real_blind_greedy_quadrants": quadrants,
    }


def _metric_cell(summary: dict[str, Any], condition: str, split: str, field: str) -> str:
    metric = summary["aggregates"][condition][split]["metrics"][field]
    return f"{metric['mean']:.4f} [{metric['ci_low']:.4f}, {metric['ci_high']:.4f}]"


def render_markdown(summary: dict[str, Any]) -> str:
    dataset_name = str(summary.get("dataset_name", "Geometry3K"))
    splits = tuple(summary.get("splits", ("train", "test")))
    lines = [
        f"# {dataset_name} Blind-Solvability Audit",
        "",
        "Status:",
        f"- Complete over {summary['n_items']} {dataset_name} items under all five registered conditions.",
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
        for split in ("all", *splits):
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
    lines.extend(
        [
            "",
            "Sample-p distribution over all items:",
            "| Condition | p=0 | 0<p<0.2 | 0.2<=p<=0.8 | 0.8<p<1 | p=1 |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    distribution_fields = ("zero", "low_0_0p2", "mid_0p2_0p8", "high_0p8_1", "one")
    for condition in CONDITIONS:
        distribution = summary["aggregates"][condition]["all"]["p_sample_distribution"]
        cells = [
            f"{distribution[field]['mean']:.4f} [{distribution[field]['ci_low']:.4f}, "
            f"{distribution[field]['ci_high']:.4f}]"
            for field in distribution_fields
        ]
        lines.append(f"| {condition} | " + " | ".join(cells) + " |")
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
            (
                "- Run the same registered harness on the stratified ViRL39K sample before the future scientific pilot."
                if dataset_name == "Geometry3K"
                else "- Use the registered ViRL39K sample results as a prerequisite input to the future scientific pilot."
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="append", required=True, help="condition=run_directory")
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--dataset-name", default="Geometry3K")
    parser.add_argument("--splits", nargs="+", default=["train", "test"])
    args = parser.parse_args()
    for output in (args.json_output, args.markdown_output):
        if output.exists():
            raise FileExistsError(f"refusing to overwrite blind-solvability summary: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
    summary = build_summary(
        _parse_runs(args.run),
        dataset_name=args.dataset_name,
        splits=tuple(args.splits),
    )
    args.json_output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(summary), encoding="utf-8")
    print(json.dumps({"n_items": summary["n_items"], "conditions": list(CONDITIONS)}, sort_keys=True))


if __name__ == "__main__":
    main()
