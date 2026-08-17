#!/usr/bin/env python3
"""HB P2.3 caption-stress readout: per family / cell / role member accuracy of
the caption-QA channel (72B question-blind captions -> base-3B text QA) next
to the blind floors. Numbers only; HB has no registered caption ceiling yet
(P3-freeze prerequisite), so no verdict column is emitted — floors and deltas
are reported as measured.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CELLS = {"hier_coord_v1": ("n8", "n12", "n20"),
         "hier_chart_v1": ("s5_low", "s5_high", "s9_low", "s9_high")}
ROLES = ("target_switch", "target_stable")


def classify(pair_id: str, family: str) -> tuple[str, str]:
    cell = next((c for c in CELLS[family] if f"_{c}_" in pair_id), None)
    role = next((r for r in ROLES if r in pair_id), None)
    if cell is None or role is None:
        raise ValueError(f"unclassifiable pair_id for {family}: {pair_id}")
    return cell, role


def member_hits(row: dict) -> tuple[int, int]:
    for a_key, b_key in (("correct_a", "correct_b"),
                         ("member_correct_a", "member_correct_b"),
                         ("lenient_correct_a", "lenient_correct_b")):
        if a_key in row and b_key in row:
            return int(bool(row[a_key])) + int(bool(row[b_key])), 2
    raise KeyError(f"no member-correct fields in row; keys={sorted(row)[:20]}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qa-run", type=Path, required=True,
                        help="dir holding {family}_predictions.jsonl + "
                             "{family}_metrics.json")
    parser.add_argument("--caption-run", type=Path, required=True)
    parser.add_argument("--p23-readout", type=Path,
                        default=ROOT / "reports/hier_p23_readout_v1.json")
    parser.add_argument("--output-json", type=Path,
                        default=ROOT / "reports/hier_caption_stress_readout_v1.json")
    parser.add_argument("--output-md", type=Path,
                        default=ROOT / "reports/hier_caption_stress_readout_v1.md")
    args = parser.parse_args()
    for out in (args.output_json, args.output_md):
        if out.exists():
            raise FileExistsError(out)

    blind = json.loads(args.p23_readout.read_text())["blind_floors"]["member_accuracy"]
    families = {}
    for family in CELLS:
        pred_path = args.qa_run / f"{family}_predictions.jsonl"
        rows = [json.loads(l) for l in pred_path.read_text().splitlines()
                if l.strip()]
        if not rows:
            raise ValueError(f"empty predictions: {pred_path}")
        agg: dict[tuple[str, str], list[int]] = {}
        total = [0, 0]
        for row in rows:
            cell, role = classify(str(row["pair_id"]), family)
            hits, n = member_hits(row)
            bucket = agg.setdefault((cell, role), [0, 0])
            bucket[0] += hits
            bucket[1] += n
            total[0] += hits
            total[1] += n
        metrics_path = args.qa_run / f"{family}_metrics.json"
        families[family] = {
            "n_pairs": len(rows),
            "member_accuracy": round(total[0] / total[1], 4),
            "per_cell_role": {
                f"{cell}/{role}": {"n_members": n, "member_accuracy":
                                   round(h / n, 4)}
                for (cell, role), (h, n) in sorted(agg.items())},
            "instrument_metrics": (json.loads(metrics_path.read_text())
                                   if metrics_path.exists() else None),
        }

    payload = {
        "schema_version": "blind-gains.hier-caption-stress-readout.v1",
        "caption_run": str(args.caption_run),
        "qa_run": str(args.qa_run),
        "captioner": "Qwen2.5-VL-72B-Instruct (question-blind, TP4)",
        "qa_model": "base 3B (text-only over caption pairs)",
        "registered_ceiling": None,
        "families": families,
        "blind_floors_l3": {
            fam: {cell: {"gray": blind["gray"].get(f"{fam}_{cell}_l3"),
                         "no_image": blind["no_image"].get(f"{fam}_{cell}_l3")}
                  for cell in CELLS[fam]} for fam in CELLS},
    }
    args.output_json.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = ["# HB P2.3 caption-stress readout (72B captions -> base-3B QA)",
             "",
             f"Caption run: `{args.caption_run}` · QA run: `{args.qa_run}`.",
             "No registered HB caption ceiling exists yet (P3-freeze "
             "prerequisite); numbers as measured.", ""]
    for family, entry in families.items():
        lines += [f"## `{family}` — caption member accuracy "
                  f"{entry['member_accuracy']:.4f} ({entry['n_pairs']} pairs)",
                  "",
                  "| cell/role | n members | caption member acc | blind gray L3 |",
                  "|---|---|---|---|"]
        for key, s in entry["per_cell_role"].items():
            cell = key.split("/")[0]
            gray = blind["gray"].get(f"{family}_{cell}_l3")
            gray_s = f"{gray:.4f}" if gray is not None else "—"
            lines.append(f"| {key} | {s['n_members']} | "
                         f"{s['member_accuracy']:.4f} | {gray_s} |")
        lines.append("")
    args.output_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.output_json} and {args.output_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
