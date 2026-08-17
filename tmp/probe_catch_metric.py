#!/usr/bin/env python3
"""Verify, by running the code, what src.eval.fliptrack_metrics.pair_score does
and does not give us on a Mini-A5 catch (equal-gold) pair.

Three synthetic prediction cases against a real catch row:
  1. consistent AND correct     -> should be pair_correct
  2. consistent BUT wrong       -> stability holds, correctness fails
  3. inconsistent (A ok, B not) -> stability fails
"""
import json
from pathlib import Path

from src.eval.fliptrack_metrics import golds_equivalent, pair_score

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
row0 = json.loads((ROOT / "data/mini_a5_catch_v1/pairs.jsonl").read_text().splitlines()[0])
gold = row0["answer_a"]
print(f"catch row: pair_group_uid={row0['pair_group_uid']}  answer_a={row0['answer_a']!r} "
      f"answer_b={row0['answer_b']!r}")
print(f"golds_equivalent(answer_a, answer_b) = {golds_equivalent(row0['answer_a'], row0['answer_b'])}")

cases = {
    "consistent_and_correct": (f"<answer>{gold}</answer>", f"<answer>{gold}</answer>"),
    "consistent_but_wrong": ("<answer>ZZZ</answer>", "<answer>ZZZ</answer>"),
    "inconsistent_a_correct": (f"<answer>{gold}</answer>", "<answer>ZZZ</answer>"),
}
INTEREST = ["pair_correct", "strict_pair_correct", "correct_a", "correct_b",
            "collapsed", "equal_gold_a", "equal_gold_b",
            "extracted_answer_a", "extracted_answer_b"]

for name, (pa, pb) in cases.items():
    scored = pair_score(
        {"pair_id": row0["pair_group_uid"], "answer_a": row0["answer_a"],
         "answer_b": row0["answer_b"], "prediction_a": pa, "prediction_b": pb},
        prompt_contract=None,
    )
    print(f"\n--- {name}")
    for key in INTEREST:
        print(f"    {key:<24} {scored[key]!r}")
    # The indicator the endpoint actually needs, computed explicitly:
    from src.rewards.answer_reward import normalize_text
    consistent = normalize_text(scored["extracted_answer_a"]) == normalize_text(scored["extracted_answer_b"])
    print(f"    {'>> self_consistency':<24} {consistent!r}   (NOT exposed by pair_score on equal-gold rows)")
