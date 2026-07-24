#!/usr/bin/env python3
"""Fail-closed finalizer for the registered blind-arm margin calibration.

Implements docs/registered_blindarm_margin_calibration_v1.md: verifies the nine
calibration cells and the nine frozen seed-1 cells, computes the registered
real-input paired-margin effects against the frozen base (with the seed-1
paired bootstrap), the blind-condition integrity controls, the secondary
estimators, and the calibration-specific entropy / top1-minus-top2 statistics,
then applies the registered interpretation rule verbatim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.eval.visual_evidence_ranking import SCORER_VERSION, bootstrap_mean_ci

CAL_MODELS = ("a2_step100", "a2b_step100", "a3_step100")
SEED1_MODELS = ("base", "a1_step60", "a1_step100")
CONDITIONS = ("real", "gray", "no_image")
BLIND_CONDITIONS = ("gray", "no_image")
EFFECT_MODELS = ("a1_step60", "a1_step100", "a2_step100", "a2b_step100", "a3_step100")
SECONDARY_FIELDS = (
    "pair_success",
    "candidate_pair_top1",
    "candidate_pair_mrr",
    "raw_sum_paired_margin_robustness",
)
BLIND_MARGIN_TOLERANCE = 1e-9


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def verify_cell(
    run_dir: Path,
    *,
    config: dict[str, Any],
    config_hash: str,
    registry_by_pair: dict[str, dict[str, Any]],
    expected_pair_ids: set[str],
) -> tuple[str, str, list[dict[str, Any]], dict[str, Any]]:
    manifest_path = run_dir / "run_manifest.json"
    output_path = run_dir / "scores.jsonl"
    manifest = _read_json(manifest_path)
    model = str(manifest["model_key"])
    condition = str(manifest["condition"])
    if manifest.get("status") != "complete" or manifest.get("exit_code") != 0:
        raise ValueError(f"run is not complete: {run_dir}")
    if manifest.get("limit") is not None:
        raise ValueError(f"limited smoke run cannot enter results: {run_dir}")
    if manifest.get("data_manifest_hash") != str(config["candidate_registry"]["sha256"]):
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
    if any(row.get("scorer_version") != SCORER_VERSION for row in rows):
        raise ValueError(f"row scorer version mismatch: {run_dir}")
    evidence = {
        "run_dir": str(run_dir),
        "manifest_sha256": _sha256(manifest_path),
        "output_sha256": _sha256(output_path),
        "rows": len(rows),
        "model_key": model,
        "condition": condition,
    }
    return model, condition, rows, evidence


def row_entropy_and_gap(row: dict[str, Any]) -> tuple[float, float]:
    entropies: list[float] = []
    gaps: list[float] = []
    for side in ("a", "b"):
        scores = [float(value) for value in row[f"candidate_scores_{side}"]]
        if len(scores) < 2:
            raise ValueError(f"candidate set too small in pair {row['pair_id']}")
        peak = max(scores)
        exps = [math.exp(score - peak) for score in scores]
        total = sum(exps)
        probs = [value / total for value in exps]
        entropy = -sum(p * math.log(p) for p in probs if p > 0.0)
        entropies.append(entropy / math.log(len(scores)))
        ordered = sorted(scores, reverse=True)
        gaps.append(ordered[0] - ordered[1])
    return (
        sum(entropies) / len(entropies),
        sum(gaps) / len(gaps),
    )


def summarize(values: list[float], n_boot: int, seed: int) -> dict[str, Any]:
    lower, upper = bootstrap_mean_ci(values, n_boot=n_boot, seed=seed)
    return {
        "n_pairs": len(values),
        "mean": sum(values) / len(values),
        "ci95": [lower, upper],
    }


def intervals_overlap(a: list[float], b: list[float]) -> bool:
    return a[0] <= b[1] and b[0] <= a[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--calibration-config", required=True)
    parser.add_argument("--seed1-config", required=True)
    parser.add_argument("--calibration-run-dir", action="append", required=True)
    parser.add_argument("--seed1-run-dir", action="append", required=True)
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--markdown-output", required=True)
    parser.add_argument("--audit-output", required=True)
    args = parser.parse_args()
    output_paths = [Path(args.json_output), Path(args.markdown_output), Path(args.audit_output)]
    if any(path.exists() for path in output_paths):
        raise FileExistsError("refusing to overwrite calibration result artifacts")

    cal_config_path = Path(args.calibration_config)
    seed1_config_path = Path(args.seed1_config)
    cal_config = _read_json(cal_config_path)
    seed1_config = _read_json(seed1_config_path)
    cal_config_hash = _sha256(cal_config_path)
    seed1_config_hash = _sha256(seed1_config_path)

    for field, extract in (
        ("candidate_registry.sha256", lambda c: c["candidate_registry"]["sha256"]),
        ("candidate_registry.path", lambda c: c["candidate_registry"]["path"]),
        ("candidate_registry.pair_count", lambda c: c["candidate_registry"]["pair_count"]),
        ("processor.artifact_sha256", lambda c: c["processor"]["artifact_sha256"]),
        ("prompt_contract.sha256", lambda c: c["prompt_contract"]["sha256"]),
        ("analysis.bootstrap.resamples", lambda c: c["analysis"]["bootstrap"]["resamples"]),
        ("analysis.bootstrap.seed", lambda c: c["analysis"]["bootstrap"]["seed"]),
        ("analysis.primary_template", lambda c: c["analysis"]["primary_template"]),
    ):
        if extract(cal_config) != extract(seed1_config):
            raise ValueError(f"frozen input diverges between configurations: {field}")

    registry_path = Path(str(cal_config["candidate_registry"]["path"]))
    if _sha256(registry_path) != str(cal_config["candidate_registry"]["sha256"]):
        raise ValueError("frozen candidate registry hash mismatch on disk")
    registry_rows = _read_jsonl(registry_path)
    registry_by_pair = {str(row["pair_id"]): row for row in registry_rows}
    if len(registry_by_pair) != len(registry_rows):
        raise ValueError("frozen candidate registry has duplicate pair identities")
    expected_pair_ids = set(registry_by_pair)

    cell_rows: dict[tuple[str, str], list[dict[str, Any]]] = {}
    run_evidence: list[dict[str, Any]] = []
    for value, config, config_hash in (
        [(item, cal_config, cal_config_hash) for item in args.calibration_run_dir]
        + [(item, seed1_config, seed1_config_hash) for item in args.seed1_run_dir]
    ):
        model, condition, rows, evidence = verify_cell(
            Path(value),
            config=config,
            config_hash=config_hash,
            registry_by_pair=registry_by_pair,
            expected_pair_ids=expected_pair_ids,
        )
        key = (model, condition)
        if key in cell_rows:
            raise ValueError(f"duplicate matrix cell: {key}")
        cell_rows[key] = rows
        run_evidence.append(evidence)

    expected_cells = {
        (model, condition)
        for model in CAL_MODELS + SEED1_MODELS
        for condition in CONDITIONS
    }
    if set(cell_rows) != expected_cells:
        raise ValueError(f"cell matrix incomplete: {sorted(set(cell_rows))}")

    n_boot = int(cal_config["analysis"]["bootstrap"]["resamples"])
    boot_seed = int(cal_config["analysis"]["bootstrap"]["seed"])
    primary_template = str(cal_config["analysis"]["primary_template"])

    indexed: dict[tuple[str, str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    template_labels: dict[str, str] = {}
    for (model, condition), rows in cell_rows.items():
        for row in rows:
            template = str(row["template_id"])
            template_labels[template] = str(row["template_label"])
            pair_id = str(row["pair_id"])
            if pair_id in indexed[(model, condition, template)]:
                raise ValueError(f"duplicate pair in cell: {model}/{condition}/{pair_id}")
            indexed[(model, condition, template)][pair_id] = row
    templates = sorted(template_labels)
    if primary_template not in template_labels:
        raise ValueError("registered primary template absent from scores")

    cells: dict[str, Any] = {}
    integrity: dict[str, Any] = {}
    integrity_violations: list[str] = []
    for (model, condition, template), rows_by_pair in sorted(indexed.items()):
        rows = list(rows_by_pair.values())
        margins = [float(row["paired_margin"]) for row in rows]
        entropy_gap = [row_entropy_and_gap(row) for row in rows]
        key = f"{model}|{condition}|{template}"
        cells[key] = {
            "model_key": model,
            "condition": condition,
            "template_id": template,
            "template_label": template_labels[template],
            "n_pairs": len(rows),
            "paired_margin_mean": sum(margins) / len(margins),
            "paired_margin_ci95": list(
                bootstrap_mean_ci(margins, n_boot=n_boot, seed=boot_seed)
            ),
            "pair_success_rate": sum(float(bool(r["pair_success"])) for r in rows) / len(rows),
            "candidate_pair_top1_rate": sum(
                float(bool(r["candidate_pair_top1"])) for r in rows
            ) / len(rows),
            "candidate_pair_mrr_mean": sum(
                float(r["candidate_pair_mrr"]) for r in rows
            ) / len(rows),
            "normalized_entropy_mean": sum(e for e, _ in entropy_gap) / len(rows),
            "top1_minus_top2_gap_mean": sum(g for _, g in entropy_gap) / len(rows),
        }
        if condition in BLIND_CONDITIONS:
            max_abs = max(abs(value) for value in margins)
            integrity[key] = {
                "paired_margin_mean": cells[key]["paired_margin_mean"],
                "max_abs_paired_margin": max_abs,
                "structurally_zero": max_abs <= BLIND_MARGIN_TOLERANCE,
            }
            if max_abs > BLIND_MARGIN_TOLERANCE:
                integrity_violations.append(key)

    if integrity_violations:
        raise ValueError(
            "blind-condition margins are not structurally zero (broken cells): "
            + ", ".join(sorted(integrity_violations))
        )

    effects: dict[str, Any] = {}
    for model in EFFECT_MODELS:
        for template in templates:
            base_cell = indexed[("base", "real", template)]
            model_cell = indexed[(model, "real", template)]
            if set(base_cell) != set(model_cell):
                raise ValueError(f"pair identity mismatch in effect: {model}/{template}")
            ordered_ids = sorted(base_cell)
            margin_diffs = [
                float(model_cell[p]["paired_margin"]) - float(base_cell[p]["paired_margin"])
                for p in ordered_ids
            ]
            entry: dict[str, Any] = {
                "model_key": model,
                "template_id": template,
                "template_label": template_labels[template],
                "real_margin_effect": summarize(margin_diffs, n_boot, boot_seed),
            }
            for field in SECONDARY_FIELDS:
                diffs = [
                    float(model_cell[p][field]) - float(base_cell[p][field])
                    for p in ordered_ids
                ]
                entry[f"{field}_effect"] = summarize(diffs, n_boot, boot_seed)
            effects[f"{model}|real_vs_base|{template}"] = entry

    a1_primary = effects[f"a1_step100|real_vs_base|{primary_template}"]["real_margin_effect"]
    rule_details: dict[str, Any] = {}
    any_overlap = False
    for model in CAL_MODELS:
        model_effect = effects[f"{model}|real_vs_base|{primary_template}"]["real_margin_effect"]
        overlap = intervals_overlap(model_effect["ci95"], a1_primary["ci95"])
        below_half = model_effect["mean"] < 0.5 * a1_primary["mean"]
        rule_details[model] = {
            "real_margin_effect_mean": model_effect["mean"],
            "real_margin_effect_ci95": model_effect["ci95"],
            "below_half_of_a1_point": below_half,
            "ci_overlaps_a1": overlap,
            "supports_image_specific": below_half and not overlap,
        }
        any_overlap = any_overlap or overlap
    if any_overlap:
        verdict = "generic_confidence_sharpening_not_excluded"
        verdict_text = (
            "At least one blind arm's real-input margin effect is comparable to the"
            " A1 step-100 effect (overlapping 95% CIs); the seed-1 margin"
            " observation must be described as generic confidence sharpening"
            " pending further evidence."
        )
    elif all(detail["supports_image_specific"] for detail in rule_details.values()):
        verdict = "margin_inflation_specific_to_real_image_training"
        verdict_text = (
            "All blind arms' real-input margin effects are below half of the A1"
            " step-100 effect with non-overlapping 95% CIs; the calibration"
            " supports margin inflation being specific to real-image training."
        )
    else:
        verdict = "intermediate_pattern"
        verdict_text = (
            "Blind-arm effects neither overlap the A1 effect nor all fall below"
            " half of it; the registered rule assigns no clean label and the"
            " pattern is reported descriptively."
        )

    a1_did_published = None
    seed1_results_path = Path("reports/seed1_visual_evidence_ranking_results_v1.json")
    if seed1_results_path.is_file():
        seed1_results = _read_json(seed1_results_path)
        a1_did_published = seed1_results.get("primary_effect", {}).get(
            "paired_margin_primary"
        )

    result = {
        "schema_version": "blind-gains.blindarm-margin-calibration-results.v1",
        "status": "complete",
        "scope": cal_config.get("scope"),
        "scorer_version": SCORER_VERSION,
        "registration": "docs/registered_blindarm_margin_calibration_v1.md",
        "primary_template": primary_template,
        "a1_step100_reference_effect": a1_primary,
        "a1_step100_published_seed1_did": a1_did_published,
        "registered_rule_details": rule_details,
        "calibration_verdict": verdict,
        "calibration_verdict_text": verdict_text,
        "integrity_controls": integrity,
        "cells": cells,
        "effects": effects,
        "provenance": {
            "calibration_config": str(cal_config_path),
            "calibration_config_sha256": cal_config_hash,
            "seed1_config": str(seed1_config_path),
            "seed1_config_sha256": seed1_config_hash,
            "candidate_registry_sha256": str(cal_config["candidate_registry"]["sha256"]),
            "runs": sorted(
                run_evidence, key=lambda item: (item["model_key"], item["condition"])
            ),
        },
    }

    lines = [
        "# Blind-arm margin calibration results (v1)",
        "",
        "Registered: `docs/registered_blindarm_margin_calibration_v1.md`."
        " Inference-only calibration of the seed-1 visual-evidence ranking margin"
        " against blind-trained seed-1 checkpoints. Terminology: visual-evidence"
        " ranking / candidate-answer ranking.",
        "",
        f"- Scorer: `{SCORER_VERSION}`",
        f"- Primary template: `{primary_template}`",
        f"- Bootstrap: {n_boot} resamples, seed {boot_seed}, paired over FlipTrack pairs",
        "",
        "## Registered verdict",
        "",
        f"**{verdict}** — {verdict_text}",
        "",
        "## Real-input paired-margin effects vs frozen base (primary template)",
        "",
        "| model | mean | 95% CI | below half of A1 | CI overlaps A1 |",
        "|---|---|---|---|---|",
    ]
    a1_row = (
        f"| a1_step100 (reference) | {a1_primary['mean']:+.4f} |"
        f" [{a1_primary['ci95'][0]:+.4f}, {a1_primary['ci95'][1]:+.4f}] | — | — |"
    )
    lines.append(a1_row)
    for model in CAL_MODELS:
        detail = rule_details[model]
        lines.append(
            f"| {model} | {detail['real_margin_effect_mean']:+.4f} |"
            f" [{detail['real_margin_effect_ci95'][0]:+.4f},"
            f" {detail['real_margin_effect_ci95'][1]:+.4f}] |"
            f" {detail['below_half_of_a1_point']} | {detail['ci_overlaps_a1']} |"
        )
    lines += [
        "",
        "A1 step-100 seed-1 published DiD (real minus no-image, identical up to the"
        " structurally-zero blind margins): "
        + (
            f"{a1_did_published['mean']:+.4f} [{a1_did_published['ci95'][0]:+.4f},"
            f" {a1_did_published['ci95'][1]:+.4f}]"
            if a1_did_published
            else "unavailable"
        ),
        "",
        "## Integrity controls (blind-condition margins, must be structurally zero)",
        "",
        "| cell | mean margin | max abs margin | structurally zero |",
        "|---|---|---|---|",
    ]
    for key in sorted(integrity):
        control = integrity[key]
        lines.append(
            f"| {key} | {control['paired_margin_mean']:.2e} |"
            f" {control['max_abs_paired_margin']:.2e} | {control['structurally_zero']} |"
        )
    lines += [
        "",
        "## Condition-independent sharpening statistics (all cells, all templates)",
        "",
        "| cell | n | margin mean | pair success | top-1 | MRR | norm. entropy | top1−top2 gap |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for key in sorted(cells):
        cell = cells[key]
        lines.append(
            f"| {key} | {cell['n_pairs']} | {cell['paired_margin_mean']:+.4f} |"
            f" {cell['pair_success_rate']:.4f} | {cell['candidate_pair_top1_rate']:.4f} |"
            f" {cell['candidate_pair_mrr_mean']:.4f} |"
            f" {cell['normalized_entropy_mean']:.4f} |"
            f" {cell['top1_minus_top2_gap_mean']:.4f} |"
        )
    lines += [
        "",
        "## Secondary real-vs-base effects (all templates)",
        "",
        "| effect | margin | pair success | top-1 | MRR | raw-sum robustness |",
        "|---|---|---|---|---|---|",
    ]
    for key in sorted(effects):
        entry = effects[key]
        lines.append(
            f"| {key} | {entry['real_margin_effect']['mean']:+.4f} |"
            f" {entry['pair_success_effect']['mean']:+.4f} |"
            f" {entry['candidate_pair_top1_effect']['mean']:+.4f} |"
            f" {entry['candidate_pair_mrr_effect']['mean']:+.4f} |"
            f" {entry['raw_sum_paired_margin_robustness_effect']['mean']:+.4f} |"
        )
    lines += [
        "",
        "No margin-scale SESOI was registered; this calibration is descriptive and"
        " assigns no B1/B2/B3 gate decision.",
        "",
    ]

    for path in output_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
    Path(args.json_output).write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    Path(args.markdown_output).write_text("\n".join(lines), encoding="utf-8")
    audit = {
        "schema_version": "blind-gains.blindarm-margin-calibration-audit.v1",
        "status": "pass",
        "cells_verified": len(run_evidence),
        "integrity_controls_pass": not integrity_violations,
        "calibration_config_sha256": cal_config_hash,
        "seed1_config_sha256": seed1_config_hash,
        "machine_output_sha256": _sha256(Path(args.json_output)),
        "markdown_output_sha256": _sha256(Path(args.markdown_output)),
        "performance_values_opened": True,
        "calibration_verdict": verdict,
    }
    Path(args.audit_output).write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
