"""ST3 arm-2 reward: necessity-sampled intervention-group scoring (C2 + C3).

Mirrors `src/rewards/cp_grpo_reward.py` (the registered C2 reference
implementation) but over k-ary intervention groups, so the joint outcome can
span BOTH the discovery step and the read step on BOTH sides of the
counterfactual. For an ST3 group — `l3_a, l3_b, probe_a, probe_b` — the reward
is 1 only when the model named the right target on both sides AND read the
right value on both sides, in the same rollout. That is C3: the answer counts
only when the premise (which target is relevant) was itself identified.

C1 (necessity) is NOT here: it lives entirely in the sampling probabilities of
the pre-materialised corpus (`build_st3_necessity_corpus.py`) — no reward
term, no loss weight, no advantage transform (I1).

Grading is delegated to the registered pilot reward so both ST3 arms share one
accuracy definition; only the aggregation differs. `compute_member_score` is
the matched control: it validates the group structure identically but scores
members independently, so the arms cannot differ in validation strictness.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.eval.prompt_contract import response_satisfies_contract  # noqa: E402
from src.rewards.pilot_reward import (  # noqa: E402
    DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS,
    grade_response_accuracy,
)
from src.train.hier_group_scoring import broadcast_joint_accuracy  # noqa: E402

REWARD_TYPE = "batch"
IGPO_REWARD_VERSION = "blind-gains-igpo-v1"
GROUP_FIELDS = ("pair_group_uid", "pair_member", "pair_rollout_index")


def _required(row: dict[str, Any], field: str) -> Any:
    if field not in row:
        raise KeyError(
            f"IGPO reward requires {field!r} on every row; the trainer must "
            "forward intervention-group metadata to the reward manager")
    return row[field]


def _member_scores(reward_inputs: list[dict[str, Any]],
                   timeout_seconds: float) -> list[dict[str, float]]:
    scores = []
    for row in reward_inputs:
        response = row.get("response", "")
        grade = grade_response_accuracy(
            response, row["ground_truth"],
            symbolic_grader_timeout_seconds=timeout_seconds)
        scores.append({
            "accuracy": float(bool(grade["mathruler_correct"])),
            "canonical_accuracy": float(bool(grade["canonical_correct"])),
            "format": float(bool(response_satisfies_contract(response, None))),
        })
    return scores


def compute_score(
    reward_inputs: list[dict[str, Any]],
    symbolic_grader_timeout_seconds: float = DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS,
) -> list[dict[str, float]]:
    """Joint intervention-group reward, broadcast to every member."""
    if not reward_inputs:
        raise ValueError("IGPO reward requires a nonempty batch")
    member_scores = _member_scores(reward_inputs, symbolic_grader_timeout_seconds)
    joint = broadcast_joint_accuracy(
        [score["accuracy"] for score in member_scores],
        [_required(row, "pair_group_uid") for row in reward_inputs],
        [_required(row, "pair_member") for row in reward_inputs],
        [_required(row, "pair_rollout_index") for row in reward_inputs],
    )
    outputs = []
    for row, score in enumerate(member_scores):
        joint_value = float(joint[row].item())
        outputs.append({
            "overall": joint_value,          # no format term, as in the CP arm
            "accuracy": score["accuracy"],
            "format": score["format"],
            "member_accuracy": score["accuracy"],
            "canonical_member_accuracy": score["canonical_accuracy"],
            "group_joint_accuracy": joint_value,
        })
    return outputs


def compute_member_score(
    reward_inputs: list[dict[str, Any]],
    symbolic_grader_timeout_seconds: float = DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS,
) -> list[dict[str, float]]:
    """Matched control: identical grading and identical group validation, but
    the member's own accuracy is the reward."""
    if not reward_inputs:
        raise ValueError("IGPO member reward requires a nonempty batch")
    member_scores = _member_scores(reward_inputs, symbolic_grader_timeout_seconds)
    # Validate the group structure even though this control does not multiply,
    # so a malformed batch fails identically in both arms.
    broadcast_joint_accuracy(
        [1.0 for _ in member_scores],
        [_required(row, "pair_group_uid") for row in reward_inputs],
        [_required(row, "pair_member") for row in reward_inputs],
        [_required(row, "pair_rollout_index") for row in reward_inputs],
    )
    return [{
        "overall": score["accuracy"],
        "accuracy": score["accuracy"],
        "format": score["format"],
        "member_accuracy": score["accuracy"],
        "canonical_member_accuracy": score["canonical_accuracy"],
    } for score in member_scores]
