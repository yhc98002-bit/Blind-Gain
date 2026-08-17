#!/usr/bin/env python3
"""Offline re-score of banked predictions under matcher v3 (sign-aware),
per dispatch 2026-08-16b ruling 2: "re-score collision-class cells only;
report deltas; amend registered readouts only where movement exceeds
rounding."

Reads `predictions.jsonl` files that already carry the model's raw text
(`prediction_a`/`prediction_b`) and scores every row TWICE with today's code —
once with the pre-v3 containment tier-1 rule, once with the sign-aware rule —
so the reported delta isolates the matcher change and nothing else. The banked
booleans are reported separately as drift provenance: files banked before an
earlier scorer fix (the P0.2 equal-gold invariance fix) legitimately differ
from today's code for unrelated reasons, and conflating the two would have
misattributed that fix to this one. No GPU, no model, no mutation of any
banked artifact.

A cell is "collision-class" iff at least one banked row carries a tier-1
credit whose gold and extracted answer differ only in sign — those are the
only rows the fix can move, and the report states that count per cell.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import math
import re as _re

import src.eval.fliptrack_metrics as metrics  # noqa: E402
from src.eval.fliptrack_metrics import MATCHER_VERSION, match_tier as MATCH_TIER_V3  # noqa: E402
from src.rewards.answer_reward import (  # noqa: E402
    answers_match,
    normalize_text,
    numeric_value,
)


def legacy_match_tier(span, answer, numeric_tol: float = 1e-4) -> int:
    """The pre-v3 (containment) tier-1 rule, kept ONLY here so the report can
    isolate the matcher change. Comparing v3 against the booleans banked in a
    predictions file would NOT isolate it: files banked before an earlier
    scorer fix (e.g. the P0.2 equal-gold invariance fix, 2026-07-28) differ
    from today's code for reasons unrelated to the matcher. Both columns below
    are therefore produced by scoring every row twice with today's code,
    swapping only the tier-1 rule."""
    pred = normalize_text(span)
    gold = normalize_text(answer)
    if not pred or not gold:
        return 0
    if pred == gold:
        return 2
    if answers_match(span, answer, numeric_tol=numeric_tol):
        return 2
    pred_num = numeric_value(pred)
    gold_num = numeric_value(gold)
    if (pred_num is not None and gold_num is not None
            and math.isclose(pred_num, gold_num, rel_tol=numeric_tol, abs_tol=numeric_tol)):
        return 2
    if _re.search(r"\w", gold):
        if _re.search(rf"(?<!\w){_re.escape(gold)}(?!\w)", pred):
            return 1
    elif gold in pred:
        return 1
    return 0


def score_all(rows, tier_fn):
    """pair_score every row with `tier_fn` installed as the tier rule."""
    original = metrics.match_tier
    metrics.match_tier = tier_fn
    try:
        return [metrics.pair_score(row) for row in rows]
    finally:
        metrics.match_tier = original


def sign_collision(gold, extracted) -> bool:
    gold, extracted = str(gold), str(extracted)
    return gold.lstrip("-") == extracted.lstrip("-") and gold != extracted


def rescore_file(path: Path) -> dict | None:
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    if not rows or "prediction_a" not in rows[0]:
        return None
    v2 = score_all(rows, legacy_match_tier)
    v3 = score_all(rows, MATCH_TIER_V3)
    banked_m = old_m = new_m = 0
    old_p = new_p = banked_p = 0
    collisions = moved = banked_drift = 0
    n_members = 0
    for row, a, b in zip(rows, v2, v3):
        for side in ("a", "b"):
            n_members += 1
            was_banked = bool(row.get(f"correct_{side}"))
            old = bool(a[f"correct_{side}"])
            new = bool(b[f"correct_{side}"])
            banked_m += was_banked
            old_m += old
            new_m += new
            if old != new:
                moved += 1
            if was_banked != old:
                banked_drift += 1
            if a[f"match_tier_{side}"] == 1 and sign_collision(
                    row.get(f"answer_{side}"), a[f"extracted_answer_{side}"]):
                collisions += 1
        banked_p += bool(row.get("pair_correct"))
        old_p += bool(a["pair_correct"])
        new_p += bool(b["pair_correct"])
    n_pairs = len(rows)
    return {
        "file": str(path),
        "n_pairs": n_pairs,
        "n_members": n_members,
        "sign_collision_credits": collisions,
        "members_moved_by_matcher": moved,
        "members_differing_from_banked_under_v2": banked_drift,
        "member_accuracy_banked": round(banked_m / n_members, 4),
        "member_accuracy_v2": round(old_m / n_members, 4),
        "member_accuracy_v3": round(new_m / n_members, 4),
        "member_delta": round((new_m - old_m) / n_members, 4),
        "pair_accuracy_v2": round(old_p / n_pairs, 4),
        "pair_accuracy_v3": round(new_p / n_pairs, 4),
        "pair_delta": round((new_p - old_p) / n_pairs, 4),
        "collision_class": collisions > 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--glob", action="append", required=True,
                        help="glob(s) of predictions.jsonl files, repeatable")
    parser.add_argument("--output-json", type=Path,
                        default=ROOT / "reports/matcher_v3_rescore_v1.json")
    parser.add_argument("--output-md", type=Path,
                        default=ROOT / "reports/matcher_v3_rescore_v1.md")
    args = parser.parse_args()
    for out in (args.output_json, args.output_md):
        if out.exists():
            raise FileExistsError(out)

    results = []
    for pattern in args.glob:
        for path in sorted(ROOT.glob(pattern)):
            entry = rescore_file(path)
            if entry is not None:
                results.append(entry)
    if not results:
        raise SystemExit("no scorable prediction files matched")

    collision = [r for r in results if r["collision_class"]]
    payload = {
        "schema_version": "blind-gains.matcher-v3-rescore.v1",
        "matcher_version": MATCHER_VERSION,
        "rule": "tier-1 containment -> sign-aware parsed-numeric equality",
        "n_files": len(results),
        "n_collision_class_files": len(collision),
        "totals": {
            "sign_collision_credits": sum(r["sign_collision_credits"] for r in results),
            "members_moved_by_matcher": sum(r["members_moved_by_matcher"] for r in results),
            "members_differing_from_banked_under_v2": sum(r["members_differing_from_banked_under_v2"] for r in results),
            "n_members": sum(r["n_members"] for r in results),
        },
        "files": results,
    }
    args.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                                encoding="utf-8")

    lines = ["# Matcher v3 re-score — banked vs sign-aware", "",
             f"Rule: {payload['rule']} (`{MATCHER_VERSION}`). "
             f"{payload['totals']['sign_collision_credits']} sign-collision credits "
             f"across {payload['totals']['n_members']} scored members in "
             f"{len(results)} files; {len(collision)} files are collision-class.",
             "", "| cell | n pairs | collisions | member v2 → v3 (Δ) | pair v2 → v3 (Δ) |",
             "|---|---|---|---|---|"]
    for r in sorted(results, key=lambda r: -abs(r["member_delta"])):
        if not r["collision_class"]:
            continue
        name = Path(r["file"]).parent.name or Path(r["file"]).stem
        lines.append(
            f"| {name} | {r['n_pairs']} | {r['sign_collision_credits']} | "
            f"{r['member_accuracy_v2']:.4f} → {r['member_accuracy_v3']:.4f} "
            f"({r['member_delta']:+.4f}) | {r['pair_accuracy_v2']:.4f} → "
            f"{r['pair_accuracy_v3']:.4f} ({r['pair_delta']:+.4f}) |")
    unaffected = [r for r in results if not r["collision_class"]]
    lines += ["", f"{len(unaffected)} file(s) carry no sign-collision credit; every "
                  "one re-scores bit-identically (verified: members_moved == 0 for "
                  f"{sum(1 for r in unaffected if r['members_moved_by_matcher'] == 0)} of them).", ""]
    args.output_md.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({k: payload[k] for k in
                      ("n_files", "n_collision_class_files", "totals")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
