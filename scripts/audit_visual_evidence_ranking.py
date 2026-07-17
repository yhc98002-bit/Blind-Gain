#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def recompute_row(row: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    gold_a = str(registry["gold_candidate_id_a"])
    gold_b = str(registry["gold_candidate_id_b"])
    scores_a = {str(key): float(value) for key, value in row["candidate_scores_a"].items()}
    scores_b = {str(key): float(value) for key, value in row["candidate_scores_b"].items()}
    expected_ids = {str(item["candidate_id"]) for item in registry["candidates"]}
    if set(scores_a) != expected_ids or set(scores_b) != expected_ids:
        raise ValueError("raw score keys do not match the frozen candidate set")
    margin_a = scores_a[gold_a] - scores_a[gold_b]
    margin_b = scores_b[gold_b] - scores_b[gold_a]
    raw_a = {
        str(key): float(value)
        for key, value in row["candidate_raw_sum_scores_a"].items()
    }
    raw_b = {
        str(key): float(value)
        for key, value in row["candidate_raw_sum_scores_b"].items()
    }
    if set(raw_a) != expected_ids or set(raw_b) != expected_ids:
        raise ValueError("raw-sum score keys do not match the frozen candidate set")

    def conservative_rank(scores: dict[str, float], gold: str) -> int:
        gold_score = scores[gold]
        return 1 + sum(
            candidate != gold and score >= gold_score - 1e-12
            for candidate, score in scores.items()
        )

    rank_a = conservative_rank(scores_a, gold_a)
    rank_b = conservative_rank(scores_b, gold_b)
    raw_margin_a = raw_a[gold_a] - raw_a[gold_b]
    raw_margin_b = raw_b[gold_b] - raw_b[gold_a]
    return {
        "margin_a": margin_a,
        "margin_b": margin_b,
        "paired_margin": (margin_a + margin_b) / 2.0,
        "pair_success": margin_a > 0.0 and margin_b > 0.0,
        "rank_a": rank_a,
        "rank_b": rank_b,
        "candidate_top1_a": rank_a == 1,
        "candidate_top1_b": rank_b == 1,
        "candidate_pair_top1": rank_a == 1 and rank_b == 1,
        "mrr_a": 1.0 / rank_a,
        "mrr_b": 1.0 / rank_b,
        "candidate_pair_mrr": (1.0 / rank_a + 1.0 / rank_b) / 2.0,
        "raw_sum_margin_a_robustness": raw_margin_a,
        "raw_sum_margin_b_robustness": raw_margin_b,
        "raw_sum_paired_margin_robustness": (raw_margin_a + raw_margin_b) / 2.0,
    }


def _bootstrap(values: list[float], n_boot: int, seed: int) -> list[float]:
    array = np.asarray(values, dtype=np.float64)
    rng = np.random.Generator(np.random.PCG64(seed))
    means: list[float] = []
    for start in range(0, n_boot, 1024):
        count = min(1024, n_boot - start)
        indices = rng.integers(0, len(array), size=(count, len(array)))
        means.extend(array[indices].mean(axis=1).tolist())
    means.sort()
    return means


def _effect_summary(values: list[float], n_boot: int, seed: int) -> dict[str, Any]:
    means = _bootstrap(values, n_boot=n_boot, seed=seed)
    return {
        "n_pairs": len(values),
        "mean": sum(values) / len(values),
        "ci95": [means[math.floor(0.025 * n_boot)], means[math.ceil(0.975 * n_boot) - 1]],
    }


def _summary_matches(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return (
        int(left["n_pairs"]) == int(right["n_pairs"])
        and math.isclose(float(left["mean"]), float(right["mean"]), rel_tol=0.0, abs_tol=1e-12)
        and all(
            math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=1e-12)
            for a, b in zip(left["ci95"], right["ci95"])
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--result-json", required=True)
    parser.add_argument("--result-markdown", required=True)
    parser.add_argument("--run-dir", action="append", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite audit: {output}")

    config = _json(Path(args.config))
    result = _json(Path(args.result_json))
    registry_rows = _jsonl(Path(config["candidate_registry"]["path"]))
    registry = {str(row["pair_id"]): row for row in registry_rows}
    cells: dict[tuple[str, str], dict[str, dict[str, Any]]] = {}
    stored_metric_mismatches = 0
    for value in args.run_dir:
        run_dir = Path(value)
        manifest = _json(run_dir / "run_manifest.json")
        key = (str(manifest["model_key"]), str(manifest["condition"]))
        rows: dict[str, dict[str, Any]] = {}
        for row in _jsonl(run_dir / "scores.jsonl"):
            pair_id = str(row["pair_id"])
            recalculated = recompute_row(row, registry[pair_id])
            for field in (
                "margin_a",
                "margin_b",
                "paired_margin",
                "mrr_a",
                "mrr_b",
                "candidate_pair_mrr",
                "raw_sum_margin_a_robustness",
                "raw_sum_margin_b_robustness",
                "raw_sum_paired_margin_robustness",
            ):
                if not math.isclose(
                    float(row[field]), float(recalculated[field]), rel_tol=0.0, abs_tol=1e-12
                ):
                    stored_metric_mismatches += 1
            if bool(row["pair_success"]) != bool(recalculated["pair_success"]):
                stored_metric_mismatches += 1
            for field in (
                "rank_a",
                "rank_b",
                "candidate_top1_a",
                "candidate_top1_b",
                "candidate_pair_top1",
            ):
                if row[field] != recalculated[field]:
                    stored_metric_mismatches += 1
            rows[pair_id] = {**row, **recalculated}
        cells[key] = rows

    template = str(config["analysis"]["primary_template"])
    pair_ids = sorted(
        pair_id for pair_id, row in registry.items() if row["template_id"] == template
    )
    base_real = cells[("base", "real")]
    trained_real = cells[("a1_step100", "real")]
    base_none = cells[("base", "no_image")]
    trained_none = cells[("a1_step100", "no_image")]
    effects = [
        (float(trained_real[pair_id]["paired_margin"]) - float(base_real[pair_id]["paired_margin"]))
        - (float(trained_none[pair_id]["paired_margin"]) - float(base_none[pair_id]["paired_margin"]))
        for pair_id in pair_ids
    ]
    n_boot = int(config["analysis"]["bootstrap"]["resamples"])
    seed = int(config["analysis"]["bootstrap"]["seed"])
    recomputed_primary = _effect_summary(effects, n_boot=n_boot, seed=seed)
    published = result["primary_effect"]["paired_margin_primary"]
    effect_summary_mismatches = 0
    effect_field_map = {
        "paired_margin_primary": "paired_margin",
        "pair_success_secondary": "pair_success",
        "candidate_pair_top1_secondary": "candidate_pair_top1",
        "candidate_pair_mrr_secondary": "candidate_pair_mrr",
        "raw_sum_margin_robustness": "raw_sum_paired_margin_robustness",
    }
    for published_effect in result["effects"].values():
        trained_model = str(published_effect["trained_model"])
        blind = str(published_effect["blind_comparator"])
        effect_template = str(published_effect["template_id"])
        effect_ids = sorted(
            pair_id
            for pair_id, registry_row in registry.items()
            if registry_row["template_id"] == effect_template
        )
        for summary_field, row_field in effect_field_map.items():
            values = [
                (
                    float(cells[(trained_model, "real")][pair_id][row_field])
                    - float(cells[("base", "real")][pair_id][row_field])
                )
                - (
                    float(cells[(trained_model, blind)][pair_id][row_field])
                    - float(cells[("base", blind)][pair_id][row_field])
                )
                for pair_id in effect_ids
            ]
            recomputed = _effect_summary(values, n_boot=n_boot, seed=seed)
            if not _summary_matches(published_effect[summary_field], recomputed):
                effect_summary_mismatches += 1
    markdown = Path(args.result_markdown).read_text(encoding="utf-8")
    checks = {
        "exact_nine_cells": set(cells)
        == {(model, condition) for model in ("base", "a1_step60", "a1_step100") for condition in ("real", "no_image", "gray")},
        "all_cells_exact_pair_set": all(set(rows) == set(registry) for rows in cells.values()),
        "stored_margin_recompute_zero_mismatches": stored_metric_mismatches == 0,
        "primary_n_exact": int(published["n_pairs"]) == recomputed_primary["n_pairs"],
        "primary_mean_exact": math.isclose(float(published["mean"]), recomputed_primary["mean"], rel_tol=0.0, abs_tol=1e-12),
        "primary_ci_exact": all(
            math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=1e-12)
            for left, right in zip(published["ci95"], recomputed_primary["ci95"])
        ),
        "all_effect_summaries_exact": effect_summary_mismatches == 0,
        "branch_unassigned": result.get("branch_assignment") is None,
        "prohibited_phrase_absent": "perception improved" not in markdown.lower(),
        "chart_human_label_present": "cued chart point-value reading" in markdown,
    }
    audit = {
        "schema_version": "blind-gains.seed1-visual-evidence-ranking-independent-audit.v1",
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "stored_metric_mismatches": stored_metric_mismatches,
        "effect_summary_mismatches": effect_summary_mismatches,
        "recomputed_primary": recomputed_primary,
        "result_json_sha256": _sha256(Path(args.result_json)),
        "result_markdown_sha256": _sha256(Path(args.result_markdown)),
        "config_sha256": _sha256(Path(args.config)),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))
    if audit["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
