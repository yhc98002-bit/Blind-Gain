#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from scripts import build_pilot_4arm_seed1_readout as seed1
from src.eval.fliptrack_metrics import pair_score, template_key_shuffle_null_pair_accuracy
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT
from src.rewards.answer_reward import PARSER_VERSION, normalize_text


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "blind-gains.pilot-seed1-r19-key-shuffle.v1"
PERMUTATION_DRAWS = 1000
PERMUTATION_SEED = 0
CHART_CATEGORY_ID = "chart_two_hop_read"
CHART_DISPLAY_NAME = "cued chart point-value reading"
CATEGORY_DISPLAY_NAMES = {
    CHART_CATEGORY_ID: CHART_DISPLAY_NAME,
    "document_header_indexing": "document header indexing (calibration)",
    "geometry_coordinate_indexing": "geometry coordinate indexing",
}
OTHER_PREDICTION_BUCKET = "__other_or_invalid__"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_new(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f".{path.name}.partial.{os.getpid()}")
    partial.write_text(content, encoding="utf-8")
    os.replace(partial, path)


def _index_rows(rows: Iterable[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        pair_id = str(row.get("pair_id", ""))
        if not pair_id or pair_id in indexed:
            raise ValueError(f"missing or duplicate pair_id in {label}: {pair_id!r}")
        indexed[pair_id] = row
    if len(indexed) != 1200:
        raise ValueError(f"R19 coverage mismatch in {label}: {len(indexed)} != 1200")
    return indexed


def _validate_identity(
    base: dict[str, dict[str, Any]],
    observed: dict[str, dict[str, Any]],
    label: str,
) -> None:
    if set(base) != set(observed):
        raise ValueError(f"pair identity mismatch in {label}")
    static_fields = ("template_id", "category", "answer_a", "answer_b")
    mismatches = [
        pair_id
        for pair_id in base
        if any(base[pair_id].get(key) != observed[pair_id].get(key) for key in static_fields)
    ]
    if mismatches:
        raise ValueError(f"static R19 mismatch in {label}: {mismatches[:5]}")


def _scored_pair_accuracy(rows: Iterable[dict[str, Any]]) -> float:
    scores = [
        bool(pair_score(row, prompt_contract=DEFAULT_PROMPT_CONTRACT)["pair_correct"])
        for row in rows
    ]
    if not scores:
        raise ValueError("cannot score an empty R19 scope")
    return sum(scores) / len(scores)


def chart_member_diagnostics(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(rows)
    if not rows or {str(row.get("category")) for row in rows} != {CHART_CATEGORY_ID}:
        raise ValueError("chart diagnostics require only nonempty frozen chart rows")

    valid_answers = sorted(
        {
            normalize_text(row[key])
            for row in rows
            for key in ("answer_a", "answer_b")
        },
        key=lambda value: (float(value) if value.replace(".", "", 1).isdigit() else float("inf"), value),
    )
    valid_set = set(valid_answers)
    prediction_counts: Counter[str] = Counter()
    truth_counts: Counter[str] = Counter()
    truth_correct: Counter[str] = Counter()

    for row in rows:
        scored = pair_score(row, prompt_contract=DEFAULT_PROMPT_CONTRACT)
        for side in ("a", "b"):
            truth = normalize_text(row[f"answer_{side}"])
            prediction = normalize_text(scored[f"extracted_answer_{side}"])
            prediction_counts[
                prediction if prediction in valid_set else OTHER_PREDICTION_BUCKET
            ] += 1
            truth_counts[truth] += 1
            truth_correct[truth] += int(bool(scored[f"acc_final_{side}"]))

    member_count = 2 * len(rows)
    prediction_values = valid_answers + [OTHER_PREDICTION_BUCKET]
    return {
        "n_pairs": len(rows),
        "n_members": member_count,
        "valid_answer_values": valid_answers,
        "prediction_frequency": {
            value: {
                "count": prediction_counts[value],
                "share": prediction_counts[value] / member_count,
            }
            for value in prediction_values
        },
        "accuracy_by_answer_value": {
            value: {
                "n": truth_counts[value],
                "correct": truth_correct[value],
                "accuracy": truth_correct[value] / truth_counts[value],
            }
            for value in valid_answers
        },
    }


def chart_change_from_base(
    base: dict[str, Any], checkpoint: dict[str, Any]
) -> dict[str, Any]:
    if base["valid_answer_values"] != checkpoint["valid_answer_values"]:
        raise ValueError("chart answer support changed across checkpoints")
    prediction_values = base["valid_answer_values"] + [OTHER_PREDICTION_BUCKET]
    return {
        "prediction_share_delta": {
            value: checkpoint["prediction_frequency"][value]["share"]
            - base["prediction_frequency"][value]["share"]
            for value in prediction_values
        },
        "accuracy_delta_by_answer_value": {
            value: checkpoint["accuracy_by_answer_value"][value]["accuracy"]
            - base["accuracy_by_answer_value"][value]["accuracy"]
            for value in base["valid_answer_values"]
        },
    }


def _existing_observed(
    readout: dict[str, Any], arm: str, step: int, category: str
) -> float:
    summary = readout["fliptrack_r19"]["arms"][arm][str(step)][f"category:{category}"]
    return float(summary["pair_accuracy_observed"])


def build_analysis(
    config: dict[str, Any], existing_readout: dict[str, Any], root: Path = ROOT
) -> dict[str, Any]:
    resolved = seed1.preflight_inputs(config, root=root)
    base_rows = seed1._load_r19_shards(
        resolved["r19_base"]["shards"], "seed1:key-shuffle:step0"
    )
    base = _index_rows(base_rows, "step0")
    categories = sorted({str(row["category"]) for row in base_rows})
    if set(categories) != set(CATEGORY_DISPLAY_NAMES):
        raise ValueError(f"unexpected R19 categories: {categories}")
    template_by_category: dict[str, str] = {}
    for category in categories:
        templates = {
            str(row["template_id"]) for row in base_rows if row["category"] == category
        }
        if len(templates) != 1:
            raise ValueError(f"category is not bound to one frozen template: {category}")
        template_by_category[category] = next(iter(templates))

    rows_by_arm_step: dict[str, dict[int, list[dict[str, Any]]]] = {}
    source_artifacts: dict[str, Any] = {
        "step0": {
            "run_manifest": str(resolved["r19_base"]["manifest"].relative_to(root)),
            "run_manifest_sha256": _sha256(resolved["r19_base"]["manifest"]),
            "shards": [
                {"path": str(path.relative_to(root)), "sha256": _sha256(path)}
                for path in resolved["r19_base"]["shards"]
            ],
        },
        "arms": {},
    }
    for arm in seed1.ARMS:
        rows_by_arm_step[arm] = {0: base_rows}
        source_artifacts["arms"][arm] = {}
        for step in (60, 100):
            resolved_step = resolved["r19"][arm][step]
            rows = seed1._load_r19_shards(
                resolved_step["shards"], f"seed1:key-shuffle:{arm}:step{step}"
            )
            observed = _index_rows(rows, f"{arm}:step{step}")
            _validate_identity(base, observed, f"{arm}:step{step}")
            rows_by_arm_step[arm][step] = rows
            source_artifacts["arms"][arm][str(step)] = {
                "marker": str(resolved_step["marker"].relative_to(root)),
                "marker_sha256": _sha256(resolved_step["marker"]),
                "run_manifest": str(resolved_step["evaluation_manifest"].relative_to(root)),
                "run_manifest_sha256": _sha256(resolved_step["evaluation_manifest"]),
                "shards": [
                    {"path": str(path.relative_to(root)), "sha256": _sha256(path)}
                    for path in resolved_step["shards"]
                ],
            }

    null_rows: list[dict[str, Any]] = []
    chart: dict[str, Any] = {"arms": {}}
    step0_nulls: dict[str, dict[str, float]] = {}
    for arm in seed1.ARMS:
        chart["arms"][arm] = {}
        base_chart = chart_member_diagnostics(
            row for row in rows_by_arm_step[arm][0] if row["category"] == CHART_CATEGORY_ID
        )
        for step in (0, 60, 100):
            rows = rows_by_arm_step[arm][step]
            for category in categories:
                selected = [row for row in rows if row["category"] == category]
                observed_pair_accuracy = _scored_pair_accuracy(selected)
                if step > 0:
                    expected = _existing_observed(existing_readout, arm, step, category)
                    if abs(observed_pair_accuracy - expected) > 1e-12:
                        raise ValueError(
                            f"observed pair accuracy disagrees with seed-1 readout: "
                            f"{arm} step {step} {category}"
                        )
                if step == 0 and category in step0_nulls:
                    null = step0_nulls[category]
                else:
                    null = template_key_shuffle_null_pair_accuracy(
                        selected, n_perm=PERMUTATION_DRAWS, seed=PERMUTATION_SEED
                    )
                    if step == 0:
                        step0_nulls[category] = null
                if abs(null["observed"] - observed_pair_accuracy) > 1e-12:
                    raise ValueError("null observed score failed frozen-scorer recomputation")
                null_rows.append(
                    {
                        "arm": arm,
                        "checkpoint": step,
                        "category_id": category,
                        "category_display_name": CATEGORY_DISPLAY_NAMES[category],
                        "template_id": template_by_category[category],
                        "n_pairs": len(selected),
                        "observed_pair_accuracy": null["observed"],
                        "null_mean": null["null_mean"],
                        "p_value_ge_observed": null["p_ge"],
                    }
                )

            checkpoint_chart = chart_member_diagnostics(
                row for row in rows if row["category"] == CHART_CATEGORY_ID
            )
            checkpoint_chart["change_from_step0"] = (
                None if step == 0 else chart_change_from_base(base_chart, checkpoint_chart)
            )
            chart["arms"][arm][str(step)] = checkpoint_chart

    scorer_path = root / "src/eval/fliptrack_metrics.py"
    existing_path = root / "reports/pilot_4arm_seed1_results_v1.json"
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "complete",
        "scientific_gate_decision": None,
        "analysis_scope": "cached predictions only; no inference or retraining",
        "seed1_readout": {
            "path": str(existing_path.relative_to(root)),
            "sha256": _sha256(existing_path),
            "pi_verification": "CORE READOUT PASS",
        },
        "frozen_scoring": {
            "parser_version": PARSER_VERSION,
            "scorer_path": str(scorer_path.relative_to(root)),
            "scorer_sha256": _sha256(scorer_path),
            "prompt_contract_id": DEFAULT_PROMPT_CONTRACT.contract_id,
            "permutation_method": "shuffle answer-key pairs within each frozen template",
            "permutation_draws": PERMUTATION_DRAWS,
            "permutation_seed": PERMUTATION_SEED,
            "p_value": "(count(null >= observed) + 1) / (draws + 1)",
        },
        "checks": {
            "all_source_runs_complete_before_prediction_loading": True,
            "all_cells_have_1200_unique_pair_ids": True,
            "static_identity_matches_step0": True,
            "observed_checkpoint_values_match_seed1_readout": True,
            "cell_count": len(null_rows),
            "expected_cell_count": len(seed1.ARMS) * 3 * len(categories),
            "chart_human_label_exact": CHART_DISPLAY_NAME,
            "model_performance_interpretation_made": False,
        },
        "category_template_compatibility_map": template_by_category,
        "key_shuffle_cells": null_rows,
        "chart_diagnostics": chart,
        "source_artifacts": source_artifacts,
    }


def _format(value: float) -> str:
    return f"{value:.4f}"


def render_markdown(payload: dict[str, Any], machine_path: Path) -> str:
    frozen = payload["frozen_scoring"]
    lines = [
        "# Seed-1 R19 Key-Shuffle Null and Chart Diagnostics V1",
        "",
        "Status:",
        "- Cached-prediction analysis complete; no inference or retraining was run.",
        "- This report adds the registered null and chart diagnostics to the PI-verified seed-1 core readout. It makes no scientific gate decision.",
        "- Rejecting this null does not by itself establish perceptual learning.",
        "",
        "Evidence:",
        f"- Machine artifact: `{machine_path}`.",
        f"- Frozen parser: `{frozen['parser_version']}`; scorer SHA256: `{frozen['scorer_sha256']}`.",
        f"- Within-template answer-key shuffles: `{frozen['permutation_draws']}`; seed: `{frozen['permutation_seed']}`.",
        "- Every checkpoint row was recomputed from the immutable cached predictions and checked against the existing seed-1 category value.",
        "",
        "## Within-Template Key-Shuffle Null",
        "",
        "| Arm | Checkpoint | R19 construct | n | Observed pair acc | Null mean | p(null >= observed) |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for row in payload["key_shuffle_cells"]:
        lines.append(
            f"| {seed1.DISPLAY_NAMES[row['arm']]} | {row['checkpoint']} | "
            f"{row['category_display_name']} | {row['n_pairs']} | "
            f"{_format(row['observed_pair_accuracy'])} | {_format(row['null_mean'])} | "
            f"{_format(row['p_value_ge_observed'])} |"
        )

    lines.extend(
        [
            "",
            "The legacy chart category identifier is retained only in the machine artifact for compatibility. Human-facing text uses **cued chart point-value reading**.",
            "",
            "## Cued Chart Point-Value Reading",
            "",
            "Prediction frequency is computed over the 600 pair members. Predictions outside the frozen answer support are grouped as `other/invalid`. Accuracy is member accuracy conditioned on the ground-truth answer value.",
        ]
    )
    for arm in seed1.ARMS:
        lines.extend(["", f"### {seed1.DISPLAY_NAMES[arm]}", ""])
        steps = payload["chart_diagnostics"]["arms"][arm]
        values = steps["0"]["valid_answer_values"] + [OTHER_PREDICTION_BUCKET]
        lines.extend(
            [
                "| Predicted value | Step 0 share | Step 60 share (change) | Step 100 share (change) |",
                "|---|---:|---:|---:|",
            ]
        )
        for value in values:
            display = "other/invalid" if value == OTHER_PREDICTION_BUCKET else value
            base_share = steps["0"]["prediction_frequency"][value]["share"]
            cells = []
            for step in (60, 100):
                share = steps[str(step)]["prediction_frequency"][value]["share"]
                delta = steps[str(step)]["change_from_step0"]["prediction_share_delta"][value]
                cells.append(f"{share:.4f} ({delta:+.4f})")
            lines.append(
                f"| {display} | {base_share:.4f} | {cells[0]} | {cells[1]} |"
            )
        lines.extend(
            [
                "",
                "| Ground-truth value | n | Step 0 acc | Step 60 acc (change) | Step 100 acc (change) |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for value in steps["0"]["valid_answer_values"]:
            base_accuracy = steps["0"]["accuracy_by_answer_value"][value]["accuracy"]
            n = steps["0"]["accuracy_by_answer_value"][value]["n"]
            cells = []
            for step in (60, 100):
                accuracy = steps[str(step)]["accuracy_by_answer_value"][value]["accuracy"]
                delta = steps[str(step)]["change_from_step0"]["accuracy_delta_by_answer_value"][value]
                cells.append(f"{accuracy:.4f} ({delta:+.4f})")
            lines.append(
                f"| {value} | {n} | {base_accuracy:.4f} | {cells[0]} | {cells[1]} |"
            )

    lines.extend(
        [
            "",
            "Problems:",
            "- These diagnostics test compatibility with marginal answer-key regularities; they do not identify a perceptual mechanism.",
            "- Seed-1 chart deltas remain non-final until seeds 2-3 land.",
            "",
            "Decision:",
            "- None. Chart outputs are now eligible for PI interpretation and paper-figure gating, subject to the registered caveats.",
            "",
            "Next actions:",
            "- Carry this null alongside every seed-1 chart category table.",
            "- Recompute the same frozen analysis for the multi-seed summary without changing permutation settings.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", default="experiments/manifests/pilot_4arm_seed1_readout_v2.json"
    )
    parser.add_argument(
        "--existing-readout", default="reports/pilot_4arm_seed1_results_v1.json"
    )
    parser.add_argument(
        "--output-json", default="reports/pilot_4arm_seed1_r19_null_v1.json"
    )
    parser.add_argument(
        "--output-md", default="reports/pilot_4arm_seed1_r19_null_v1.md"
    )
    args = parser.parse_args()

    config_path = (ROOT / args.config).resolve()
    readout_path = (ROOT / args.existing_readout).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["config_path"] = str(config_path.relative_to(ROOT))
    existing = json.loads(readout_path.read_text(encoding="utf-8"))
    payload = build_analysis(config, existing, root=ROOT)
    payload["analysis_config"] = {
        "path": str(config_path.relative_to(ROOT)),
        "sha256": _sha256(config_path),
    }
    output_json = (ROOT / args.output_json).resolve()
    output_md = (ROOT / args.output_md).resolve()
    _write_new(output_json, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    try:
        _write_new(output_md, render_markdown(payload, output_json.relative_to(ROOT)))
    except Exception:
        output_json.unlink(missing_ok=True)
        raise


if __name__ == "__main__":
    main()
