#!/usr/bin/env python3
"""HB P2.3 readout: attacker-gate verdicts (pooled + per-template), blind
floors (gray / no_image member accuracy per cell x layer), and the leak
verification tabulation, in one numbers-only report.

Inputs are existing artifacts; this script computes nothing new except blind
member accuracies re-derived from the blind-sweep predictions. Registered
attacker criterion (docs/registered_hier_benchmark_v1.md, premise-v2 lineage):
folded gate statistic <= 0.55 point AND folded CI upper <= 0.62, per attacker,
pooled and per template. Refuses to overwrite outputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = ("hier_coord_v1", "hier_chart_v1")
LAYERS = ("l1", "l2", "l3", "probe")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blind_accuracies(run_dir: Path) -> dict[str, float]:
    out: dict[str, float] = {}
    for cell_dir in sorted(run_dir.iterdir()):
        pred = cell_dir / "predictions.jsonl"
        if not cell_dir.is_dir() or not pred.exists():
            continue
        rows = [json.loads(l) for l in pred.read_text().splitlines() if l.strip()]
        if not rows:
            raise ValueError(f"empty predictions: {pred}")
        hits = sum(bool(r["correct_a"]) + bool(r["correct_b"]) for r in rows)
        out[cell_dir.name] = round(hits / (2 * len(rows)), 4)
    if not out:
        raise ValueError(f"no prediction cells under {run_dir}")
    return out


def attacker_tables(gate: dict) -> dict:
    rows = []
    for attacker, entry in sorted(gate["attacks"].items()):
        scopes = {"pooled": entry["pooled"], **entry["per_template"]}
        for scope, stats in sorted(scopes.items()):
            folded = float(stats["gate_statistic"])
            ci = stats["pair_bootstrap_ci_95"]
            rows.append({
                "attacker": attacker,
                "scope": scope,
                "folded_gate_statistic": folded,
                "folded_ci_95": [float(ci[0]), float(ci[1])],
                "directed_oof_auc": float(stats["directed_oof_auc"]),
                "unfolded_ci_95": [float(v) for v in
                                   stats["directed_oof_auc_unfolded_ci_95"]],
                "n_pairs": int(stats["n_pairs"]),
                "point_over_0_55": folded > 0.55,
                "ci_upper_over_0_62": float(ci[1]) > 0.62,
            })
    return {"gate": gate["gate"], "rows": rows,
            "n_pairs": gate["n_pairs"], "split": gate.get("split")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attacker-gate", nargs=2, type=Path, default=[
        ROOT / "reports/hier_p2_attacker_gate_hier_coord_v1.json",
        ROOT / "reports/hier_p2_attacker_gate_hier_chart_v1.json"])
    parser.add_argument("--blind-gray-run", type=Path, required=True)
    parser.add_argument("--blind-no-image-run", type=Path, required=True)
    parser.add_argument("--leak-verification", type=Path,
                        default=ROOT / "reports/hier_p2_leak_verification_v1.json")
    parser.add_argument("--output-json", type=Path,
                        default=ROOT / "reports/hier_p23_readout_v1.json")
    parser.add_argument("--output-md", type=Path,
                        default=ROOT / "reports/hier_p23_readout_v1.md")
    args = parser.parse_args()
    for out in (args.output_json, args.output_md):
        if out.exists():
            raise FileExistsError(out)

    attacker = {}
    for path in args.attacker_gate:
        gate = json.loads(path.read_text())
        family = next(f for f in FAMILIES if f in path.name)
        attacker[family] = attacker_tables(gate)
        attacker[family]["source"] = {"path": str(path),
                                      "sha256": sha256_file(path)}
    blind = {"gray": blind_accuracies(args.blind_gray_run),
             "no_image": blind_accuracies(args.blind_no_image_run)}
    leak = json.loads(args.leak_verification.read_text())

    payload = {
        "schema_version": "blind-gains.hier-p23-readout.v1",
        "criterion": "folded gate statistic <= 0.55 point AND folded CI upper "
                     "<= 0.62, per attacker, pooled and per template",
        "attacker_gates": attacker,
        "blind_floors": {
            "gray_run": str(args.blind_gray_run),
            "no_image_run": str(args.blind_no_image_run),
            "member_accuracy": blind,
        },
        "leak_verification": leak,
    }
    args.output_json.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = ["# HB P2.3 readout — attacker gates, blind floors, leak verification",
             "",
             f"Criterion: {payload['criterion']}.", ""]
    for family in FAMILIES:
        entry = attacker[family]
        lines += [f"## Attacker gate — `{family}`", "",
                  f"Gate status: **{entry['gate']['status']}** — checks "
                  f"`{json.dumps(entry['gate']['checks'], sort_keys=True)}`; "
                  f"point failures: {entry['gate'].get('point_failures', [])}.",
                  "",
                  "| attacker | scope | folded stat | folded CI95 | unfolded AUC "
                  "| unfolded CI95 | n pairs | flags |",
                  "|---|---|---|---|---|---|---|---|"]
        for row in entry["rows"]:
            flags = ("point>0.55 " if row["point_over_0_55"] else "") + \
                    ("ci_up>0.62" if row["ci_upper_over_0_62"] else "")
            lines.append(
                f"| {row['attacker']} | {row['scope']} | "
                f"{row['folded_gate_statistic']:.4f} | "
                f"[{row['folded_ci_95'][0]:.4f}, {row['folded_ci_95'][1]:.4f}] | "
                f"{row['directed_oof_auc']:.4f} | "
                f"[{row['unfolded_ci_95'][0]:.4f}, {row['unfolded_ci_95'][1]:.4f}] | "
                f"{row['n_pairs']} | {flags.strip() or '—'} |")
        lines.append("")
    lines += ["## Blind floors (member accuracy, base 3B)", "",
              "| cell | gray | no_image |", "|---|---|---|"]
    for cell in sorted(blind["gray"]):
        lines.append(f"| {cell} | {blind['gray'][cell]:.4f} | "
                     f"{blind['no_image'].get(cell, float('nan')):.4f} |")
    lines += ["", "## Leak verification (edit direction + PNG size, causal pairs)",
              "",
              "| family | cell | role | n | value-delta neg | pos | multi-field "
              "| png edited>base | edited<base | mean delta (B) |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for family, cells in sorted(leak["cells"].items()):
        for cell, roles in sorted(cells.items()):
            for role, s in sorted(roles.items()):
                lines.append(
                    f"| {family} | {cell} | {role} | {s['n']} | "
                    f"{s['value_delta_neg']} | {s['value_delta_pos']} | "
                    f"{s['multi_field_edits']} | {s['png_size_edited_gt_base']} | "
                    f"{s['png_size_edited_lt_base']} | "
                    f"{s['png_size_mean_delta_bytes']:+.0f} |")
    lines.append("")
    args.output_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.output_json} and {args.output_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
