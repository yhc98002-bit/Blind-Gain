#!/usr/bin/env python3
"""HB P2.2 — informativeness-gate readout (registered_hier_benchmark_v1.md §7
+ Amendment A2; gates quoted from EXPERIMENT_TODO HB.7 and scored on BASE 3B
ONLY). Reports pass/fail per knob cell; no knob iteration beyond the
registered grid. All four models' per-layer accuracies are reported
descriptively; the gates read the base-3B columns.

Gate composition (A2): per layer, MEMBER accuracy pooled over the
target-stable + invariance rows — a composition held constant across the
three layers. L3 target-switch member accuracy is reported separately and
never averaged in.

Registered gates, scored per cell on base 3B:
  monotone   L1 > L2 > L3
  L1 band    L1 ∈ [0.60, 0.95]
  L2 band    L2 ∈ [0.20, 0.80]
  L3 floor   L3 ≥ 0.05 in at least one cell per family (a FAMILY-level gate)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = {
    "hier_coord_v1": ("n8", "n12", "n20"),
    "hier_chart_v1": ("s5_low", "s5_high", "s9_low", "s9_high"),
}
LAYERS = ("l1", "l2", "l3")
GATE_MODEL = "base3b"


def member_accuracy(rows: list[dict], roles: set[str]) -> tuple[float, int]:
    hits = total = 0
    for row in rows:
        if row.get("role") not in roles:
            continue
        for side in ("a", "b"):
            total += 1
            if row.get(f"correct_{side}"):
                hits += 1
    if total == 0:
        raise AssertionError("no rows for the gate composition")
    return hits / total, total


def load_predictions(run_dir: Path, family: str, cell: str, layer: str) -> list[dict]:
    path = run_dir / f"{family}_{cell}_{layer}" / "predictions.jsonl"
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", action="append", required=True,
                        metavar="MODEL_KEY=RUN_DIR",
                        help="open-form sweep run dir per model (repeat)")
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    if args.json_output.exists() or args.markdown_output.exists():
        raise FileExistsError("refusing to overwrite an existing gate readout")

    run_dirs: dict[str, Path] = {}
    for spec in args.run_dir:
        key, _, path = spec.partition("=")
        run_dirs[key] = ROOT / path
    if GATE_MODEL not in run_dirs:
        raise SystemExit(f"--run-dir must include {GATE_MODEL}=...")

    cells: dict[str, dict] = {}
    for family, family_cells in FAMILIES.items():
        for cell in family_cells:
            entry: dict = {"per_model": {}}
            for model_key, run_dir in sorted(run_dirs.items()):
                layers = {}
                for layer in LAYERS:
                    rows = load_predictions(run_dir, family, cell, layer)
                    gate_acc, gate_n = member_accuracy(
                        rows, {"target_stable", "invariance"})
                    layers[layer] = {
                        "gate_member_accuracy": gate_acc,
                        "gate_n_members": gate_n,
                    }
                    if layer == "l3":
                        switch_acc, switch_n = member_accuracy(
                            rows, {"target_switch"})
                        layers[layer]["switch_member_accuracy"] = switch_acc
                        layers[layer]["switch_n_members"] = switch_n
                probe_rows = load_predictions(run_dir, family, cell, "probe")
                probe_acc, probe_n = member_accuracy(
                    probe_rows, {"target_switch", "target_stable", "invariance"})
                entry["per_model"][model_key] = {
                    **layers,
                    "probe": {"member_accuracy": probe_acc, "n_members": probe_n},
                }
            base = entry["per_model"][GATE_MODEL]
            l1 = base["l1"]["gate_member_accuracy"]
            l2 = base["l2"]["gate_member_accuracy"]
            l3 = base["l3"]["gate_member_accuracy"]
            entry["gates_base3b"] = {
                "l1": l1, "l2": l2, "l3": l3,
                "monotone_l1_gt_l2_gt_l3": l1 > l2 > l3,
                "l1_in_band_060_095": 0.60 <= l1 <= 0.95,
                "l2_in_band_020_080": 0.20 <= l2 <= 0.80,
                "l3_at_least_005": l3 >= 0.05,
            }
            cells[f"{family}/{cell}"] = entry

    family_gates = {}
    for family, family_cells in FAMILIES.items():
        family_gates[family] = {
            "l3_floor_in_at_least_one_cell": any(
                cells[f"{family}/{cell}"]["gates_base3b"]["l3_at_least_005"]
                for cell in family_cells),
            "cells_passing_all_cell_gates": [
                cell for cell in family_cells
                if all(v for k, v in cells[f"{family}/{cell}"]["gates_base3b"].items()
                       if isinstance(v, bool))],
        }

    payload = {
        "schema_version": "blind-gains.hier-p2-gate-readout.v1",
        "registration": "docs/registered_hier_benchmark_v1.md §7 + A2",
        "gate_model": GATE_MODEL,
        "gate_composition": "member accuracy over target_stable+invariance rows",
        "run_dirs": {k: str(v.relative_to(ROOT)) for k, v in run_dirs.items()},
        "cells": cells,
        "family_gates": family_gates,
    }
    args.json_output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                                encoding="utf-8")

    lines = [
        "# HB P2.2 — informativeness gates (base 3B; stable+invariance member accuracy)",
        "",
        "| cell | L1 | L2 | L3 | monotone | L1 band | L2 band | L3≥0.05 | L3 switch (sep.) |",
        "|---|---:|---:|---:|---|---|---|---|---:|",
    ]
    for cell_key, entry in sorted(cells.items()):
        gates = entry["gates_base3b"]
        base = entry["per_model"][GATE_MODEL]
        lines.append(
            f"| {cell_key} | {gates['l1']:.4f} | {gates['l2']:.4f} | "
            f"{gates['l3']:.4f} | "
            f"{'PASS' if gates['monotone_l1_gt_l2_gt_l3'] else '**FAIL**'} | "
            f"{'PASS' if gates['l1_in_band_060_095'] else '**FAIL**'} | "
            f"{'PASS' if gates['l2_in_band_020_080'] else '**FAIL**'} | "
            f"{'PASS' if gates['l3_at_least_005'] else '**FAIL**'} | "
            f"{base['l3']['switch_member_accuracy']:.4f} |")
    lines += ["", "## Family-level L3 floor (≥ 0.05 in at least one cell)", ""]
    for family, gates in family_gates.items():
        lines.append(
            f"- {family}: "
            f"{'PASS' if gates['l3_floor_in_at_least_one_cell'] else '**FAIL**'}; "
            f"cells passing every cell-level gate: "
            f"{gates['cells_passing_all_cell_gates'] or 'none'}")
    lines += ["", "Per-model per-layer accuracies (descriptive) are in the JSON.", ""]
    args.markdown_output.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(family_gates, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
