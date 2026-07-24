#!/usr/bin/env python3
"""Fail-closed finalizer for the registered X2 hard-negative ranking.

Verifies the three v2 cells and the three pinned v1 real-condition cells,
reports old-vs-new pair-success side by side on the 600 geometry pairs, and
applies the pre-committed interpretation ladder of
docs/registered_x2_ladder_v1.md mechanically to the base-model against-set
number. No interpretation beyond the ladder branch enters the output.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.eval.visual_evidence_ranking import SCORER_VERSION, bootstrap_mean_ci

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
MODELS = ("base", "a1_step60", "a1_step100")
TEMPLATE = "coordinate_register_twenty_point_x_v02"
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


def find_one(pattern: str) -> Path:
    complete = []
    for match in sorted(glob.glob(str(ROOT / pattern))):
        manifest = Path(match) / "run_manifest.json"
        if manifest.is_file():
            payload = _read_json(manifest)
            if payload.get("status") == "complete" and payload.get("exit_code") == 0:
                complete.append(Path(match))
    if len(complete) != 1:
        raise ValueError(f"expected one complete run for {pattern}, found {len(complete)}")
    return complete[0]


def verify_cell(
    run_dir: Path,
    *,
    config: dict[str, Any],
    config_hash: str,
    registry_by_pair: dict[str, dict[str, Any]],
    expected_pairs: set[str],
    expected_rows: int,
) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    manifest = _read_json(run_dir / "run_manifest.json")
    model = str(manifest["model_key"])
    if manifest.get("status") != "complete" or manifest.get("exit_code") != 0:
        raise ValueError(f"cell not complete: {run_dir}")
    if manifest.get("limit") is not None:
        raise ValueError(f"limited smoke run cannot enter results: {run_dir}")
    if manifest.get("config_hash") != config_hash:
        raise ValueError(f"config hash mismatch: {run_dir}")
    if manifest.get("model_index_sha256") != config["models"][model]["model_index_sha256"]:
        raise ValueError(f"model hash mismatch: {run_dir}")
    if manifest.get("scorer_version") != SCORER_VERSION:
        raise ValueError(f"scorer version mismatch: {run_dir}")
    rows = _read_jsonl(run_dir / "scores.jsonl")
    if len(rows) != expected_rows:
        raise ValueError(f"row count mismatch: {run_dir}")
    observed = {str(row["pair_id"]) for row in rows}
    if observed != expected_pairs or len(observed) != len(rows):
        raise ValueError(f"pair identity mismatch: {run_dir}")
    if any(
        row.get("candidate_set_sha256")
        != registry_by_pair[str(row["pair_id"])]["candidate_set_sha256"]
        for row in rows
        if str(row["pair_id"]) in registry_by_pair
    ):
        raise ValueError(f"candidate-set hash mismatch: {run_dir}")
    evidence = {
        "run_dir": str(run_dir.relative_to(ROOT)),
        "manifest_sha256": _sha256(run_dir / "run_manifest.json"),
        "output_sha256": _sha256(run_dir / "scores.jsonl"),
        "model_key": model,
        "rows": len(rows),
    }
    return model, rows, evidence


def rate(values: list[bool]) -> dict[str, Any]:
    floats = [float(v) for v in values]
    lower, upper = bootstrap_mean_ci(floats, n_boot=N_BOOT, seed=BOOT_SEED)
    return {"n_pairs": len(floats), "rate": sum(floats) / len(floats), "ci95": [lower, upper]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--markdown-output", required=True)
    parser.add_argument("--audit-output", required=True)
    args = parser.parse_args()
    outputs = [Path(args.json_output), Path(args.markdown_output), Path(args.audit_output)]
    if any(path.exists() for path in outputs):
        raise FileExistsError("refusing to overwrite X2 result artifacts")

    x2_config_path = ROOT / "configs/eval/x2_hard_negative_ranking_v1.json"
    seed1_config_path = ROOT / "configs/eval/seed1_visual_evidence_ranking_v1.json"
    x2_config = _read_json(x2_config_path)
    seed1_config = _read_json(seed1_config_path)
    x2_hash = _sha256(x2_config_path)
    seed1_hash = _sha256(seed1_config_path)

    v2_registry_path = ROOT / str(x2_config["candidate_registry"]["path"])
    if _sha256(v2_registry_path) != str(x2_config["candidate_registry"]["sha256"]):
        raise ValueError("frozen v2 registry hash mismatch on disk")
    v2_registry = {str(row["pair_id"]): row for row in _read_jsonl(v2_registry_path)}
    v2_pairs = set(v2_registry)
    v1_registry_path = ROOT / str(seed1_config["candidate_registry"]["path"])
    v1_registry = {
        str(row["pair_id"]): row
        for row in _read_jsonl(v1_registry_path)
        if row["template_id"] == TEMPLATE
    }
    if set(v1_registry) != v2_pairs:
        raise ValueError("v1/v2 geometry pair identity mismatch")

    v2_rows: dict[str, list[dict[str, Any]]] = {}
    v1_rows: dict[str, list[dict[str, Any]]] = {}
    evidence: list[dict[str, Any]] = []
    for model in MODELS:
        run_dir = find_one(
            f"experiments/runs/d1_visual_evidence_{model}_real_*_x2_ranking_matrix_queue_login_20260724T172219Z"
        )
        key, rows, cell_evidence = verify_cell(
            run_dir,
            config=x2_config,
            config_hash=x2_hash,
            registry_by_pair=v2_registry,
            expected_pairs=v2_pairs,
            expected_rows=600,
        )
        cell_evidence["registry"] = "v2_structured_negatives"
        v2_rows[key] = rows
        evidence.append(cell_evidence)

        v1_dir = find_one(
            f"experiments/runs/d1_visual_evidence_{model}_real_*_d1_visual_evidence_matrix_queue_login_20260717T175951Z"
        )
        v1_registry_full = {
            str(row["pair_id"]): row for row in _read_jsonl(v1_registry_path)
        }
        key1, rows1, evidence1 = verify_cell(
            v1_dir,
            config=seed1_config,
            config_hash=seed1_hash,
            registry_by_pair=v1_registry_full,
            expected_pairs=set(v1_registry_full),
            expected_rows=1200,
        )
        evidence1["registry"] = "v1_pinned"
        v1_rows[key1] = [row for row in rows1 if row["template_id"] == TEMPLATE]
        evidence.append(evidence1)

    comparison: dict[str, Any] = {}
    margin_consistency: dict[str, Any] = {}
    for model in MODELS:
        v2_by_pair = {str(row["pair_id"]): row for row in v2_rows[model]}
        v1_by_pair = {str(row["pair_id"]): row for row in v1_rows[model]}
        ordered = sorted(v2_pairs)
        comparison[model] = {
            "v1_margin_pair_success": rate([bool(v1_by_pair[p]["pair_success"]) for p in ordered]),
            "v2_margin_pair_success": rate([bool(v2_by_pair[p]["pair_success"]) for p in ordered]),
            "v1_against_set_pair_success": rate(
                [bool(v1_by_pair[p]["candidate_pair_top1"]) for p in ordered]
            ),
            "v2_against_set_pair_success": rate(
                [bool(v2_by_pair[p]["candidate_pair_top1"]) for p in ordered]
            ),
        }
        disagreements = sum(
            1
            for p in ordered
            if bool(v1_by_pair[p]["pair_success"]) != bool(v2_by_pair[p]["pair_success"])
        )
        margin_consistency[model] = {
            "margin_pair_success_disagreements": disagreements,
            "note": "the golds-only margin statistic is candidate-set-invariant by construction; disagreements measure recomputation determinism only",
        }

    base_metric = comparison["base"]["v2_against_set_pair_success"]["rate"]
    if base_metric >= 0.75:
        branch = "top_branch_full_strength_co_headline"
    elif base_metric >= 0.55:
        branch = "mid_form_substantial_latent_preference_partially_candidate_sensitive"
    else:
        branch = "candidate_set_structure_realization_gap_measurement_methods_finding"

    result = {
        "schema_version": "blind-gains.x2-hard-negative-results.v1",
        "status": "complete",
        "registration": "docs/registered_x2_ladder_v1.md",
        "scorer_version": SCORER_VERSION,
        "template": TEMPLATE,
        "ladder_metric_definition": "against-set pair-success: both members rank their own gold first within the frozen structured negative set (candidate_pair_top1)",
        "base_ladder_metric": comparison["base"]["v2_against_set_pair_success"],
        "ladder_branch": branch,
        "comparison": comparison,
        "margin_invariance": margin_consistency,
        "provenance": {
            "x2_config_sha256": x2_hash,
            "seed1_config_sha256": seed1_hash,
            "v2_registry_sha256": str(x2_config["candidate_registry"]["sha256"]),
            "cells": sorted(evidence, key=lambda item: (item["registry"], item["model_key"])),
        },
    }

    lines = [
        "# X2 hard-negative ranking results (v1)",
        "",
        "Registered ladder: `docs/registered_x2_ladder_v1.md`. Layer: candidate-evidence",
        "ranking. 600 geometry pairs, frozen structured negative sets",
        "(`data/fliptrack_r19_hard_negative_candidates_v2.jsonl`). The v2 against-set",
        "number supersedes the corresponding v1 number in all downstream text.",
        "",
        f"- Ladder metric: {result['ladder_metric_definition']}",
        "- The golds-only margin statistic is candidate-set-invariant by construction",
        "  and is reported for continuity only.",
        "",
        "## Old vs new pair-success (geometry template, 600 pairs)",
        "",
        "| model | v1 margin pair-success | v2 margin pair-success | v1 against-set (14 candidates) | v2 against-set (structured, 4-8) |",
        "|---|---|---|---|---|",
    ]
    for model in MODELS:
        entry = comparison[model]
        lines.append(
            f"| {model} | {entry['v1_margin_pair_success']['rate']:.4f}"
            f" | {entry['v2_margin_pair_success']['rate']:.4f}"
            f" | {entry['v1_against_set_pair_success']['rate']:.4f}"
            f" [{entry['v1_against_set_pair_success']['ci95'][0]:.4f}, {entry['v1_against_set_pair_success']['ci95'][1]:.4f}]"
            f" | {entry['v2_against_set_pair_success']['rate']:.4f}"
            f" [{entry['v2_against_set_pair_success']['ci95'][0]:.4f}, {entry['v2_against_set_pair_success']['ci95'][1]:.4f}] |"
        )
    lines += [
        "",
        "## Registered ladder application (base model, v2 against-set pair-success)",
        "",
        f"- Measured: {base_metric:.4f}"
        f" [{comparison['base']['v2_against_set_pair_success']['ci95'][0]:.4f},"
        f" {comparison['base']['v2_against_set_pair_success']['ci95'][1]:.4f}]",
        f"- Ladder branch (mechanical): **{branch}**",
        "",
        "Whichever branch obtains ships without renegotiation; branch text is defined",
        "in the registration and is not restated here.",
        "",
    ]

    for path in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
    Path(args.json_output).write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    Path(args.markdown_output).write_text("\n".join(lines), encoding="utf-8")
    audit = {
        "schema_version": "blind-gains.x2-hard-negative-audit.v1",
        "status": "pass",
        "cells_verified": len(evidence),
        "machine_output_sha256": _sha256(Path(args.json_output)),
        "markdown_output_sha256": _sha256(Path(args.markdown_output)),
        "performance_values_opened": True,
        "ladder_branch": branch,
    }
    Path(args.audit_output).write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({**audit, "base_v2_against_set": base_metric}, sort_keys=True))


if __name__ == "__main__":
    main()
