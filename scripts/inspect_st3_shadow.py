#!/usr/bin/env python3
"""Decompose an ST3 shadow log into accuracy vs format over training time.

`pilot_reward.compute_score` returns overall = (1-fw)*accuracy + fw*format, so a
rising `critic/score/mean` can be format compliance rather than task accuracy.
The shadow log records the two components per response, in emission order, so
binning by row order recovers the trajectory without the trainer's metrics.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("shadow", type=Path, nargs="+")
    parser.add_argument("--bin", type=int, default=1200,
                        help="rows per bin (one step = rollout_batch * rollout.n)")
    args = parser.parse_args()

    for path in args.shadow:
        rows = []
        for line in path.read_text(errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        print(f"=== {path} : {len(rows)} rows")
        if not rows:
            continue
        keys = sorted(rows[0].keys())
        print("    fields:", ", ".join(keys))
        for start in range(0, len(rows), args.bin):
            chunk = rows[start:start + args.bin]
            if len(chunk) < args.bin // 4:
                continue

            def mean(field: str) -> float | None:
                vals = [r[field] for r in chunk if field in r
                        and isinstance(r[field], (bool, int, float))]
                return sum(float(v) for v in vals) / len(vals) if vals else None

            acc = mean("mathruler_accuracy_reward")
            fmt = mean("contract_valid")
            can = mean("canonical_eval_reward")
            train = mean("training_reward")
            parts = [f"bin {start // args.bin:>3}", f"n={len(chunk)}"]
            for label, value in (("acc", acc), ("format", fmt), ("canon", can),
                                 ("train", train)):
                parts.append(f"{label}={value:.4f}" if value is not None
                             else f"{label}=NA")
            if acc is not None and fmt is not None:
                parts.append(f"overall@fw0.5={0.5 * acc + 0.5 * fmt:.4f}")
            print("   ", "  ".join(parts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
