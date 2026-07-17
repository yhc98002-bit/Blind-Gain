#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.eval.visual_evidence_ranking import (
    SCORER_VERSION,
    bootstrap_mean_ci,
    image_dependent_effect,
)


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_MODELS = {"base", "a1_step60", "a1_step100"}
EXPECTED_CONDITIONS = {"real", "no_image", "gray"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def aggregate_rows(rows: list[dict[str, Any]], n_boot: int, seed: int) -> dict[str, Any]:
    if not rows:
        raise ValueError("cannot aggregate an empty cell")
    margins = [float(row["paired_margin"]) for row in rows]
    top1 = [float(bool(row["candidate_pair_top1"])) for row in rows]
    success = [float(bool(row["pair_success"])) for row in rows]
    mrr = [float(row["candidate_pair_mrr"]) for row in rows]
    lower, upper = bootstrap_mean_ci(margins, n_boot=n_boot, seed=seed)
    return {
        "n_pairs": len(rows),
        "paired_margin_mean": sum(margins) / len(margins),
        "paired_margin_ci95": [lower, upper],
        "pair_success_rate": sum(success) / len(success),
        "candidate_pair_top1_rate": sum(top1) / len(top1),
        "candidate_pair_mrr_mean": sum(mrr) / len(mrr),
    }


def paired_metric_did(
    *,
    base_real: dict[str, dict[str, Any]],
    trained_real: dict[str, dict[str, Any]],
    base_blind: dict[str, dict[str, Any]],
    trained_blind: dict[str, dict[str, Any]],
    field: str,
) -> dict[str, float]:
    identities = set(base_real)
    if not identities or any(
        set(cell) != identities for cell in (trained_real, base_blind, trained_blind)
    ):
        raise ValueError("secondary effect cells have mismatched pair identities")
    return {
        pair_id: (float(trained_real[pair_id][field]) - float(base_real[pair_id][field]))
        - (float(trained_blind[pair_id][field]) - float(base_blind[pair_id][field]))
        for pair_id in identities
    }


def _effect_summary(values: dict[str, float], n_boot: int, seed: int) -> dict[str, Any]:
    ordered = [values[pair_id] for pair_id in sorted(values)]
    lower, upper = bootstrap_mean_ci(ordered, n_boot=n_boot, seed=seed)
    return {
        "n_pairs": len(ordered),
        "mean": sum(ordered) / len(ordered),
        "ci95": [lower, upper],
    }


def build_result(
    config: dict[str, Any],
    cell_rows: dict[tuple[str, str], list[dict[str, Any]]],
) -> dict[str, Any]:
    n_boot = int(config["analysis"]["bootstrap"]["resamples"])
    seed = int(config["analysis"]["bootstrap"]["seed"])
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    indexed: dict[tuple[str, str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    template_labels: dict[str, str] = {}
    for (model, condition), rows in cell_rows.items():
        for row in rows:
            template = str(row["template_id"])
            template_labels[template] = str(row["template_label"])
            grouped[(model, condition, template)].append(row)
            pair_id = str(row["pair_id"])
            if pair_id in indexed[(model, condition, template)]:
                raise ValueError(f"duplicate pair in result cell: {model}/{condition}/{pair_id}")
            indexed[(model, condition, template)][pair_id] = row

    cells: dict[str, Any] = {}
    for (model, condition, template), rows in sorted(grouped.items()):
        key = f"{model}|{condition}|{template}"
        cells[key] = {
            "model_key": model,
            "condition": condition,
            "template_id": template,
            "template_label": template_labels[template],
            **aggregate_rows(rows, n_boot=n_boot, seed=seed),
        }

    effects: dict[str, Any] = {}
    for trained_model in ("a1_step60", "a1_step100"):
        for blind in ("no_image", "gray"):
            for template in sorted(template_labels):
                base_real = indexed[("base", "real", template)]
                trained_real = indexed[(trained_model, "real", template)]
                base_blind = indexed[("base", blind, template)]
                trained_blind = indexed[(trained_model, blind, template)]
                margins = image_dependent_effect(
                    {key: float(row["paired_margin"]) for key, row in base_real.items()},
                    {key: float(row["paired_margin"]) for key, row in trained_real.items()},
                    {key: float(row["paired_margin"]) for key, row in base_blind.items()},
                    {key: float(row["paired_margin"]) for key, row in trained_blind.items()},
                )
                success = paired_metric_did(
                    base_real=base_real,
                    trained_real=trained_real,
                    base_blind=base_blind,
                    trained_blind=trained_blind,
                    field="pair_success",
                )
                top1 = paired_metric_did(
                    base_real=base_real,
                    trained_real=trained_real,
                    base_blind=base_blind,
                    trained_blind=trained_blind,
                    field="candidate_pair_top1",
                )
                mrr = paired_metric_did(
                    base_real=base_real,
                    trained_real=trained_real,
                    base_blind=base_blind,
                    trained_blind=trained_blind,
                    field="candidate_pair_mrr",
                )
                raw_sum = paired_metric_did(
                    base_real=base_real,
                    trained_real=trained_real,
                    base_blind=base_blind,
                    trained_blind=trained_blind,
                    field="raw_sum_paired_margin_robustness",
                )
                effect_key = f"{trained_model}|real_minus_{blind}|{template}"
                effects[effect_key] = {
                    "trained_model": trained_model,
                    "blind_comparator": blind,
                    "template_id": template,
                    "template_label": template_labels[template],
                    "paired_margin_primary": _effect_summary(margins, n_boot, seed),
                    "pair_success_secondary": _effect_summary(success, n_boot, seed),
                    "candidate_pair_top1_secondary": _effect_summary(top1, n_boot, seed),
                    "candidate_pair_mrr_secondary": _effect_summary(mrr, n_boot, seed),
                    "raw_sum_margin_robustness": _effect_summary(raw_sum, n_boot, seed),
                }

    primary_key = (
        "a1_step100|real_minus_no_image|"
        + str(config["analysis"]["primary_template"])
    )
    if primary_key not in effects:
        raise ValueError("registered primary effect is absent")
    return {
        "schema_version": "blind-gains.seed1-visual-evidence-ranking-results.v1",
        "status": "complete",
        "scope": config["scope"],
        "scorer_version": SCORER_VERSION,
        "primary_effect_key": primary_key,
        "primary_effect": effects[primary_key],
        "cells": cells,
        "effects": effects,
        "branch_assignment": None,
        "branch_assignment_reason": config["analysis"]["branch_reason"],
        "interpretation_contract": config["interpretation"],
    }


def render_markdown(result: dict[str, Any], provenance: dict[str, Any]) -> str:
    lines = [
        "# Seed-1 Visual-Evidence Ranking Results V1",
        "",
        "Status:",
        "- Complete as a post-seed-1 prospective diagnostic; it is not part of the original pilot preregistration.",
        "- No automatic B1/B2/B3 assignment is made because no margin-scale SESOI was registered.",
        "",
        "Evidence:",
        f"- Scorer: `{result['scorer_version']}`; complete immutable cells: `{len(provenance['runs'])}`.",
        "- Primary statistic is paired mean-token-log-probability margin; candidate top-1 and MRR are secondary.",
        "",
        "## Primary Geometry Effect",
        "",
        "| checkpoint | blind comparator | mean image-dependent paired-margin effect | 95% paired bootstrap CI | pairs |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    primary_template = result["primary_effect"]["template_id"]
    for key, effect in sorted(result["effects"].items()):
        if effect["template_id"] != primary_template:
            continue
        stat = effect["paired_margin_primary"]
        lines.append(
            f"| {effect['trained_model']} | {effect['blind_comparator']} | {stat['mean']:.6f} | "
            f"[{stat['ci95'][0]:.6f}, {stat['ci95'][1]:.6f}] | {stat['n_pairs']} |"
        )
    lines.extend(
        [
            "",
            "## Absolute Cell Summaries",
            "",
            "| checkpoint | condition | construct | paired margin | 95% CI | pair success | candidate top-1 | candidate MRR |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for cell in sorted(
        result["cells"].values(),
        key=lambda item: (item["model_key"], item["condition"], item["template_label"]),
    ):
        lines.append(
            f"| {cell['model_key']} | {cell['condition']} | {cell['template_label']} | "
            f"{cell['paired_margin_mean']:.6f} | [{cell['paired_margin_ci95'][0]:.6f}, {cell['paired_margin_ci95'][1]:.6f}] | "
            f"{cell['pair_success_rate']:.6f} | {cell['candidate_pair_top1_rate']:.6f} | "
            f"{cell['candidate_pair_mrr_mean']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## Per-Template Effects",
            "",
            "| checkpoint | comparator | construct | paired-margin effect | 95% CI | pair-success effect | top-1 effect | MRR effect | raw-sum robustness |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for effect in sorted(
        result["effects"].values(),
        key=lambda item: (item["trained_model"], item["blind_comparator"], item["template_label"]),
    ):
        margin = effect["paired_margin_primary"]
        success = effect["pair_success_secondary"]
        top1 = effect["candidate_pair_top1_secondary"]
        mrr = effect["candidate_pair_mrr_secondary"]
        raw_sum = effect["raw_sum_margin_robustness"]
        lines.append(
            f"| {effect['trained_model']} | {effect['blind_comparator']} | {effect['template_label']} | "
            f"{margin['mean']:.6f} | [{margin['ci95'][0]:.6f}, {margin['ci95'][1]:.6f}] | "
            f"{success['mean']:.6f} | {top1['mean']:.6f} | {mrr['mean']:.6f} | {raw_sum['mean']:.6f} |"
        )
    lines.extend(
        [
            "",
            "Problems:",
            "- Candidate-answer ranking is not a direct perception measure.",
            "- Rejecting a zero effect would show improved visual-evidence ranking under this frozen score, not establish an internal perceptual mechanism.",
            "- The R19 chart construct is `cued chart point-value reading` and remains secondary.",
            "",
            "Decision:",
            "- Publish estimates and intervals without automatic branch assignment or causal mechanism language.",
            "",
            "Next actions:",
            "- PIs compare the registered B1/B2/B3 descriptions to this diagnostic and the free-generation readout.",
            "- Multi-seed pilot results remain the required confirmation for the original pilot estimands.",
            "",
        ]
    )
    text = "\n".join(lines)
    if "perception improved" in text.lower():
        raise AssertionError("prohibited interpretation phrase entered the report")
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--run-dir", action="append", required=True)
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--markdown-output", required=True)
    parser.add_argument("--audit-output", required=True)
    args = parser.parse_args()
    output_paths = [Path(args.json_output), Path(args.markdown_output), Path(args.audit_output)]
    if any(path.exists() for path in output_paths):
        raise FileExistsError("refusing to overwrite ranking result artifacts")

    config_path = Path(args.config)
    config = _read_json(config_path)
    config_hash = _sha256(config_path)
    expected_data_hash = str(config["candidate_registry"]["sha256"])
    registry_path = Path(str(config["candidate_registry"]["path"]))
    registry_rows = _read_jsonl(registry_path)
    registry_by_pair = {str(row["pair_id"]): row for row in registry_rows}
    if len(registry_by_pair) != len(registry_rows):
        raise ValueError("frozen candidate registry has duplicate pair identities")
    expected_pair_ids = set(registry_by_pair)
    cell_rows: dict[tuple[str, str], list[dict[str, Any]]] = {}
    run_evidence: list[dict[str, Any]] = []
    checks: dict[str, bool] = {}
    for value in args.run_dir:
        run_dir = Path(value)
        manifest_path = run_dir / "run_manifest.json"
        output_path = run_dir / "scores.jsonl"
        manifest = _read_json(manifest_path)
        model = str(manifest["model_key"])
        condition = str(manifest["condition"])
        key = (model, condition)
        if key in cell_rows:
            raise ValueError(f"duplicate matrix cell: {key}")
        if manifest.get("status") != "complete" or manifest.get("exit_code") != 0:
            raise ValueError(f"run is not complete: {run_dir}")
        if manifest.get("limit") is not None:
            raise ValueError(f"limited smoke run cannot enter results: {run_dir}")
        if manifest.get("data_manifest_hash") != expected_data_hash:
            raise ValueError(f"candidate registry mismatch: {run_dir}")
        if manifest.get("config_hash") != config_hash:
            raise ValueError(f"config hash mismatch: {run_dir}")
        expected_model_hash = config["models"][model]["model_index_sha256"]
        if manifest.get("model_index_sha256") != expected_model_hash:
            raise ValueError(f"model hash mismatch: {run_dir}")
        if manifest.get("processor_artifact_sha256") != config["processor"]["artifact_sha256"]:
            raise ValueError(f"processor hash mismatch: {run_dir}")
        if manifest.get("prompt_contract_sha256") != config["prompt_contract"]["sha256"]:
            raise ValueError(f"prompt hash mismatch: {run_dir}")
        if manifest.get("scorer_version") != SCORER_VERSION:
            raise ValueError(f"scorer version mismatch: {run_dir}")
        rows = _read_jsonl(output_path)
        if len(rows) != int(config["candidate_registry"]["pair_count"]):
            raise ValueError(f"row count mismatch: {run_dir}")
        observed_ids = {str(row["pair_id"]) for row in rows}
        if len(observed_ids) != len(rows):
            raise ValueError(f"duplicate pair identities: {run_dir}")
        if observed_ids != expected_pair_ids:
            raise ValueError(f"pair identity set mismatch: {run_dir}")
        if any(row["model_key"] != model or row["condition"] != condition for row in rows):
            raise ValueError(f"row cell identity mismatch: {run_dir}")
        if any(
            row.get("candidate_set_sha256")
            != registry_by_pair[str(row["pair_id"])]["candidate_set_sha256"]
            for row in rows
        ):
            raise ValueError(f"candidate-set hash mismatch: {run_dir}")
        cell_rows[key] = rows
        run_evidence.append(
            {
                "run_dir": str(run_dir),
                "manifest_sha256": _sha256(manifest_path),
                "output_sha256": _sha256(output_path),
                "rows": len(rows),
                "model_key": model,
                "condition": condition,
            }
        )
    expected_cells = {(model, condition) for model in EXPECTED_MODELS for condition in EXPECTED_CONDITIONS}
    checks["exact_nine_cells"] = set(cell_rows) == expected_cells
    checks["all_cells_1200_rows"] = all(len(rows) == 1200 for rows in cell_rows.values())
    checks["scorer_version_exact"] = all(
        row.get("scorer_version") == SCORER_VERSION
        for rows in cell_rows.values()
        for row in rows
    )
    if not all(checks.values()):
        raise ValueError(f"matrix checks failed: {checks}")

    result = build_result(config, cell_rows)
    provenance = {
        "config": str(config_path),
        "config_sha256": config_hash,
        "runs": sorted(run_evidence, key=lambda item: (item["model_key"], item["condition"])),
    }
    result["provenance"] = provenance
    json_text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    markdown_text = render_markdown(result, provenance)
    for path in output_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
    Path(args.json_output).write_text(json_text, encoding="utf-8")
    Path(args.markdown_output).write_text(markdown_text, encoding="utf-8")
    audit = {
        "schema_version": "blind-gains.seed1-visual-evidence-ranking-audit.v1",
        "status": "pass",
        "checks": checks,
        "config_sha256": provenance["config_sha256"],
        "machine_output_sha256": _sha256(Path(args.json_output)),
        "markdown_output_sha256": _sha256(Path(args.markdown_output)),
        "performance_values_opened": True,
        "branch_assignment": None,
    }
    Path(args.audit_output).write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
