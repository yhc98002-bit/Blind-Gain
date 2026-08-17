#!/usr/bin/env python3
"""HB diagnostic D1 readout (docs/registered_hier_instrument_sweep_v1.md):
does any existing RLVR recipe buy hierarchy capability, and at which layer?

Per arm × cell × layer: member accuracy over the registered stable+invariance
composition (A2), with target_switch and the discovery probe reported
separately, never averaged into the composition (I13). Two-seed arms are
summarised by the registered per-item seed mean before any aggregate. All
scoring is re-derived here from banked predictions with the CURRENT scorer
(matcher v3), so every arm and the frozen base are on one footing.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.eval.fliptrack_metrics import MATCHER_VERSION, pair_score  # noqa: E402

CELLS = ("n8", "n12", "n20")
LAYERS = ("l1", "l2", "l3", "probe")
COMPOSITION = ("target_stable", "invariance")


def cell_rows(run_dir: Path, cell: str, layer: str) -> list[dict]:
    path = run_dir / f"hier_coord_v1_{cell}_{layer}" / "predictions.jsonl"
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def per_item(run_dir: Path) -> dict:
    """(cell, layer, subset) -> {pair_id: [member correctness, ...]} re-scored."""
    out: dict = defaultdict(dict)
    for cell in CELLS:
        for layer in LAYERS:
            for row in cell_rows(run_dir, cell, layer):
                scored = pair_score(row)
                role = next((r for r in ("target_switch", "target_stable",
                                         "invariance") if r in row["pair_id"]), None)
                subset = ("composition" if role in COMPOSITION else role)
                key = (cell, layer, subset)
                out[key][row["pair_id"]] = [bool(scored["correct_a"]),
                                            bool(scored["correct_b"])]
    return out


def seed_mean(per_seed: list[dict]) -> dict:
    """Registered estimator: per-item seed mean BEFORE any aggregate."""
    merged: dict = {}
    keys = set().union(*(set(d) for d in per_seed))
    for key in keys:
        items = set().union(*(set(d.get(key, {})) for d in per_seed))
        acc = {}
        for pair_id in items:
            vals = [d[key][pair_id] for d in per_seed if pair_id in d.get(key, {})]
            acc[pair_id] = [sum(v[i] for v in vals) / len(vals) for i in (0, 1)]
        merged[key] = acc
    return merged


def summarise(items: dict) -> dict:
    out = {}
    for (cell, layer, subset), pairs in items.items():
        vals = [v for members in pairs.values() for v in members]
        if vals:
            out[f"{cell}/{layer}/{subset}"] = round(sum(vals) / len(vals), 4)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", action="append", nargs="+",
                        metavar=("NAME", "RUN_DIR"), required=True,
                        help="arm name followed by one run dir per seed")
    parser.add_argument("--output-json", type=Path,
                        default=ROOT / "reports/hier_instrument_sweep_v1.json")
    parser.add_argument("--output-md", type=Path,
                        default=ROOT / "reports/hier_instrument_sweep_v1.md")
    args = parser.parse_args()
    for out in (args.output_json, args.output_md):
        if out.exists():
            raise FileExistsError(out)

    arms = {}
    for spec in args.arm:
        name, run_dirs = spec[0], [Path(p) for p in spec[1:]]
        per_seed = [per_item(d) for d in run_dirs]
        merged = seed_mean(per_seed) if len(per_seed) > 1 else per_seed[0]
        arms[name] = {"run_dirs": [str(d) for d in run_dirs],
                      "n_seeds": len(run_dirs),
                      "accuracy": summarise(merged)}

    payload = {"schema_version": "blind-gains.hier-instrument-sweep.v1",
               "registration": "docs/registered_hier_instrument_sweep_v1.md",
               "matcher_version": MATCHER_VERSION,
               "instrument": "data/hier_v1_dev_r2 (coord r2, frozen)",
               "composition": "stable+invariance member accuracy (A2); "
                              "switch and probe reported separately (I13)",
               "arms": arms}
    args.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                                encoding="utf-8")

    names = list(arms)
    lines = ["# HB diagnostic D1 — does any RLVR recipe buy hierarchy capability?",
             "",
             f"Instrument: frozen coord r2, scored with `{MATCHER_VERSION}`. "
             "Composition = stable+invariance member accuracy; switch and probe "
             "separate. Two-seed arms use the registered per-item seed mean.",
             ""]
    for subset in ("composition", "target_switch", "probe"):
        lines += [f"## {subset}", "",
                  "| cell/layer | " + " | ".join(names) + " |",
                  "|---|" + "---|" * len(names)]
        keys = sorted({k for a in arms.values() for k in a["accuracy"]
                       if k.endswith("/" + subset) or
                       (subset == "probe" and "/probe/" in k)})
        for key in keys:
            cells = []
            for name in names:
                val = arms[name]["accuracy"].get(key)
                cells.append(f"{val:.4f}" if val is not None else "—")
            lines.append(f"| {key.rsplit('/', 1)[0]} | " + " | ".join(cells) + " |")
        lines.append("")
    args.output_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.output_json} and {args.output_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
