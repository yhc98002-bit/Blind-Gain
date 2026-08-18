#!/usr/bin/env python3
"""Exact gradient availability for each candidate ST3 arm-2 grouping.

`diagnose_st3_joint_feasibility.py` shows the registered k=4 product leaves only
~2.4% of groups able to produce a GRPO gradient at cold start, against 42.2% for
the Mini-A5 k=2 CP arm the registration names as C2's reference implementation.
This scores the candidate repairs on the SAME measurement so the choice is a
comparison of numbers rather than of intuitions.

The registered arm-2 reward multiplies two separable registered ideas:

  C2  joint intervention-group scoring   -- both SIDES of the counterfactual
  C3  premise-verified hierarchical      -- the read counts only if the probe
      reward                                (which target is relevant) was right

k=4 is C2 x C3 applied together. C2 alone (l3_a x l3_b) and C3 alone
(l3_s x probe_s, per side s) are each k=2 -- the size Mini-A5 validated.

Members are separate prompts sampled independently, so every q below is exact
given per-member p; no approximation except the clearly-labelled warm-start row,
which assumes a homogeneous competence level rather than a measured one.
"""
from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def informative(rates: list[float], rollouts: int) -> float:
    return statistics.mean(
        1.0 - rate ** rollouts - (1.0 - rate) ** rollouts for rate in rates)


def load_members(corpus: Path, globs: list[str], field: str) -> dict[str, dict[str, float]]:
    rows = [json.loads(l) for l in corpus.read_text().splitlines() if l.strip()]
    scored: dict[int, float] = {}
    for pattern in globs:
        for run_dir in sorted(ROOT.glob(pattern)):
            path = run_dir / "per_item.jsonl"
            if not path.exists():
                continue
            for line in path.read_text().splitlines():
                if line.strip():
                    row = json.loads(line)
                    scored[int(row["row_index"])] = float(row[field])
    if len(scored) != len(rows):
        raise SystemExit(f"coverage mismatch: {len(scored)} vs {len(rows)}")
    groups: dict[str, dict[str, float]] = defaultdict(dict)
    for index, row in enumerate(rows):
        groups[str(row["pair_group_uid"])][str(row["pair_member"])] = scored[index]
    return dict(groups)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=ROOT / "data/st3_train_v1/train.jsonl")
    parser.add_argument("--real-glob", nargs="+",
                        default=["experiments/runs/st3_delta_q_real_*"])
    parser.add_argument("--field", default="p_sample")
    parser.add_argument("--rollout-n", type=int, default=5)
    parser.add_argument("--reference", type=float, default=0.4218,
                        help="Mini-A5 k=2 CP arm informative fraction (trained fine)")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    groups = load_members(args.corpus, args.real_glob, args.field)
    need = {"l3_a", "l3_b", "probe_a", "probe_b"}
    for uid, members in groups.items():
        if set(members) != need:
            raise SystemExit(f"group {uid} has members {sorted(members)}")

    designs: list[tuple[str, str, list[float], int]] = []
    designs.append((
        "A. k=4 joint  (AS REGISTERED: C2 x C3)",
        "l3_a*l3_b*probe_a*probe_b",
        [m["l3_a"] * m["l3_b"] * m["probe_a"] * m["probe_b"] for m in groups.values()],
        args.rollout_n))
    designs.append((
        "B. k=2 per-side premise gate  (C3 only)",
        "l3_s*probe_s, one group per side",
        [m[f"l3_{s}"] * m[f"probe_{s}"] for m in groups.values() for s in ("a", "b")],
        args.rollout_n))
    designs.append((
        "C. k=2 counterfactual pair  (C2 only)",
        "l3_a*l3_b; probes scored as members",
        [m["l3_a"] * m["l3_b"] for m in groups.values()],
        args.rollout_n))
    designs.append((
        "D. k=4 joint at R=16 rollouts",
        "as registered, more rollouts (breaks the matched rollout budget)",
        [m["l3_a"] * m["l3_b"] * m["probe_a"] * m["probe_b"] for m in groups.values()],
        16))
    designs.append((
        "E. member reward  (ARM 1 baseline)",
        "each member scored alone",
        [p for m in groups.values() for p in m.values()],
        args.rollout_n))

    print(f"ST3 arm-2 grouping options -- gradient availability at cold start\n"
          f"{len(groups)} groups, base member p = "
          f"{statistics.mean([p for m in groups.values() for p in m.values()]):.4f}\n")
    print(f"{'design':<42} {'mean q':>8} {'usable':>8}  vs Mini-A5 k=2")
    records = []
    for label, detail, rates, rollouts in designs:
        share = informative(rates, rollouts)
        ratio = share / args.reference
        print(f"{label:<42} {statistics.mean(rates):>8.4f} {share:>8.4f}  {ratio:>6.2f}x")
        print(f"{'   ' + detail:<42}")
        records.append({"design": label, "detail": detail, "rollouts": rollouts,
                        "mean_q": statistics.mean(rates),
                        "informative_fraction": share,
                        "ratio_to_mini_a5_reference": ratio})

    print("\nwarm start of the REGISTERED k=4 reward (homogeneous approximation:\n"
          "  every member at the same competence p, so q = p^4)")
    print(f"{'  member p':>12} {'q=p^4':>8} {'usable':>8}")
    warm = []
    for level in (0.25, 0.40, 0.55, 0.70, 0.85, 0.95):
        share = informative([level ** 4], args.rollout_n)
        print(f"{level:>12.2f} {level ** 4:>8.4f} {share:>8.4f}")
        warm.append({"member_p": level, "q": level ** 4, "informative_fraction": share})

    if args.report:
        args.report.write_text(json.dumps(
            {"schema_version": "blind-gains.st3-design-options.v1",
             "rollout_n": args.rollout_n,
             "n_groups": len(groups),
             "mini_a5_reference_informative_fraction": args.reference,
             "designs": records,
             "warm_start_homogeneous": warm}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
        print(f"\nwrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
