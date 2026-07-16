from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from src.eval.prompt_contract import response_satisfies_contract
from src.rewards.pilot_reward import (
    DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS,
    REASON_CODES,
    grade_response_accuracy,
)
from src.train.cp_grouping import broadcast_joint_accuracy


REWARD_NAME = "blind_gains_cp_grpo_v1"
REWARD_TYPE = "batch"
CP_REWARD_VERSION = "cp-grpo-reward-v1"


def _required(reward_input: dict[str, Any], field: str) -> Any:
    if field not in reward_input:
        raise KeyError(f"CP-GRPO reward input is missing {field!r}")
    return reward_input[field]


def _member_scores(
    reward_inputs: Sequence[dict[str, Any]], symbolic_grader_timeout_seconds: float
) -> list[dict[str, Any]]:
    scores: list[dict[str, Any]] = []
    for reward_input in reward_inputs:
        response = str(_required(reward_input, "response"))
        ground_truth = str(_required(reward_input, "ground_truth")).strip()
        grade = grade_response_accuracy(
            response,
            ground_truth,
            symbolic_grader_timeout_seconds=symbolic_grader_timeout_seconds,
        )
        scores.append(
            {
                "accuracy": float(bool(grade["mathruler_correct"])),
                "canonical_eval_reward": float(bool(grade["canonical_correct"])),
                "format": float(response_satisfies_contract(response)),
                "reward_disagreement": float(
                    grade["reward_disagreement_reason"] != "none"
                ),
                "reward_disagreement_reason_code": REASON_CODES[
                    str(grade["reward_disagreement_reason"])
                ],
            }
        )
    return scores


def compute_score(
    reward_inputs: list[dict[str, Any]],
    symbolic_grader_timeout_seconds: float = DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS,
) -> list[dict[str, float]]:
    """Compute the exact registered CP reward and broadcast it to pair members."""

    if not reward_inputs:
        raise ValueError("CP-GRPO reward requires a nonempty batch")
    member_scores = _member_scores(reward_inputs, symbolic_grader_timeout_seconds)
    joint = broadcast_joint_accuracy(
        [score["accuracy"] for score in member_scores],
        [_required(row, "pair_group_uid") for row in reward_inputs],
        [_required(row, "pair_member") for row in reward_inputs],
        [_required(row, "pair_rollout_index") for row in reward_inputs],
    )
    outputs: list[dict[str, float]] = []
    for row, score in enumerate(member_scores):
        outputs.append(
            {
                "overall": float(joint[row].item()),
                "accuracy": score["accuracy"],
                "format": score["format"],
                "member_accuracy": score["accuracy"],
                "pair_joint_accuracy": float(joint[row].item()),
                "canonical_eval_reward": score["canonical_eval_reward"],
                "reward_disagreement": score["reward_disagreement"],
                "reward_disagreement_reason_code": score[
                    "reward_disagreement_reason_code"
                ],
            }
        )
    return outputs


def compute_member_score(
    reward_inputs: list[dict[str, Any]],
    symbolic_grader_timeout_seconds: float = DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS,
) -> list[dict[str, float]]:
    """Matched same-data control: member accuracy with identical metadata checks."""

    if not reward_inputs:
        raise ValueError("same-data reward requires a nonempty batch")
    # Validate complete paired rollouts even though this control does not multiply rewards.
    broadcast_joint_accuracy(
        [1.0] * len(reward_inputs),
        [_required(row, "pair_group_uid") for row in reward_inputs],
        [_required(row, "pair_member") for row in reward_inputs],
        [_required(row, "pair_rollout_index") for row in reward_inputs],
    )
    outputs = _member_scores(reward_inputs, symbolic_grader_timeout_seconds)
    return [
        {
            "overall": score["accuracy"],
            "accuracy": score["accuracy"],
            "format": score["format"],
            "member_accuracy": score["accuracy"],
            "pair_joint_accuracy": 0.0,
            "canonical_eval_reward": score["canonical_eval_reward"],
            "reward_disagreement": score["reward_disagreement"],
            "reward_disagreement_reason_code": score[
                "reward_disagreement_reason_code"
            ],
        }
        for score in outputs
    ]
