#!/usr/bin/env python3
"""Finalizer for the registered B1 trained-checkpoint scoring.

Implements docs/registered_b1_trained_v1.md: per model x intervention type
pair/member rates against the pinned base rates, with the same single-gold
scoring for consistency pairs used in the base calibration, and the
pre-committed readings.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.finalize_b1_calibration_batch import single_gold_correct

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
TYPES = ("fact_read", "chained_premise", "binding_swap", "distractor_only", "style_twin", "prior_conflict")
MODELS = ("a1_seed1_step100", "a1_seed2_step100", "a2b_seed1_step100", "a3_seed1_step100")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--markdown-output", required=True)
    args = parser.parse_args()
    for path in (Path(args.json_output), Path(args.markdown_output)):
        if path.exists():
            raise FileExistsError("refusing to overwrite B1 trained artifacts")

    manifest_path = ROOT / "data/b1_geometry_track_v1/manifest.jsonl"
    batch = {str(row["pair_id"]): row for row in _read_jsonl(manifest_path)}
    base_report = json.loads((ROOT / "reports/geometry_track_prototype_v1.json").read_text(encoding="utf-8"))
    if base_report["declared_batch_sha256"] != _sha256(manifest_path):
        raise ValueError("batch hash differs from the base calibration")
    base_table = base_report["per_intervention"]

    by_type: dict[str, list[str]] = defaultdict(list)
    for pair_id, row in batch.items():
        by_type[str(row["intervention_type"])].append(pair_id)

    results: dict[str, Any] = {}
    evidence = []
    for model in MODELS:
        matches = sorted(glob.glob(str(ROOT / f"experiments/runs/b1_trained_{model}_real_an12_*")))
        if len(matches) != 1:
            raise ValueError(f"expected one cell for {model}, found {len(matches)}")
        run_dir = Path(matches[0])
        rows = {str(r["pair_id"]): r for r in _read_jsonl(run_dir / "predictions.jsonl")}
        if len(rows) != 100:
            raise ValueError(f"row count mismatch for {model}: {len(rows)}")
        for pair_id, meta in batch.items():
            if not meta.get("answers_equal"):
                continue
            gold = str(meta["answer_a"])
            scored = rows[pair_id]
            scored["correct_a"] = single_gold_correct(str(scored.get("prediction_a", "")), gold)
            scored["correct_b"] = single_gold_correct(str(scored.get("prediction_b", "")), gold)
            scored["pair_correct"] = scored["correct_a"] and scored["correct_b"]
        entry: dict[str, Any] = {}
        for itype in TYPES:
            ids = sorted(by_type[itype])
            pair = sum(bool(rows[p]["pair_correct"]) for p in ids) / len(ids)
            member = sum(
                float(bool(rows[p][f"correct_{side}"])) for p in ids for side in ("a", "b")
            ) / (2 * len(ids))
            entry[itype] = {
                "pairs": len(ids),
                "pair_correct": pair,
                "member_correct": member,
                "base_pair_correct": base_table[itype]["real_pair_correct"],
                "delta_pair_vs_base": pair - base_table[itype]["real_pair_correct"],
                "base_member_correct": base_table[itype]["real_member_correct"],
                "delta_member_vs_base": member - base_table[itype]["real_member_correct"],
            }
        results[model] = entry
        evidence.append({"model": model, "run_dir": str(run_dir.relative_to(ROOT)),
                         "predictions_sha256": _sha256(run_dir / "predictions.jsonl")})

    a1 = [results[m] for m in ("a1_seed1_step100", "a1_seed2_step100")]
    fact_up = all(e["fact_read"]["delta_pair_vs_base"] > 0 for e in a1)
    invariance_down = any(
        e[t]["delta_pair_vs_base"] < 0 for e in a1 for t in ("distractor_only", "style_twin")
    )
    chained_floor = all(
        results[m]["chained_premise"]["pair_correct"] == 0.0 for m in MODELS
    )
    if chained_floor:
        chained_reading = "c_chained_construct_not_discriminative_at_3b"
    else:
        chained_reading = "chained_construct_discriminative"
    if fact_up and not invariance_down:
        reading = "a_fact_extraction_improves_without_invariance_cost"
    elif fact_up and invariance_down:
        reading = "b_fact_extraction_invariance_tradeoff"
    else:
        reading = "no_registered_branch_fact_read_not_improved_in_both_seeds"

    result = {
        "schema_version": "blind-gains.b1-trained-scoring.v1",
        "registration": "docs/registered_b1_trained_v1.md",
        "batch_sha256": base_report["declared_batch_sha256"],
        "registered_reading": reading,
        "chained_premise_reading": chained_reading,
        "per_model": results,
        "provenance": {"cells": evidence, "base_pinned_from": "reports/geometry_track_prototype_v1.json"},
    }

    lines = [
        "# B1 trained-checkpoint scoring (v1)",
        "",
        "Registered: `docs/registered_b1_trained_v1.md`. Declared 100-pair batch",
        "unchanged; base rates pinned from the base calibration, not re-measured;",
        "consistency pairs scored single-gold as in that calibration.",
        "",
        f"**Registered reading: {reading}**",
        f"Chained construct: {chained_reading}",
        "",
        "## Pair-correct by intervention type (delta vs base in parentheses)",
        "",
        "| intervention | pairs | base | A1 s1 | A1 s2 | A2b s1 | A3 s1 |",
        "|---|---|---|---|---|---|---|",
    ]
    for itype in TYPES:
        cells = []
        for model in MODELS:
            entry = results[model][itype]
            cells.append(f"{entry['pair_correct']:.3f} ({entry['delta_pair_vs_base']:+.3f})")
        base_rate = base_table[itype]["real_pair_correct"]
        lines.append(
            f"| {itype} | {results[MODELS[0]][itype]['pairs']} | {base_rate:.3f} | " + " | ".join(cells) + " |"
        )
    lines += [
        "",
        "## Member-correct by intervention type",
        "",
        "| intervention | base | A1 s1 | A1 s2 | A2b s1 | A3 s1 |",
        "|---|---|---|---|---|---|",
    ]
    for itype in TYPES:
        cells = [f"{results[m][itype]['member_correct']:.3f}" for m in MODELS]
        lines.append(f"| {itype} | {base_table[itype]['real_member_correct']:.3f} | " + " | ".join(cells) + " |")
    lines += ["", "No interpretation beyond the registered readings.", ""]

    Path(args.json_output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    Path(args.markdown_output).write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"reading": reading, "chained": chained_reading}, sort_keys=True))


if __name__ == "__main__":
    main()
