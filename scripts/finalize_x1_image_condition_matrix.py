#!/usr/bin/env python3
"""Fail-closed finalizer for the registered X1 image-condition matrix.

Implements docs/registered_x1_matrix_v1.md and nothing beyond it: verifies the
ten novel candidate-evidence ranking cells, the fifteen pinned correct/gray/
no-image ranking cells from the audited seed-1 and calibration matrices, and
the twenty-five open-form realization cells; computes the registered readings
(a)/(b)/(c) and the wrong-item vs right-item secondary; renders the machine
JSON, the report, and the audit. No interpretation beyond the registered
readings enters the output.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from src.eval.visual_evidence_ranking import SCORER_VERSION, bootstrap_mean_ci

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
ARMS = ("a1_step100", "a2_step100", "a2b_step100", "a3_step100")
MODELS = ("base",) + ARMS
NEW_CONDITIONS = ("mismatched_real", "twin_counterfactual")
PINNED_CONDITIONS = ("real", "gray", "no_image")
OPENFORM_CONDITIONS = ("real", "gray", "no_image", "mismatched_real", "twin_counterfactual")
N_BOOT = 10000
BOOT_SEED = 20260717


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


def verify_ranking_cell(
    run_dir: Path,
    *,
    config: dict[str, Any],
    config_hash: str,
    registry_by_pair: dict[str, dict[str, Any]],
    expected_pair_ids: set[str],
) -> tuple[str, str, list[dict[str, Any]], dict[str, Any]]:
    manifest_path = run_dir / "run_manifest.json"
    manifest = _read_json(manifest_path)
    model = str(manifest["model_key"])
    condition = str(manifest["condition"])
    if manifest.get("status") != "complete" or manifest.get("exit_code") != 0:
        raise ValueError(f"ranking cell is not complete: {run_dir}")
    if manifest.get("limit") is not None:
        raise ValueError(f"limited smoke run cannot enter results: {run_dir}")
    if manifest.get("data_manifest_hash") != str(config["candidate_registry"]["sha256"]):
        raise ValueError(f"candidate registry mismatch: {run_dir}")
    if manifest.get("config_hash") != config_hash:
        raise ValueError(f"config hash mismatch: {run_dir}")
    if manifest.get("model_index_sha256") != config["models"][model]["model_index_sha256"]:
        raise ValueError(f"model hash mismatch: {run_dir}")
    if manifest.get("scorer_version") != SCORER_VERSION:
        raise ValueError(f"scorer version mismatch: {run_dir}")
    rows = _read_jsonl(run_dir / "scores.jsonl")
    if len(rows) != int(config["candidate_registry"]["pair_count"]):
        raise ValueError(f"row count mismatch: {run_dir}")
    observed = {str(row["pair_id"]) for row in rows}
    if len(observed) != len(rows) or observed != expected_pair_ids:
        raise ValueError(f"pair identity mismatch: {run_dir}")
    if any(row["model_key"] != model or row["condition"] != condition for row in rows):
        raise ValueError(f"row cell identity mismatch: {run_dir}")
    if any(
        row.get("candidate_set_sha256")
        != registry_by_pair[str(row["pair_id"])]["candidate_set_sha256"]
        for row in rows
    ):
        raise ValueError(f"candidate-set hash mismatch: {run_dir}")
    evidence = {
        "run_dir": str(run_dir.relative_to(ROOT)),
        "manifest_sha256": _sha256(manifest_path),
        "output_sha256": _sha256(run_dir / "scores.jsonl"),
        "model_key": model,
        "condition": condition,
        "rows": len(rows),
        "layer": "candidate-evidence ranking",
    }
    return model, condition, rows, evidence


def find_one(pattern: str) -> Path:
    matches = sorted(glob.glob(str(ROOT / pattern)))
    complete = []
    for match in matches:
        manifest = Path(match) / "run_manifest.json"
        if manifest.is_file():
            payload = _read_json(manifest)
            if payload.get("status") == "complete" and payload.get("exit_code") == 0:
                complete.append(Path(match))
    if len(complete) != 1:
        raise ValueError(f"expected exactly one complete run for {pattern}, found {len(complete)}")
    return complete[0]


def ratio_ci(
    numerator: list[float], denominator: list[float], n_boot: int, seed: int
) -> tuple[float | None, float | None, bool]:
    array_n = np.asarray(numerator, dtype=np.float64)
    array_d = np.asarray(denominator, dtype=np.float64)
    rng = np.random.default_rng(seed)
    ratios: list[float] = []
    unstable = False
    for start in range(0, n_boot, 1024):
        count = min(1024, n_boot - start)
        idx = rng.integers(0, len(array_n), size=(count, len(array_n)))
        means_n = array_n[idx].mean(axis=1)
        means_d = array_d[idx].mean(axis=1)
        bad = np.abs(means_d) < 1e-9
        if bad.any():
            unstable = True
            means_n = means_n[~bad]
            means_d = means_d[~bad]
        ratios.extend((means_n / means_d).tolist())
    if not ratios:
        return None, None, True
    ratios.sort()
    lower = ratios[max(0, math.floor(0.025 * len(ratios)))]
    upper = ratios[min(len(ratios) - 1, math.ceil(0.975 * len(ratios)) - 1)]
    return lower, upper, unstable


def summarize(values: list[float]) -> dict[str, Any]:
    lower, upper = bootstrap_mean_ci(values, n_boot=N_BOOT, seed=BOOT_SEED)
    return {"n_pairs": len(values), "mean": sum(values) / len(values), "ci95": [lower, upper]}


def intervals_overlap(a: list[float], b: list[float]) -> bool:
    return a[0] <= b[1] and b[0] <= a[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--markdown-output", required=True)
    parser.add_argument("--audit-output", required=True)
    args = parser.parse_args()
    outputs = [Path(args.json_output), Path(args.markdown_output), Path(args.audit_output)]
    if any(path.exists() for path in outputs):
        raise FileExistsError("refusing to overwrite X1 result artifacts")

    x1_config_path = ROOT / "configs/eval/x1_image_condition_matrix_v1.json"
    seed1_config_path = ROOT / "configs/eval/seed1_visual_evidence_ranking_v1.json"
    cal_config_path = ROOT / "configs/eval/blindarm_margin_calibration_v1.json"
    x1_config = _read_json(x1_config_path)
    seed1_config = _read_json(seed1_config_path)
    cal_config = _read_json(cal_config_path)
    hashes = {
        "x1": _sha256(x1_config_path),
        "seed1": _sha256(seed1_config_path),
        "calibration": _sha256(cal_config_path),
    }
    registry_path = ROOT / str(x1_config["candidate_registry"]["path"])
    if _sha256(registry_path) != str(x1_config["candidate_registry"]["sha256"]):
        raise ValueError("frozen candidate registry hash mismatch on disk")
    registry_rows = _read_jsonl(registry_path)
    registry_by_pair = {str(row["pair_id"]): row for row in registry_rows}
    expected_pair_ids = set(registry_by_pair)

    ranking: dict[tuple[str, str], list[dict[str, Any]]] = {}
    evidence: list[dict[str, Any]] = []
    for model in MODELS:
        for condition in NEW_CONDITIONS:
            run_dir = find_one(
                f"experiments/runs/d1_visual_evidence_{model}_{condition}_*_x1_ranking_matrix_queue_login_20260724T085613Z"
            )
            key_model, key_condition, rows, cell_evidence = verify_ranking_cell(
                run_dir,
                config=x1_config,
                config_hash=hashes["x1"],
                registry_by_pair=registry_by_pair,
                expected_pair_ids=expected_pair_ids,
            )
            ranking[(key_model, key_condition)] = rows
            evidence.append(cell_evidence)
    pinned_sources = {
        "base": ("d1_visual_evidence_matrix_queue_login_20260717T175951Z", seed1_config, "seed1"),
        "a1_step100": ("d1_visual_evidence_matrix_queue_login_20260717T175951Z", seed1_config, "seed1"),
        "a2_step100": ("blindarm_margin_calibration_matrix_queue_login_20260723T143504Z", cal_config, "calibration"),
        "a2b_step100": ("blindarm_margin_calibration_matrix_queue_login_20260723T143504Z", cal_config, "calibration"),
        "a3_step100": ("blindarm_margin_calibration_matrix_queue_login_20260723T143504Z", cal_config, "calibration"),
    }
    for model, (suffix, family_config, family) in pinned_sources.items():
        for condition in PINNED_CONDITIONS:
            run_dir = find_one(
                f"experiments/runs/d1_visual_evidence_{model}_{condition}_*_{suffix}"
            )
            key_model, key_condition, rows, cell_evidence = verify_ranking_cell(
                run_dir,
                config=family_config,
                config_hash=hashes[family],
                registry_by_pair=registry_by_pair,
                expected_pair_ids=expected_pair_ids,
            )
            cell_evidence["pinned_from"] = family
            ranking[(key_model, key_condition)] = rows
            evidence.append(cell_evidence)
    if len(ranking) != len(MODELS) * 5:
        raise ValueError(f"ranking matrix incomplete: {len(ranking)} cells")

    openform: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for model in MODELS:
        for condition in OPENFORM_CONDITIONS:
            run_dir = find_one(f"experiments/runs/x1_openform_{model}_{condition}_an12_*")
            manifest = _read_json(run_dir / "run_manifest.json")
            if manifest.get("config_hash") != hashes["x1"]:
                raise ValueError(f"open-form config hash mismatch: {run_dir}")
            if (
                manifest.get("model_index_sha256")
                != x1_config["models"][model]["model_index_sha256"]
            ):
                raise ValueError(f"open-form model hash mismatch: {run_dir}")
            rows = _read_jsonl(run_dir / "predictions.jsonl")
            if len(rows) != 1200:
                raise ValueError(f"open-form row count mismatch: {run_dir}")
            openform[(model, condition)] = rows
            evidence.append(
                {
                    "run_dir": str(run_dir.relative_to(ROOT)),
                    "manifest_sha256": _sha256(run_dir / "run_manifest.json"),
                    "output_sha256": _sha256(run_dir / "predictions.jsonl"),
                    "model_key": model,
                    "condition": condition,
                    "rows": len(rows),
                    "layer": "open-form realization",
                }
            )

    indexed: dict[tuple[str, str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    templates: set[str] = set()
    for (model, condition), rows in ranking.items():
        for row in rows:
            template = str(row["template_id"])
            templates.add(template)
            indexed[(model, condition, template)][str(row["pair_id"])] = row
    template_list = sorted(templates)
    primary_template = str(x1_config["analysis"]["primary_template"])

    margin = lambda cell, pair: float(cell[pair]["paired_margin"])  # noqa: E731

    inflation_effects: dict[str, Any] = {}
    readings_ab: dict[str, Any] = {}
    for arm in ARMS:
        for template in template_list:
            base_real = indexed[("base", "real", template)]
            base_mis = indexed[("base", "mismatched_real", template)]
            arm_real = indexed[(arm, "real", template)]
            arm_mis = indexed[(arm, "mismatched_real", template)]
            pairs = sorted(base_real)
            correct_diffs = [margin(arm_real, p) - margin(base_real, p) for p in pairs]
            mismatched_diffs = [margin(arm_mis, p) - margin(base_mis, p) for p in pairs]
            correct_summary = summarize(correct_diffs)
            mismatched_summary = summarize(mismatched_diffs)
            ratio = (
                correct_summary["mean"] / mismatched_summary["mean"]
                if abs(mismatched_summary["mean"]) > 1e-9
                else None
            )
            r_lower, r_upper, r_unstable = ratio_ci(
                correct_diffs, mismatched_diffs, N_BOOT, BOOT_SEED
            )
            key = f"{arm}|{template}"
            inflation_effects[key] = {
                "inflation_correct": correct_summary,
                "inflation_mismatched": mismatched_summary,
                "ratio_correct_over_mismatched": ratio,
                "ratio_ci95": [r_lower, r_upper],
                "ratio_bootstrap_unstable": r_unstable,
            }
            if template == primary_template:
                if ratio is None:
                    reading = "ratio_undefined_mismatched_inflation_near_zero"
                elif 0.8 <= ratio <= 1.25:
                    reading = "a_image_presence_gating"
                elif ratio > 1.25 and not intervals_overlap(
                    correct_summary["ci95"], mismatched_summary["ci95"]
                ):
                    reading = "b_content_specific_evidence_sharpening"
                else:
                    reading = "outside_registered_readings"
                readings_ab[arm] = {
                    "ratio": ratio,
                    "ratio_ci95": [r_lower, r_upper],
                    "inflation_cis_overlap": intervals_overlap(
                        correct_summary["ci95"], mismatched_summary["ci95"]
                    ),
                    "registered_reading": reading,
                }

    twin_readings: dict[str, Any] = {}
    for model in MODELS:
        for template in template_list:
            twin_cell = indexed[(model, "twin_counterfactual", template)]
            real_cell = indexed[(model, "real", template)]
            members = 0
            twin_gold_preferred = 0
            sign_flip_members = 0
            realpos_members = 0
            realpos_flipped = 0
            for pair_id, row in twin_cell.items():
                registry_row = registry_by_pair[pair_id]
                for side in ("a", "b"):
                    twin_side = "b" if side == "a" else "a"
                    own_gold = str(registry_row[f"gold_candidate_id_{side}"])
                    twin_gold = str(registry_row[f"gold_candidate_id_{twin_side}"])
                    scores = row[f"candidate_scores_{side}"]
                    members += 1
                    if float(scores[twin_gold]) > float(scores[own_gold]):
                        twin_gold_preferred += 1
                    twin_margin = float(row[f"margin_{side}"])
                    if twin_margin < 0:
                        sign_flip_members += 1
                    real_margin = float(real_cell[pair_id][f"margin_{side}"])
                    if real_margin > 0:
                        realpos_members += 1
                        if twin_margin < 0:
                            realpos_flipped += 1
            twin_readings[f"{model}|{template}"] = {
                "members": members,
                "twin_gold_preferred_rate": twin_gold_preferred / members,
                "margin_sign_negative_rate": sign_flip_members / members,
                "flip_rate_given_real_positive": (
                    realpos_flipped / realpos_members if realpos_members else None
                ),
                "real_positive_members": realpos_members,
            }

    secondary: dict[str, Any] = {}
    for arm in ARMS:
        for template in template_list:
            arm_open = {
                str(row["pair_id"]): bool(row["pair_correct"])
                for row in openform[(arm, "real")]
                if str(row["template_id"]) == template
            }
            base_real = indexed[("base", "real", template)]
            arm_real = indexed[(arm, "real", template)]
            right = [
                margin(arm_real, p) - margin(base_real, p)
                for p in sorted(base_real)
                if arm_open[p]
            ]
            wrong = [
                margin(arm_real, p) - margin(base_real, p)
                for p in sorted(base_real)
                if not arm_open[p]
            ]
            entry: dict[str, Any] = {
                "right_items": len(right),
                "wrong_items": len(wrong),
            }
            if right:
                entry["inflation_right_items"] = summarize(right)
            if wrong:
                entry["inflation_wrong_items"] = summarize(wrong)
            if right and wrong:
                entry["ratio_wrong_over_right"] = (
                    (sum(wrong) / len(wrong)) / (sum(right) / len(right))
                    if abs(sum(right) / len(right)) > 1e-9
                    else None
                )
            secondary[f"{arm}|{template}"] = entry

    realization: dict[str, Any] = {}
    for (model, condition), rows in openform.items():
        by_template: dict[str, list[bool]] = defaultdict(list)
        for row in rows:
            by_template[str(row["template_id"])].append(bool(row["pair_correct"]))
        realization[f"{model}|{condition}"] = {
            "pair_correct_overall": sum(v for values in by_template.values() for v in values)
            / sum(len(values) for values in by_template.values()),
            **{
                f"pair_correct_{template}": sum(values) / len(values)
                for template, values in sorted(by_template.items())
            },
        }

    result = {
        "schema_version": "blind-gains.x1-image-condition-results.v1",
        "status": "complete",
        "registration": "docs/registered_x1_matrix_v1.md",
        "scorer_version": SCORER_VERSION,
        "primary_template": primary_template,
        "ratio_definition": "inflation_correct.mean / inflation_mismatched.mean, where inflation_X = per-pair (arm margin - base margin) under condition X; paired bootstrap 10000 resamples seed 20260717",
        "registered_readings_ab": readings_ab,
        "reading_c_twin_condition": twin_readings,
        "secondary_wrong_vs_right": secondary,
        "inflation_effects": inflation_effects,
        "open_form_realization": realization,
        "provenance": {
            "configs": {
                "x1": {"path": str(x1_config_path.relative_to(ROOT)), "sha256": hashes["x1"]},
                "seed1": {"path": str(seed1_config_path.relative_to(ROOT)), "sha256": hashes["seed1"]},
                "calibration": {"path": str(cal_config_path.relative_to(ROOT)), "sha256": hashes["calibration"]},
            },
            "candidate_registry_sha256": str(x1_config["candidate_registry"]["sha256"]),
            "truncation_guard": "reports/x1_openform_truncation_guard_v1.json (32-token budget stands)",
            "cells": sorted(evidence, key=lambda item: (item["layer"], item["model_key"], item["condition"])),
        },
    }

    lines = [
        "# X1 image-condition matrix results (v1)",
        "",
        "Registered: `docs/registered_x1_matrix_v1.md`. Layers: candidate-evidence",
        "ranking and open-form realization. All open-form cells use the locked",
        "32-token greedy contract (truncation guard: 0/250 sampled rows truncated).",
        "Statistics below are the registered readings and registered secondary only.",
        "",
        f"- Ratio definition: {result['ratio_definition']}",
        f"- Primary template: `{primary_template}`",
        "",
        "## Registered readings (a)/(b): margin-inflation ratio, primary template",
        "",
        "| arm | inflation correct | inflation mismatched | ratio (correct/mismatched) | ratio 95% CI | registered reading |",
        "|---|---|---|---|---|---|",
    ]
    for arm in ARMS:
        effect = inflation_effects[f"{arm}|{primary_template}"]
        reading = readings_ab[arm]
        ci = reading["ratio_ci95"]
        lines.append(
            f"| {arm} | {effect['inflation_correct']['mean']:+.4f}"
            f" [{effect['inflation_correct']['ci95'][0]:+.4f}, {effect['inflation_correct']['ci95'][1]:+.4f}]"
            f" | {effect['inflation_mismatched']['mean']:+.4f}"
            f" [{effect['inflation_mismatched']['ci95'][0]:+.4f}, {effect['inflation_mismatched']['ci95'][1]:+.4f}]"
            f" | {reading['ratio']:.3f} | [{ci[0]:.3f}, {ci[1]:.3f}] | {reading['registered_reading']} |"
        )
    lines += [
        "",
        "## Registered reading (c): twin-counterfactual condition, primary template",
        "",
        "| model | twin-gold preferred rate | margin sign negative rate | flip rate given real-positive |",
        "|---|---|---|---|",
    ]
    for model in MODELS:
        reading = twin_readings[f"{model}|{primary_template}"]
        conditional = reading["flip_rate_given_real_positive"]
        lines.append(
            f"| {model} | {reading['twin_gold_preferred_rate']:.4f}"
            f" | {reading['margin_sign_negative_rate']:.4f}"
            f" | {conditional if conditional is None else format(conditional, '.4f')} |"
        )
    lines += [
        "",
        "## Registered secondary: wrong-item vs right-item margin inflation (real condition, primary template)",
        "",
        "| arm | right items | wrong items | inflation right | inflation wrong | ratio wrong/right |",
        "|---|---|---|---|---|---|",
    ]
    for arm in ARMS:
        entry = secondary[f"{arm}|{primary_template}"]
        right_summary = entry.get("inflation_right_items")
        wrong_summary = entry.get("inflation_wrong_items")
        lines.append(
            f"| {arm} | {entry['right_items']} | {entry['wrong_items']}"
            f" | {right_summary['mean']:+.4f}" if right_summary else "| n/a"
        )
        rendered = (
            f"| {arm} | {entry['right_items']} | {entry['wrong_items']} | "
            + (f"{right_summary['mean']:+.4f}" if right_summary else "n/a")
            + " | "
            + (f"{wrong_summary['mean']:+.4f}" if wrong_summary else "n/a")
            + " | "
            + (
                f"{entry['ratio_wrong_over_right']:.3f}"
                if entry.get("ratio_wrong_over_right") is not None
                else "n/a"
            )
            + " |"
        )
        lines[-1] = rendered
    lines += [
        "",
        "## Open-form realization: pair-correct by model x condition (all templates pooled)",
        "",
        "| model | real | mismatched_real | twin_counterfactual | gray | no_image |",
        "|---|---|---|---|---|---|",
    ]
    for model in MODELS:
        cells = [
            f"{realization[f'{model}|{condition}']['pair_correct_overall']:.4f}"
            for condition in ("real", "mismatched_real", "twin_counterfactual", "gray", "no_image")
        ]
        lines.append(f"| {model} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "Per-template tables, all inflation effects, and full cell provenance are in",
        "the machine JSON. No interpretation beyond the registered readings.",
        "",
    ]

    for path in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
    Path(args.json_output).write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    Path(args.markdown_output).write_text("\n".join(lines), encoding="utf-8")
    audit = {
        "schema_version": "blind-gains.x1-image-condition-audit.v1",
        "status": "pass",
        "ranking_cells_verified": sum(1 for item in evidence if item["layer"] == "candidate-evidence ranking"),
        "openform_cells_verified": sum(1 for item in evidence if item["layer"] == "open-form realization"),
        "machine_output_sha256": _sha256(Path(args.json_output)),
        "markdown_output_sha256": _sha256(Path(args.markdown_output)),
        "performance_values_opened": True,
    }
    Path(args.audit_output).write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({**audit, "readings": {arm: readings_ab[arm]["registered_reading"] for arm in ARMS}}, sort_keys=True))


if __name__ == "__main__":
    main()
