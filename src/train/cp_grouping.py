from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from typing import Any

import numpy as np
import torch


PAIR_MEMBERS = frozenset({"a", "b"})


def _text_list(values: Sequence[Any], name: str) -> list[str]:
    result = [str(value) for value in values]
    if not result or any(not value for value in result):
        raise ValueError(f"{name} must be nonempty strings")
    return result


def validate_pair_rows(pair_group_uids: Sequence[Any], pair_members: Sequence[Any]) -> None:
    """Require exactly one A and one B source row for every training pair."""

    uids = _text_list(pair_group_uids, "pair_group_uid")
    members = _text_list(pair_members, "pair_member")
    if len(uids) != len(members):
        raise ValueError("pair_group_uid and pair_member lengths differ")
    grouped: dict[str, list[str]] = defaultdict(list)
    for uid, member in zip(uids, members, strict=True):
        if member not in PAIR_MEMBERS:
            raise ValueError(f"pair {uid!r} has invalid member {member!r}")
        grouped[uid].append(member)
    malformed = {
        uid: sorted(observed)
        for uid, observed in grouped.items()
        if sorted(observed) != ["a", "b"]
    }
    if malformed:
        raise ValueError(f"each pair must contain exactly members a and b: {malformed}")


def repeated_pair_metadata(
    pair_group_uids: Sequence[Any], pair_members: Sequence[Any], rollout_n: int
) -> dict[str, np.ndarray]:
    """Create shared GRPO ids and stable rollout indices before batch reordering."""

    if rollout_n < 1:
        raise ValueError("pair rollout count must be positive")
    validate_pair_rows(pair_group_uids, pair_members)
    uids = np.asarray([str(value) for value in pair_group_uids], dtype=object)
    members = np.asarray([str(value) for value in pair_members], dtype=object)
    return {
        "uid": np.repeat(uids, rollout_n),
        "pair_group_uid": np.repeat(uids, rollout_n),
        "pair_member": np.repeat(members, rollout_n),
        "pair_rollout_index": np.tile(np.arange(rollout_n, dtype=np.int64), len(uids)),
    }


def broadcast_joint_accuracy(
    member_accuracy: Sequence[float] | torch.Tensor,
    pair_group_uids: Sequence[Any],
    pair_members: Sequence[Any],
    pair_rollout_indices: Sequence[int],
) -> torch.Tensor:
    """Return acc(a_i) * acc(b_i) on both members of every paired rollout."""

    scores = torch.as_tensor(member_accuracy, dtype=torch.float32)
    uids = _text_list(pair_group_uids, "pair_group_uid")
    members = _text_list(pair_members, "pair_member")
    indices = [int(value) for value in pair_rollout_indices]
    if not (scores.ndim == 1 and len(scores) == len(uids) == len(members) == len(indices)):
        raise ValueError("pair reward inputs must be aligned one-dimensional arrays")

    grouped: dict[tuple[str, int], dict[str, int]] = defaultdict(dict)
    for row, (uid, member, rollout_index) in enumerate(
        zip(uids, members, indices, strict=True)
    ):
        if member not in PAIR_MEMBERS:
            raise ValueError(f"pair {uid!r} has invalid member {member!r}")
        key = (uid, rollout_index)
        if member in grouped[key]:
            raise ValueError(f"duplicate member {member!r} for paired rollout {key!r}")
        grouped[key][member] = row

    output = torch.empty_like(scores)
    for key, rows in grouped.items():
        if set(rows) != PAIR_MEMBERS:
            raise ValueError(f"paired rollout {key!r} does not contain members a and b")
        joint = scores[rows["a"]] * scores[rows["b"]]
        output[rows["a"]] = joint
        output[rows["b"]] = joint
    return output


def compute_pair_level_grpo_advantage(
    token_level_rewards: torch.Tensor,
    response_mask: torch.Tensor,
    pair_group_uids: Sequence[Any],
    pair_members: Sequence[Any],
    pair_rollout_indices: Sequence[int],
    *,
    eps: float = 1e-6,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Normalize unique pair outcomes, then broadcast advantages to both members.

    This avoids treating the two copies of each joint reward as independent samples.
    The result is exactly the ordinary EasyR1 GRPO normalization over the G unique
    pair outcomes, copied to A and B.
    """

    if token_level_rewards.ndim != 2 or response_mask.shape != token_level_rewards.shape:
        raise ValueError("token rewards and response mask must have the same 2-D shape")
    scalar_rewards = token_level_rewards.sum(dim=-1)
    uids = _text_list(pair_group_uids, "pair_group_uid")
    members = _text_list(pair_members, "pair_member")
    indices = [int(value) for value in pair_rollout_indices]
    if len(scalar_rewards) != len(uids) or len(uids) != len(members) or len(uids) != len(indices):
        raise ValueError("advantage metadata does not align with rewards")

    grouped: dict[str, dict[int, dict[str, int]]] = defaultdict(lambda: defaultdict(dict))
    for row, (uid, member, rollout_index) in enumerate(
        zip(uids, members, indices, strict=True)
    ):
        if member not in PAIR_MEMBERS:
            raise ValueError(f"pair {uid!r} has invalid member {member!r}")
        if member in grouped[uid][rollout_index]:
            raise ValueError(
                f"duplicate member {member!r} for paired rollout {(uid, rollout_index)!r}"
            )
        grouped[uid][rollout_index][member] = row

    normalized = torch.empty_like(scalar_rewards)
    for uid, rollouts in grouped.items():
        if len(rollouts) < 2:
            raise ValueError(f"pair group {uid!r} needs at least two rollout outcomes")
        ordered_indices = sorted(rollouts)
        unique_rewards: list[torch.Tensor] = []
        for rollout_index in ordered_indices:
            rows = rollouts[rollout_index]
            if set(rows) != PAIR_MEMBERS:
                raise ValueError(
                    f"paired rollout {(uid, rollout_index)!r} does not contain members a and b"
                )
            reward_a = scalar_rewards[rows["a"]]
            reward_b = scalar_rewards[rows["b"]]
            if not torch.equal(reward_a, reward_b):
                raise ValueError(
                    f"joint reward was not broadcast identically for {(uid, rollout_index)!r}"
                )
            unique_rewards.append(reward_a)
        pair_scores = torch.stack(unique_rewards)
        mean = torch.mean(pair_scores)
        std = torch.std(pair_scores)
        pair_advantages = (pair_scores - mean) / (std + eps)
        for offset, rollout_index in enumerate(ordered_indices):
            rows = rollouts[rollout_index]
            normalized[rows["a"]] = pair_advantages[offset]
            normalized[rows["b"]] = pair_advantages[offset]

    returns = normalized.unsqueeze(-1) * response_mask
    return returns, returns
