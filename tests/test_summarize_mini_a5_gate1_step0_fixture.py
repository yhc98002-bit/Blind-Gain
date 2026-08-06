"""Adversarial fixtures (I10) for the Gate-1 step-0 summarizer/audit.

The summarizer must recompute every reward from the raw responses and reject
tampered reward columns, incomplete rollout identity sets, and cross-arm rows;
an honest prediction set is the positive control.
"""
from __future__ import annotations

import copy

from scripts.summarize_mini_a5_gate1_step0 import EXPECTED_PAIRS, build_summary
from src.rewards.cp_grpo_reward import compute_member_score, compute_score


def _make_rows(arm: str = "std") -> list[dict]:
    rows = []
    for pair_index in range(EXPECTED_PAIRS):
        uid = f"{'std1_' if arm == 'std' else 'nec1_'}fx{pair_index:06d}"
        reward_inputs = []
        for member in ("a", "b"):
            truth = f"{pair_index}{member}"
            for rollout_index in range(5):
                # Rollouts alternate correct/incorrect deterministically.
                correct = (pair_index + rollout_index) % 2 == 0
                response = (
                    f"<answer> {truth} </answer>"
                    if correct
                    else "<answer> wrong </answer>"
                )
                reward_inputs.append(
                    {
                        "response": response,
                        "ground_truth": truth,
                        "pair_group_uid": uid,
                        "pair_member": member,
                        "pair_rollout_index": rollout_index,
                    }
                )
        cp_scores = compute_score(reward_inputs)
        member_scores = compute_member_score(reward_inputs)
        for reward_input, cp_score, member_score in zip(
            reward_inputs, cp_scores, member_scores, strict=True
        ):
            rows.append(
                {
                    "arm": arm,
                    "pair_group_uid": uid,
                    "pair_member": reward_input["pair_member"],
                    "pair_rollout_index": reward_input["pair_rollout_index"],
                    "template_id": f"fx_template_{pair_index % 3}",
                    "response": reward_input["response"],
                    "ground_truth": reward_input["ground_truth"],
                    "member_reward": float(member_score["overall"]),
                    "cp_joint_reward": float(cp_score["overall"]),
                    "contract_valid": float(member_score["format"]),
                    "reward_disagreement_reason_code": float(
                        member_score["reward_disagreement_reason_code"]
                    ),
                }
            )
    return rows


def test_honest_predictions_pass():
    rows = _make_rows()
    summary = build_summary(rows, "std")
    assert summary["status"] == "pass"
    assert summary["recompute_mismatches"] == 0
    assert summary["pairs"] == EXPECTED_PAIRS
    assert summary["member_reward"]["n"] == EXPECTED_PAIRS * 10


def test_tampered_reward_column_fails():
    """Naive: trust the stored member_reward column instead of recomputing --
    a flipped reward must be caught."""
    rows = _make_rows()
    tampered = copy.deepcopy(rows)
    tampered[17]["member_reward"] = 1.0 - float(tampered[17]["member_reward"])
    summary = build_summary(tampered, "std")
    assert summary["status"] == "fail"
    assert not summary["checks"]["reward_recompute_identical"]


def test_missing_rollout_fails():
    rows = _make_rows()
    summary = build_summary(rows[:-1], "std")
    assert summary["status"] == "fail"
    assert not summary["checks"]["row_count_exact"]
    assert not summary["checks"]["identity_sets_complete"]


def test_cross_arm_rows_fail():
    rows = _make_rows()
    mixed = copy.deepcopy(rows)
    mixed[3]["arm"] = "necessity"
    summary = build_summary(mixed, "std")
    assert summary["status"] == "fail"
    assert not summary["checks"]["single_arm"]


def test_duplicated_identity_fails():
    rows = _make_rows()
    duplicated = copy.deepcopy(rows)
    duplicated[1] = copy.deepcopy(duplicated[0])
    summary = build_summary(duplicated, "std")
    assert summary["status"] == "fail"
    assert not summary["checks"]["identity_sets_complete"]
