"""ST3 arm-2 reward: necessity-sampled intervention-group scoring (C2 + C3).

Mirrors `src/rewards/cp_grpo_reward.py` (the registered C2 reference
implementation) but over k-ary intervention groups. Launch amendment 2 pins the
ST3 group to ONE SIDE of a mother-item -- that side's L3 read and its discovery
probe -- so the reward is 1 only when the model named the right target for that
side AND read the right value there, in the same rollout. That is C3: the answer
counts only when the premise (which target is relevant) was itself identified.

The k=4 both-sides product was measured at 2.41% of groups able to produce a
GRPO gradient at base competence, against 42.2% for the Mini-A5 k=2 arm the
registration names as C2's reference implementation; see
`reports/st3_joint_feasibility_v1.md`.

C1 (necessity) is NOT here: it lives entirely in the sampling probabilities of
the pre-materialised corpus (`build_st3_necessity_corpus.py`) -- no reward term,
no loss weight, no advantage transform (I1).

Reward shape matches arm 1's `pilot_reward.compute_score`
(`(1 - format_weight) * accuracy + format_weight * format`) so the two ST3 arms
differ in the intervention alone. The one forced change is that the format term
is averaged over the group: a per-member format score varies across members of
one rollout, which `compute_group_level_grpo_advantage` refuses because the
group reward must be broadcast identically. Format saturates within ~2 steps in
practice, and a constant offset cancels exactly under GRPO normalisation, so the
term is near-inert after the early steps in either form.

`compute_member_score` is the matched control: identical grading, identical
group validation, but the member's own accuracy and its own format.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.eval.prompt_contract import response_satisfies_contract  # noqa: E402
from src.rewards.pilot_reward import (  # noqa: E402
    DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS,
    PARSER_VERSION,
    REASON_CODES,
    SYMBOLIC_GRADER_GUARD_VERSION,
    _append_shadow,
    grade_response_accuracy,
)
from src.train.hier_group_scoring import (  # noqa: E402
    broadcast_group_mean,
    broadcast_joint_accuracy,
)

REWARD_NAME = "blind_gains_igpo_v1"
REWARD_TYPE = "batch"
IGPO_REWARD_VERSION = "igpo-reward-v2-side-gate"
GROUP_FIELDS = ("pair_group_uid", "pair_member", "pair_rollout_index")
DEFAULT_FORMAT_WEIGHT = 0.5

# The ST3 group contract, passed explicitly so a batch missing a member
# everywhere cannot silently shrink the joint product (inferring the expected
# set from the first group cannot see a uniformly incomplete batch).
ST3_GROUP_MEMBERS = ("l3", "probe")


def _required(row: dict[str, Any], field: str) -> Any:
    if field not in row:
        raise KeyError(
            f"IGPO reward requires {field!r} on every row; the trainer must "
            "forward intervention-group metadata to the reward manager")
    return row[field]


def _member_scores(reward_inputs: list[dict[str, Any]],
                   timeout_seconds: float) -> list[dict[str, Any]]:
    scores: list[dict[str, Any]] = []
    for row in reward_inputs:
        response = str(row.get("response", ""))
        ground_truth = str(_required(row, "ground_truth")).strip()
        grade = grade_response_accuracy(
            response, ground_truth,
            symbolic_grader_timeout_seconds=timeout_seconds)
        scores.append({
            "response": response,
            "ground_truth": ground_truth,
            "extracted": grade["extracted"],
            "accuracy": float(bool(grade["mathruler_correct"])),
            "canonical_eval_reward": float(bool(grade["canonical_correct"])),
            "format": float(bool(response_satisfies_contract(response))),
            "mathruler_error": grade["mathruler_error"],
            "reward_disagreement": float(
                grade["reward_disagreement_reason"] != "none"),
            "reward_disagreement_reason": str(grade["reward_disagreement_reason"]),
            "reward_disagreement_reason_code": REASON_CODES[
                str(grade["reward_disagreement_reason"])],
        })
    return scores


def _group_metadata(reward_inputs: list[dict[str, Any]]) -> tuple[list, list, list]:
    return ([_required(row, "pair_group_uid") for row in reward_inputs],
            [_required(row, "pair_member") for row in reward_inputs],
            [_required(row, "pair_rollout_index") for row in reward_inputs])


def _log_shadow(rows: list[dict[str, Any]], scores: list[dict[str, Any]],
                training_rewards: list[float], joint: list[float] | None,
                format_weight: float, timeout_seconds: float,
                shadow_log_path: str | None, require_shadow_log: bool) -> None:
    """Same field names as the pilot reward's shadow log, plus the group fields,
    so the accuracy/format trajectory of either arm reads with the same tools."""
    resolved = shadow_log_path or os.environ.get("BLIND_GAINS_REWARD_SHADOW_LOG")
    if require_shadow_log and not resolved:
        raise RuntimeError(
            "IGPO reward requires BLIND_GAINS_REWARD_SHADOW_LOG or shadow_log_path")
    if not resolved:
        return
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path = Path(resolved)
    for index, (row, score) in enumerate(zip(rows, scores, strict=True)):
        _append_shadow(path, {
            "schema_version": "blind-gains.igpo-reward-shadow.v1",
            "timestamp_utc": stamp,
            "pid": os.getpid(),
            "igpo_reward_version": IGPO_REWARD_VERSION,
            "symbolic_grader_guard_version": SYMBOLIC_GRADER_GUARD_VERSION,
            "symbolic_grader_timeout_seconds": timeout_seconds,
            "parser_version": PARSER_VERSION,
            "format_weight": format_weight,
            "response_sha256": hashlib.sha256(
                score["response"].encode("utf-8")).hexdigest(),
            "ground_truth": score["ground_truth"],
            "extracted_answer": score["extracted"].span,
            "extraction_level": score["extracted"].extraction_level,
            "mathruler_accuracy_reward": score["accuracy"],
            "mathruler_error": score["mathruler_error"],
            "canonical_eval_reward": score["canonical_eval_reward"],
            "contract_valid": score["format"],
            "reward_disagreement_reason": score["reward_disagreement_reason"],
            "training_reward": training_rewards[index],
            "group_joint_accuracy": joint[index] if joint is not None else None,
            "pair_group_uid": str(row.get("pair_group_uid")),
            "pair_member": str(row.get("pair_member")),
            "pair_rollout_index": int(row.get("pair_rollout_index", -1)),
        })


def compute_score(
    reward_inputs: list[dict[str, Any]],
    format_weight: float = DEFAULT_FORMAT_WEIGHT,
    symbolic_grader_timeout_seconds: float = DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS,
    shadow_log_path: str | None = None,
    require_shadow_log: bool = False,
) -> list[dict[str, float]]:
    """Joint intervention-group reward, broadcast to every member."""
    if not reward_inputs:
        raise ValueError("IGPO reward requires a nonempty batch")
    if not 0.0 <= format_weight <= 1.0:
        raise ValueError(f"format_weight must be in [0, 1], found {format_weight}")
    scores = _member_scores(reward_inputs, symbolic_grader_timeout_seconds)
    uids, members, rollouts = _group_metadata(reward_inputs)

    joint = broadcast_joint_accuracy(
        [score["accuracy"] for score in scores], uids, members, rollouts,
        expected_members=ST3_GROUP_MEMBERS)
    group_format = broadcast_group_mean(
        [score["format"] for score in scores], uids, members, rollouts,
        expected_members=ST3_GROUP_MEMBERS)

    outputs = []
    training_rewards = []
    for index, score in enumerate(scores):
        joint_value = float(joint[index].item())
        format_value = float(group_format[index].item())
        overall = (1.0 - format_weight) * joint_value + format_weight * format_value
        training_rewards.append(overall)
        outputs.append({
            "overall": overall,
            "accuracy": score["accuracy"],
            "format": score["format"],
            "member_accuracy": score["accuracy"],
            "canonical_eval_reward": score["canonical_eval_reward"],
            "group_joint_accuracy": joint_value,
            "group_format": format_value,
            "reward_disagreement": score["reward_disagreement"],
            "reward_disagreement_reason_code": score["reward_disagreement_reason_code"],
        })
    _log_shadow(reward_inputs, scores, training_rewards,
                [o["group_joint_accuracy"] for o in outputs], format_weight,
                symbolic_grader_timeout_seconds, shadow_log_path, require_shadow_log)
    return outputs


def compute_member_score(
    reward_inputs: list[dict[str, Any]],
    format_weight: float = DEFAULT_FORMAT_WEIGHT,
    symbolic_grader_timeout_seconds: float = DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS,
    shadow_log_path: str | None = None,
    require_shadow_log: bool = False,
) -> list[dict[str, float]]:
    """Matched control: identical grading and identical group validation, but
    the member's own accuracy and its own format are the reward."""
    if not reward_inputs:
        raise ValueError("IGPO member reward requires a nonempty batch")
    if not 0.0 <= format_weight <= 1.0:
        raise ValueError(f"format_weight must be in [0, 1], found {format_weight}")
    scores = _member_scores(reward_inputs, symbolic_grader_timeout_seconds)
    uids, members, rollouts = _group_metadata(reward_inputs)
    # Validate the group structure even though this control does not multiply,
    # so a malformed batch fails identically in both arms.
    broadcast_joint_accuracy([1.0] * len(scores), uids, members, rollouts,
                             expected_members=ST3_GROUP_MEMBERS)

    outputs = []
    training_rewards = []
    for score in scores:
        overall = ((1.0 - format_weight) * score["accuracy"]
                   + format_weight * score["format"])
        training_rewards.append(overall)
        outputs.append({
            "overall": overall,
            "accuracy": score["accuracy"],
            "format": score["format"],
            "member_accuracy": score["accuracy"],
            "canonical_eval_reward": score["canonical_eval_reward"],
            "group_joint_accuracy": 0.0,
            "reward_disagreement": score["reward_disagreement"],
            "reward_disagreement_reason_code": score["reward_disagreement_reason_code"],
        })
    _log_shadow(reward_inputs, scores, training_rewards, None, format_weight,
                symbolic_grader_timeout_seconds, shadow_log_path, require_shadow_log)
    return outputs
