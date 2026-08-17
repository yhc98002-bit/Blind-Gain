#!/usr/bin/env python3
"""Diagnostic blind-channel readout (descriptive, no gates): the full blind
open-form matrix (models x gray/no_image member accuracy per cell) and the
blind candidate-ranking floors (no_image MRR/top-1 per config). Run under the
PI's 2026-08-17 utilization directive; registered instruments, locked
decoding; numbers only."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def member_accuracy(run_dir: Path) -> dict[str, float]:
    out = {}
    for cell_dir in sorted(run_dir.iterdir()):
        pred = cell_dir / "predictions.jsonl"
        if not cell_dir.is_dir() or not pred.exists():
            continue
        rows = [json.loads(l) for l in pred.read_text().splitlines() if l.strip()]
        hits = sum(bool(r["correct_a"]) + bool(r["correct_b"]) for r in rows)
        out[cell_dir.name] = round(hits / (2 * len(rows)), 4)
    if not out:
        raise ValueError(f"no cells under {run_dir}")
    return out


def ranking_floor(run_dir: Path) -> dict[str, dict]:
    out = {}
    for path in sorted(run_dir.glob("*.jsonl")):
        rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
        if not rows or "candidate_pair_mrr" not in rows[0]:
            continue
        out[path.stem] = {
            "n_pairs": len(rows),
            "mean_pair_mrr": round(sum(r["candidate_pair_mrr"] for r in rows)
                                   / len(rows), 4),
            "top1_rate": round(sum(bool(r["candidate_pair_top1"]) for r in rows)
                               / len(rows), 4)}
    if not out:
        raise ValueError(f"no ranking outputs under {run_dir}")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openform", action="append", nargs=3,
                        metavar=("MODEL", "MODE", "RUN_DIR"), default=[])
    parser.add_argument("--ranking", action="append", nargs=2,
                        metavar=("MODEL", "RUN_DIR"), default=[])
    parser.add_argument("--output-json", type=Path,
                        default=ROOT / "reports/hier_blind_diagnostics_v1.json")
    parser.add_argument("--output-md", type=Path,
                        default=ROOT / "reports/hier_blind_diagnostics_v1.md")
    args = parser.parse_args()
    for out in (args.output_json, args.output_md):
        if out.exists():
            raise FileExistsError(out)

    openform = {}
    for model, mode, run_dir in args.openform:
        openform.setdefault(model, {})[mode] = {
            "run_dir": run_dir, "member_accuracy": member_accuracy(Path(run_dir))}
    ranking = {model: {"run_dir": run_dir,
                       "cells": ranking_floor(Path(run_dir))}
               for model, run_dir in args.ranking}
    payload = {"schema_version": "blind-gains.hier-blind-diagnostics.v1",
               "status": "diagnostic (descriptive; no registered gate)",
               "openform_blind_matrix": openform,
               "ranking_no_image_floors": ranking}
    args.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True)
                                + "\n", encoding="utf-8")

    lines = ["# Hier blind-channel diagnostics (descriptive)", ""]
    if openform:
        cells = sorted(next(iter(openform.values()))
                       [next(iter(next(iter(openform.values()))))]
                       ["member_accuracy"])
        header = []
        for model in sorted(openform):
            for mode in sorted(openform[model]):
                header.append(f"{model}/{mode}")
        lines += ["## Open-form blind member accuracy", "",
                  "| cell | " + " | ".join(header) + " |",
                  "|---|" + "---|" * len(header)]
        for cell in cells:
            values = []
            for model in sorted(openform):
                for mode in sorted(openform[model]):
                    values.append(
                        f"{openform[model][mode]['member_accuracy'].get(cell, float('nan')):.4f}")
            lines.append(f"| {cell} | " + " | ".join(values) + " |")
        lines.append("")
    if ranking:
        lines += ["## Candidate-ranking no_image floors (mean MRR / top-1)", "",
                  "| config | " + " | ".join(sorted(ranking)) + " |",
                  "|---|" + "---|" * len(ranking)]
        configs = sorted(next(iter(ranking.values()))["cells"])
        for config in configs:
            values = []
            for model in sorted(ranking):
                s = ranking[model]["cells"].get(config)
                values.append(f"{s['mean_pair_mrr']:.4f} ({s['top1_rate']:.4f})"
                              if s else "—")
            lines.append(f"| {config} | " + " | ".join(values) + " |")
        lines.append("")
    args.output_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.output_json} and {args.output_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
