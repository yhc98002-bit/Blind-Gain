#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.rewards.answer_reward import PARSER_VERSION


CELL_CONTRACTS = {
    "3b_real": ("3B", "real"),
    "3b_gray": ("3B", "gray"),
    "3b_noise": ("3B", "noise"),
    "3b_caption": ("3B", "caption"),
    "7b_real": ("7B", "real"),
    "7b_gray": ("7B", "gray"),
    "7b_noise": ("7B", "noise"),
    "7b_caption": ("7B", "caption"),
}
DEGRADATION_MODES = ("mild", "medium", "severe")
TEMPLATE_COUNTS = {
    "header_cued_table_code_v02": 300,
    "coordinate_register_twenty_point_x_v02": 600,
    "starred_series_value_nine_v07": 300,
}
TEMPLATE_LABELS = {
    "header_cued_table_code_v02": "document",
    "coordinate_register_twenty_point_x_v02": "geometry",
    "starred_series_value_nine_v07": "chart",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl_glob(run_dir: Path) -> list[dict[str, Any]]:
    paths = sorted((run_dir / "shards").glob("*.jsonl"))
    if not paths:
        raise ValueError(f"run has no JSONL shards: {run_dir}")
    rows = []
    for path in paths:
        rows.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    return rows


def _parse_mapping(values: list[str], expected: set[str]) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for value in values:
        key, separator, path = value.partition("=")
        if not separator or key not in expected or key in result:
            raise ValueError(f"invalid key=run mapping: {value}")
        result[key] = Path(path)
    if set(result) != expected:
        raise ValueError(f"expected mappings for {sorted(expected)}, found {sorted(result)}")
    return result


@dataclass(frozen=True)
class Cell:
    key: str
    aggregate_run: Path
    source_run: Path
    metrics: dict[str, Any]
    pair_ids: frozenset[str]
    template_by_pair: dict[str, str]
    hashes: dict[str, str]


def _validate_caption_chain(source_run: Path, expected_scale: str) -> dict[str, Any]:
    source_manifest = _read_json(source_run / "run_manifest.json")
    pair_shards = Path(str(source_manifest["data_manifest"]))
    pair_run = pair_shards.parent
    pair_manifest = _read_json(pair_run / "run_manifest.json")
    if pair_manifest.get("status") != "complete" or pair_manifest.get("job_type") != "p1_8_caption_qa_pair_adapter":
        raise ValueError(f"caption QA adapter contract failed: {pair_run}")
    caption_store = Path(str(pair_manifest["caption_store"]))
    store_summary = _read_json(caption_store.parent / "summary.json")
    expected_model_fragment = "3B" if expected_scale == "3B" else "7B"
    checks = {
        "coverage_complete": store_summary.get("coverage_complete") is True,
        "n_images": store_summary.get("n_images") == 2400,
        "max_new_tokens": store_summary.get("max_new_tokens") == 384,
        "model_scale": expected_model_fragment in str(store_summary.get("caption_model_path")),
        "prompt_hash": isinstance(store_summary.get("caption_prompt_sha256"), str)
        and len(store_summary["caption_prompt_sha256"]) == 64,
    }
    if not all(checks.values()):
        raise ValueError(f"caption store contract failed: {checks}")
    return {
        "pair_adapter_run": str(pair_run),
        "caption_store": str(caption_store),
        "caption_store_sha256": _sha256(caption_store),
        "caption_prompt_sha256": store_summary["caption_prompt_sha256"],
        "caption_model_path": store_summary["caption_model_path"],
        "max_new_tokens": 384,
    }


def load_cell(key: str, aggregate_run: Path) -> Cell:
    scale, mode = CELL_CONTRACTS.get(key, ("3B", key))
    aggregate_manifest = _read_json(aggregate_run / "run_manifest.json")
    if aggregate_manifest.get("status") != "complete" or aggregate_manifest.get("job_type") != "fliptrack_metric_aggregation":
        raise ValueError(f"aggregate run is not complete: {aggregate_run}")
    source_run = Path(str(aggregate_manifest["source_run"]))
    source_manifest_path = source_run / "run_manifest.json"
    source_manifest = _read_json(source_manifest_path)
    if source_manifest.get("status") != "complete":
        raise ValueError(f"source run is not complete: {source_run}")
    if source_manifest.get("max_new_tokens") != 32:
        raise ValueError(f"QA max_new_tokens drift in {source_run}")
    if source_manifest.get("decoding") != {"temperature": 0.0, "top_p": 1.0, "n": 1}:
        raise ValueError(f"QA decoding drift in {source_run}")
    model_path = str(source_manifest.get("model_path"))
    if scale not in model_path:
        raise ValueError(f"model scale mismatch for {key}: {model_path}")
    if mode == "caption":
        if source_manifest.get("job_type") != "fliptrack_v02_caption_only_qa":
            raise ValueError(f"caption cell uses the wrong source job: {source_run}")
        _validate_caption_chain(source_run, scale)
    else:
        if source_manifest.get("job_type") != "fliptrack_v02_image_evaluation":
            raise ValueError(f"image cell uses the wrong source job: {source_run}")
        if source_manifest.get("image_mode") != mode:
            raise ValueError(f"image mode mismatch for {key}: {source_run}")

    rows = _read_jsonl_glob(source_run)
    pair_ids = [str(row["pair_id"]) for row in rows]
    if len(pair_ids) != len(set(pair_ids)):
        raise ValueError(f"duplicate pair IDs in {source_run}")
    parser_versions = {str(row.get("parser_version")) for row in rows}
    if parser_versions != {PARSER_VERSION}:
        raise ValueError(f"parser version drift in {source_run}: {parser_versions}")
    metrics_path = aggregate_run / "metrics.json"
    metrics = _read_json(metrics_path)
    if int(metrics.get("n_pairs", -1)) != len(rows):
        raise ValueError(f"aggregate row count mismatch in {aggregate_run}")
    template_by_pair = {str(row["pair_id"]): str(row["template_id"]) for row in rows}
    return Cell(
        key=key,
        aggregate_run=aggregate_run,
        source_run=source_run,
        metrics=metrics,
        pair_ids=frozenset(pair_ids),
        template_by_pair=template_by_pair,
        hashes={
            "aggregate_manifest_sha256": _sha256(aggregate_run / "run_manifest.json"),
            "metrics_sha256": _sha256(metrics_path),
            "source_manifest_sha256": _sha256(source_manifest_path),
        },
    )


def template_criteria(
    template: str,
    cells: dict[str, dict[str, Any]],
    degradation: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    pair_accuracy = {
        key: float(metrics["per_template"][template]["pair_accuracy"])
        for key, metrics in cells.items()
    }
    degradation_values = {
        mode: float(metrics["per_template"][template]["pair_accuracy"])
        for mode, metrics in degradation.items()
    }
    curve = [
        pair_accuracy["3b_real"],
        degradation_values["mild"],
        degradation_values["medium"],
        degradation_values["severe"],
        pair_accuracy["3b_gray"],
    ]
    checks = {
        "3b_real_at_least_0_40": pair_accuracy["3b_real"] >= 0.40,
        "3b_real_at_most_0_90": pair_accuracy["3b_real"] <= 0.90,
        "3b_caption_at_most_0_15": pair_accuracy["3b_caption"] <= 0.15,
        "7b_caption_at_most_0_15": pair_accuracy["7b_caption"] <= 0.15,
        "3b_gray_at_most_0_05": pair_accuracy["3b_gray"] <= 0.05,
        "3b_noise_at_most_0_05": pair_accuracy["3b_noise"] <= 0.05,
        "7b_gray_at_most_0_05": pair_accuracy["7b_gray"] <= 0.05,
        "7b_noise_at_most_0_05": pair_accuracy["7b_noise"] <= 0.05,
        "real_accuracy_increases_3b_to_7b": pair_accuracy["7b_real"] > pair_accuracy["3b_real"],
        "3b_degradation_curve_nonincreasing": all(
            left >= right for left, right in zip(curve, curve[1:])
        ),
    }
    return {
        "label": TEMPLATE_LABELS[template],
        "checks": checks,
        "automated_outcome": (
            "generator-level-pass" if all(checks.values()) else "downgrade-to-R19-selected"
        ),
        "pair_accuracy": pair_accuracy,
        "degradation_curve": {
            "real": curve[0],
            "mild": curve[1],
            "medium": curve[2],
            "severe": curve[3],
            "gray": curve[4],
        },
    }


def _load_comparison(run_dir: Path) -> tuple[dict[str, Any], dict[str, str]]:
    manifest = _read_json(run_dir / "run_manifest.json")
    if manifest.get("status") != "complete" or manifest.get("job_type") != "fliptrack_paired_run_comparison":
        raise ValueError(f"comparison run is not complete: {run_dir}")
    path = run_dir / "comparison.json"
    payload = _read_json(path)
    if payload.get("n_pairs") != 1200 or payload.get("mcnemar", {}).get("n_common") != 1200.0:
        raise ValueError(f"comparison does not cover all R20 pairs: {run_dir}")
    return payload, {
        "run_manifest_sha256": _sha256(run_dir / "run_manifest.json"),
        "comparison_sha256": _sha256(path),
    }


def build_package(
    *,
    cell_runs: dict[str, Path],
    degradation_runs: dict[str, Path],
    real_comparison_run: Path,
    caption_comparison_run: Path,
    release_manifest: Path,
    lint_json: Path,
    attacker_json: Path,
) -> dict[str, Any]:
    release_rows = [json.loads(line) for line in release_manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    release_ids = {str(row["pair_id"]) for row in release_rows}
    release_templates = {str(row["pair_id"]): str(row["template_id"]) for row in release_rows}
    if len(release_rows) != 1200 or len(release_ids) != 1200:
        raise ValueError("R20 release manifest must contain 1,200 unique pairs")
    counts = {template: sum(value == template for value in release_templates.values()) for template in TEMPLATE_COUNTS}
    if counts != TEMPLATE_COUNTS:
        raise ValueError(f"R20 template counts drifted: {counts}")

    cells = {key: load_cell(key, run) for key, run in cell_runs.items()}
    degradation = {mode: load_cell(mode, run) for mode, run in degradation_runs.items()}
    for cell in (*cells.values(), *degradation.values()):
        if cell.pair_ids != release_ids or cell.template_by_pair != release_templates:
            raise ValueError(f"R20 row identity/metadata mismatch in {cell.source_run}")
    lint = _read_json(lint_json)
    attacker = _read_json(attacker_json)
    global_checks = {
        "release_linter": bool(lint.get("checks")) and all(lint["checks"].values()),
        "grouped_artifact_attackers": attacker.get("gate", {}).get("status") is True,
        "all_eight_hardness_cells_complete": len(cells) == 8,
        "all_three_degradation_cells_complete": len(degradation) == 3,
        "row_identity_equal_in_all_cells": True,
    }
    template_results = {
        template: template_criteria(
            template,
            {key: cell.metrics for key, cell in cells.items()},
            {key: cell.metrics for key, cell in degradation.items()},
        )
        for template in TEMPLATE_COUNTS
    }
    real_comparison, real_hashes = _load_comparison(real_comparison_run)
    caption_comparison, caption_hashes = _load_comparison(caption_comparison_run)
    for template in TEMPLATE_COUNTS:
        result = template_results[template]
        real = real_comparison["per_template"][template]
        caption = caption_comparison["per_template"][template]
        if not math.isclose(
            real["pair_accuracy_delta"],
            result["pair_accuracy"]["7b_real"] - result["pair_accuracy"]["3b_real"],
            abs_tol=1e-12,
        ) or not math.isclose(
            caption["pair_accuracy_delta"],
            result["pair_accuracy"]["7b_caption"] - result["pair_accuracy"]["3b_caption"],
            abs_tol=1e-12,
        ):
            raise ValueError(f"paired comparison disagrees with aggregate cells for {template}")
        result["paired_scale"] = {"real": real, "caption": caption}

    all_templates_pass = all(
        result["automated_outcome"] == "generator-level-pass"
        for result in template_results.values()
    )
    generator_level_outcome = (
        "generator-level-pass"
        if all(global_checks.values()) and all_templates_pass
        else "one-or-more-templates-downgraded-to-R19-selected"
    )
    return {
        "schema_version": "blind-gains.fliptrack-r20-confirmatory.v1",
        "status": "complete",
        "interpretation_rule": "R20 is confirmatory. A template failing here has its certification downgraded to R19-selected; we do not mint R21. Generator-level pass = R20 meets the pre-frozen criteria without selection.",
        "generator_level_outcome": generator_level_outcome,
        "global_checks": global_checks,
        "n_pairs": 1200,
        "template_counts": TEMPLATE_COUNTS,
        "template_results": template_results,
        "cells": {
            key: {
                "aggregate_run": str(cell.aggregate_run),
                "source_run": str(cell.source_run),
                "metrics": cell.metrics,
                "hashes": cell.hashes,
            }
            for key, cell in {**cells, **degradation}.items()
        },
        "paired_scale": {
            "real": real_comparison,
            "caption": caption_comparison,
            "real_hashes": real_hashes,
            "caption_hashes": caption_hashes,
        },
        "release_manifest": str(release_manifest),
        "release_manifest_sha256": _sha256(release_manifest),
        "lint_json": str(lint_json),
        "lint_sha256": _sha256(lint_json),
        "attacker_json": str(attacker_json),
        "attacker_sha256": _sha256(attacker_json),
        "human_contact_sheet_audit": "pending",
    }


def render_markdown(package: dict[str, Any], machine_json: Path) -> str:
    lines = [
        "# FlipTrack R20 Confirmatory Instrument",
        "",
        "Status:",
        "- The one-shot R20 pipeline is complete; this report records automated criterion outcomes and does not declare a PI gate passed.",
        f"- Generator-level automated outcome: `{package['generator_level_outcome']}`.",
        f"- Machine status JSON: `{machine_json}` (`status=complete`).",
        "- R20 contact-sheet human audit remains pending.",
        "",
        "Interpretation rule:",
        f"- {package['interpretation_rule']}",
        "",
        "Evidence:",
        f"- Release manifest: `{package['release_manifest']}`, SHA256 `{package['release_manifest_sha256']}`.",
        f"- Linter: `{package['lint_json']}`; grouped attackers: `{package['attacker_json']}`.",
        "- Every cell covers the same 1,200 opaque pair IDs: document 300, geometry 600, chart 300.",
        "- Caption stores are question-blind, greedy, fixed at 384 tokens; QA is greedy with 32 output tokens.",
        "",
        "Hardness cells:",
        "| Template | 3B real | 7B real | 3B gray | 7B gray | 3B noise | 7B noise | 3B caption | 7B caption | Outcome |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for template, result in package["template_results"].items():
        p = result["pair_accuracy"]
        lines.append(
            f"| {result['label']} | {p['3b_real']:.4f} | {p['7b_real']:.4f} | "
            f"{p['3b_gray']:.4f} | {p['7b_gray']:.4f} | {p['3b_noise']:.4f} | "
            f"{p['7b_noise']:.4f} | {p['3b_caption']:.4f} | {p['7b_caption']:.4f} | "
            f"{result['automated_outcome']} |"
        )
    lines.extend(
        [
            "",
            "3B degradation control:",
            "| Template | Real | Mild | Medium | Severe | Gray | Nonincreasing |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for result in package["template_results"].values():
        curve = result["degradation_curve"]
        lines.append(
            f"| {result['label']} | {curve['real']:.4f} | {curve['mild']:.4f} | "
            f"{curve['medium']:.4f} | {curve['severe']:.4f} | {curve['gray']:.4f} | "
            f"{str(result['checks']['3b_degradation_curve_nonincreasing']).lower()} |"
        )
    lines.extend(
        [
            "",
            "Problems:",
            "- Automated checks cannot establish legibility, naturalness, or semantic uniqueness; the second human contact-sheet audit is separate.",
            "- R20 is one-shot confirmatory evidence. No failed template is regenerated or replaced in this round.",
            "",
            "Decision:",
            "- Preserve the per-template automated outcomes exactly as reported. No R21 is authorized by this workflow.",
            "- Treat final human acceptance and any prelaunch gate decision as PI responsibilities.",
            "",
            "Next actions:",
            "- Complete the representative R20 human contact-sheet audit and record pair IDs for any semantic or legibility failures.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cell", action="append", required=True)
    parser.add_argument("--degradation", action="append", required=True)
    parser.add_argument("--real-comparison-run", type=Path, required=True)
    parser.add_argument("--caption-comparison-run", type=Path, required=True)
    parser.add_argument("--release-manifest", type=Path, required=True)
    parser.add_argument("--lint-json", type=Path, required=True)
    parser.add_argument("--attacker-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args()
    if args.output_json.exists() or args.output_markdown.exists():
        raise FileExistsError("refusing to overwrite R20 confirmatory outputs")
    package = build_package(
        cell_runs=_parse_mapping(args.cell, set(CELL_CONTRACTS)),
        degradation_runs=_parse_mapping(args.degradation, set(DEGRADATION_MODES)),
        real_comparison_run=args.real_comparison_run,
        caption_comparison_run=args.caption_comparison_run,
        release_manifest=args.release_manifest,
        lint_json=args.lint_json,
        attacker_json=args.attacker_json,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_markdown.write_text(render_markdown(package, args.output_json), encoding="utf-8")


if __name__ == "__main__":
    main()
