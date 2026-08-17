#!/usr/bin/env python3
"""HB P2.1 candidate-ranking readout: per model x cell x layer mean pair MRR
and top-1 rate over the registered ranking configs (14 per model). Numbers
only. Refuses to overwrite outputs."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CELLS = {"hier_coord_v1": ("n8", "n12", "n20"),
         "hier_chart_v1": ("s5_low", "s5_high", "s9_low", "s9_high")}
LAYERS = ("l3", "l2")


def summarize(path: Path) -> dict:
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    if not rows:
        raise ValueError(f"empty ranking output: {path}")
    mrr = sum(float(r["candidate_pair_mrr"]) for r in rows) / len(rows)
    top1 = sum(bool(r["candidate_pair_top1"]) for r in rows) / len(rows)
    return {"n_pairs": len(rows), "mean_pair_mrr": round(mrr, 4),
            "top1_rate": round(top1, 4),
            "candidate_count": int(rows[0]["candidate_count"])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="append", nargs=2,
                        metavar=("MODEL_KEY", "RUN_DIR"), required=True)
    parser.add_argument("--output-json", type=Path,
                        default=ROOT / "reports/hier_p2_ranking_readout_v1.json")
    parser.add_argument("--output-md", type=Path,
                        default=ROOT / "reports/hier_p2_ranking_readout_v1.md")
    args = parser.parse_args()
    for out in (args.output_json, args.output_md):
        if out.exists():
            raise FileExistsError(out)

    models = {}
    for model_key, run_dir in args.run:
        run = Path(run_dir)
        manifest = json.loads((run / "run_manifest.json").read_text())
        if manifest["status"] != "complete":
            raise ValueError(f"{run} status is {manifest['status']}, not complete")
        cells = {}
        for family, family_cells in CELLS.items():
            for cell in family_cells:
                for layer in LAYERS:
                    name = f"{family}_{cell}_{layer}"
                    cells[name] = summarize(run / f"{name}.jsonl")
        models[model_key] = {"run_dir": str(run), "cells": cells}

    payload = {"schema_version": "blind-gains.hier-p2-ranking-readout.v1",
               "estimands": "mean candidate_pair_mrr + candidate_pair_top1 rate "
                            "per registered ranking config",
               "models": models}
    args.output_json.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    model_keys = [key for key, _ in args.run]
    lines = ["# HB P2.1 candidate-ranking readout", "",
             "Mean pair MRR (top-1 rate) per cell; candidate registries as "
             "registered.", ""]
    for layer in LAYERS:
        lines += [f"## Layer {layer.upper()}", "",
                  "| cell | " + " | ".join(model_keys) + " |",
                  "|---|" + "---|" * len(model_keys)]
        for family, family_cells in CELLS.items():
            for cell in family_cells:
                name = f"{family}_{cell}_{layer}"
                parts = []
                for key in model_keys:
                    s = models[key]["cells"][name]
                    parts.append(f"{s['mean_pair_mrr']:.4f} ({s['top1_rate']:.4f})")
                lines.append(f"| {name} | " + " | ".join(parts) + " |")
        lines.append("")
    args.output_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.output_json} and {args.output_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
