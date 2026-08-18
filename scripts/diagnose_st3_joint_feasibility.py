#!/usr/bin/env python3
"""Cold-start feasibility of the ST3 arm-2 joint reward, from base-model rollouts.

Arm 2 scores an intervention group with the PRODUCT of its k member accuracies.
Under GRPO a group's advantage is (r - mean)/std across that group's rollouts, so
a group whose rollouts ALL score 0 (or all score 1) contributes exactly nothing to
the update. With k=4 and member accuracy p the joint rate is ~p^k, so a perfectly
good hypothesis can be untestable simply because the reward starts too sparse.

The k members of a group are SEPARATE prompts, sampled independently, so this is
computable exactly from per-item sampling probabilities rather than estimated:

    q_g      = prod_m p_m                      expected joint reward of group g
    P(var)_g = 1 - q_g^R - (1 - q_g)^R         chance g yields any gradient at R rollouts

`p_m` comes from the registered Delta-q `real` pass (16 samples, T=1, base
checkpoint) -- the same measurement C1's necessity weights are built from, so no
new GPU work is required. Reported against the arm-1 (member-reward) counterpart,
whose informative-group fraction is computed the same way at k=1.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_pass(globs: list[str], field: str) -> dict[int, float]:
    out: dict[int, float] = {}
    for pattern in globs:
        for run_dir in sorted(ROOT.glob(pattern)):
            path = run_dir / "per_item.jsonl"
            if not path.exists():
                continue
            for line in path.read_text().splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                index = int(row["row_index"])
                if index in out:
                    raise AssertionError(f"duplicate row_index {index}")
                value = row.get(field)
                if value is None:
                    raise KeyError(f"{field} missing from {path}")
                out[index] = float(value)
    if not out:
        raise SystemExit(f"no per-item rows matched {globs}")
    return out


def informative_fraction(rates: list[float], rollouts: int) -> float:
    """Fraction of groups that can produce a nonzero GRPO advantage."""
    return statistics.mean(
        1.0 - rate ** rollouts - (1.0 - rate) ** rollouts for rate in rates)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path,
                        default=ROOT / "data/st3_train_v1/train.jsonl")
    parser.add_argument("--real-glob", nargs="+",
                        default=["experiments/runs/st3_delta_q_real_*"])
    parser.add_argument("--field", default="p_sample")
    parser.add_argument("--rollout-n", type=int, default=5)
    parser.add_argument("--groups-per-step", type=int, default=60)
    parser.add_argument("--delta-q", type=Path,
                        help="per-member delta_q.jsonl (pair_group_uid, pair_member, "
                             "q_real) to use instead of corpus + Delta-q run glob; "
                             "lets a k=2 corpus be scored by identical code")
    parser.add_argument("--group-size", type=int, default=4)
    parser.add_argument("--label", default="ST3")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    groups: dict[str, dict[str, float]] = defaultdict(dict)
    by_member: dict[str, list[float]] = defaultdict(list)
    if args.delta_q:
        for line in args.delta_q.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            groups[str(row["pair_group_uid"])][str(row["pair_member"])] = float(row["q_real"])
            by_member[str(row["pair_member"])].append(float(row["q_real"]))
    else:
        corpus = [json.loads(l) for l in args.corpus.read_text().splitlines() if l.strip()]
        real = load_pass(args.real_glob, args.field)
        if len(real) != len(corpus):
            raise SystemExit(f"coverage mismatch: {len(real)} scored vs {len(corpus)} rows")
        for index, row in enumerate(corpus):
            member = str(row["pair_member"])
            probability = real[index]
            groups[str(row["pair_group_uid"])][member] = probability
            by_member[member].append(probability)

    sizes = {len(members) for members in groups.values()}
    if sizes != {args.group_size}:
        raise SystemExit(f"expected {args.group_size} members per group, "
                         f"found sizes {sorted(sizes)}")

    joint = []
    for members in groups.values():
        product = 1.0
        for probability in members.values():
            product *= probability
        joint.append(product)
    member_rates = [p for values in by_member.values() for p in values]

    joint_informative = informative_fraction(joint, args.rollout_n)
    member_informative = informative_fraction(member_rates, args.rollout_n)

    print(f"{args.label} joint-reward cold-start feasibility (base checkpoint, "
          f"{len(groups)} groups, k={args.group_size}, R={args.rollout_n})\n")
    print("per-member base accuracy")
    for member in sorted(by_member):
        values = by_member[member]
        print(f"  {member:<9} mean p = {statistics.mean(values):.4f}   "
              f"p=0 on {sum(1 for v in values if v == 0.0) / len(values):.3f} of items")
    print(f"  {'ALL':<9} mean p = {statistics.mean(member_rates):.4f}")

    print("\ngroup joint reward  q = prod_m p_m")
    print(f"  mean q                     {statistics.mean(joint):.4f}")
    print(f"  median q                   {statistics.median(joint):.4f}")
    for threshold in (0.0, 0.01, 0.05, 0.10):
        share = sum(1 for q in joint if q > threshold) / len(joint)
        print(f"  groups with q > {threshold:<5}      {share:.4f}")

    print(f"\ngradient availability at R={args.rollout_n} rollouts")
    print(f"  ARM 2 (joint, k={args.group_size}):  {joint_informative:.4f} of groups can move "
          f"-> ~{joint_informative * args.groups_per_step:.1f} of "
          f"{args.groups_per_step} groups per step")
    print(f"  ARM 1 (member, k=1): {member_informative:.4f} of prompts can move "
          f"-> ~{member_informative * args.groups_per_step * 4:.1f} of "
          f"{args.groups_per_step * 4} prompts per step")
    if member_informative > 0:
        print(f"  arm 2 starts with {joint_informative / member_informative:.2f}x "
              "the usable signal of arm 1")

    if args.report:
        args.report.write_text(json.dumps({
            "schema_version": "blind-gains.st3-joint-feasibility.v1",
            "corpus": str(args.corpus),
            "source": "registered Delta-q real pass (16 samples, T=1, base ckpt)",
            "field": args.field,
            "rollout_n": args.rollout_n,
            "n_groups": len(groups),
            "member_mean_p": statistics.mean(member_rates),
            "per_member_mean_p": {m: statistics.mean(v) for m, v in sorted(by_member.items())},
            "joint_mean_q": statistics.mean(joint),
            "joint_median_q": statistics.median(joint),
            "groups_q_gt_0": sum(1 for q in joint if q > 0.0) / len(joint),
            "arm2_informative_group_fraction": joint_informative,
            "arm1_informative_prompt_fraction": member_informative,
            "arm2_informative_groups_per_step": joint_informative * args.groups_per_step,
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"\nwrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
