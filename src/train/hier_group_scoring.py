"""k-ary intervention-group scoring for ST3 (C2 + C3).

`src/train/cp_grouping.py` implements the same idea for BINARY pairs and is
pinned by `registered_mini_a5_gate1_completion_v1.md` (its launcher checks the
file against HEAD and the EasyR1 worktree diff is sha-pinned), so it is not
touched. This module generalises it to groups of arbitrary fixed size, which
is what ST3's arm 2 needs: an ST3 group is a mother-item's four members —
`l3_a, l3_b, probe_a, probe_b` — so the joint reward can require the model to
identify the right target AND read the right value on BOTH sides of the
counterfactual (C3, premise-verified hierarchical reward). With two members
and members {a, b} the semantics reduce exactly to the binary implementation.

The three pieces mirror cp_grouping:

* `source_grpo_uids`   — which rows share a GRPO normalization group
* `broadcast_joint_accuracy` — the joint outcome, copied to every member
* `compute_group_level_grpo_advantage` — normalize the G unique group
  outcomes, then broadcast, so the k copies of one joint reward are never
  counted as k independent samples.
"""
from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Sequence
from typing import Any

import torch

GROUP_MODES = frozenset({"none", "member", "joint"})


def _text_list(values: Sequence[Any], field: str) -> list[str]:
    out = []
    for value in values:
        if value is None:
            raise ValueError(f"{field} contains a null entry")
        out.append(str(value))
    return out


def group_member_sets(uids: Sequence[Any],
                      members: Sequence[Any]) -> dict[str, set[str]]:
    """uid -> its member set, refusing duplicates within a group."""
    uid_list = _text_list(uids, "pair_group_uid")
    member_list = _text_list(members, "pair_member")
    if len(uid_list) != len(member_list):
        raise ValueError("group uid and member sequences differ in length")
    seen: dict[str, set[str]] = defaultdict(set)
    for uid, member in zip(uid_list, member_list, strict=True):
        if member in seen[uid]:
            raise ValueError(f"duplicate member {member!r} in group {uid!r}")
        seen[uid].add(member)
    return dict(seen)


def validate_group_rows(uids: Sequence[Any], members: Sequence[Any],
                        expected_members: Sequence[str] | None = None) -> set[str]:
    """Every group must carry the identical member set. Returns that set.

    A group missing a member would silently weaken the joint reward (the
    product would run over fewer factors), which is exactly the failure the
    IGPO arm must not have.
    """
    sets = group_member_sets(uids, members)
    if not sets:
        raise ValueError("no groups present")
    if expected_members is not None:
        expected = set(_text_list(expected_members, "expected member"))
    else:
        expected = next(iter(sets.values()))
    malformed = {uid: sorted(found) for uid, found in sets.items()
                 if found != expected}
    if malformed:
        raise ValueError(
            f"groups do not carry the expected member set {sorted(expected)}: "
            f"{dict(list(malformed.items())[:4])}")
    return expected


def source_grpo_uids(uids: Sequence[Any], members: Sequence[Any],
                     *, group_mode: str) -> list[str]:
    """`joint` normalizes over the whole group; `member` keeps each member in
    its own normalization group (the matched control)."""
    if group_mode not in GROUP_MODES:
        raise ValueError(f"unknown group mode {group_mode!r}")
    uid_list = _text_list(uids, "pair_group_uid")
    member_list = _text_list(members, "pair_member")
    if group_mode == "joint":
        return list(uid_list)
    return ["member:" + json.dumps([uid, member], ensure_ascii=True,
                                   separators=(",", ":"))
            for uid, member in zip(uid_list, member_list, strict=True)]


def repeated_group_metadata(uids: Sequence[Any], members: Sequence[Any],
                            rollout_n: int, *, group_mode: str) -> dict[str, Any]:
    """Row metadata repeated across rollouts, matching EasyR1's
    `.repeat(interleave=True)` ordering."""
    import numpy as np

    if rollout_n < 1:
        raise ValueError("rollout_n must be positive")
    uid_list = _text_list(uids, "pair_group_uid")
    member_list = _text_list(members, "pair_member")
    group_uids = source_grpo_uids(uid_list, member_list, group_mode=group_mode)
    return {
        "uid": np.repeat(group_uids, rollout_n),
        "pair_group_uid": np.repeat(uid_list, rollout_n),
        "pair_member": np.repeat(member_list, rollout_n),
        "pair_rollout_index": np.tile(np.arange(rollout_n, dtype=np.int64),
                                      len(uid_list)),
    }


def broadcast_joint_accuracy(scores: Sequence[float], uids: Sequence[Any],
                             members: Sequence[Any],
                             rollout_indices: Sequence[int],
                             *, expected_members: Sequence[str] | None = None
                             ) -> torch.Tensor:
    """Return the product of member accuracies on every member of each
    (group, rollout) — the k-ary generalisation of acc(a)*acc(b).

    The key is (pair_group_uid, pair_rollout_index): the k-th rollout of every
    member is judged together, so the joint outcome is 1 only when the model
    got the whole intervention group right in the same sample.
    """
    values = torch.tensor([float(score) for score in scores], dtype=torch.float64)
    uid_list = _text_list(uids, "pair_group_uid")
    member_list = _text_list(members, "pair_member")
    indices = [int(value) for value in rollout_indices]
    if not (len(values) == len(uid_list) == len(member_list) == len(indices)):
        raise ValueError("joint-reward metadata does not align with scores")
    expected = validate_group_rows(uid_list, member_list, expected_members)

    grouped: dict[tuple[str, int], dict[str, int]] = defaultdict(dict)
    for row, (uid, member, rollout_index) in enumerate(
            zip(uid_list, member_list, indices, strict=True)):
        key = (uid, rollout_index)
        if member in grouped[key]:
            raise ValueError(f"duplicate member {member!r} for rollout {key!r}")
        grouped[key][member] = row

    output = torch.empty_like(values)
    for key, rows in grouped.items():
        if set(rows) != expected:
            raise ValueError(
                f"rollout {key!r} does not contain the full group "
                f"{sorted(expected)}; found {sorted(rows)}")
        joint = torch.prod(torch.stack([values[row] for row in rows.values()]))
        for row in rows.values():
            output[row] = joint
    return output


def compute_group_level_grpo_advantage(
    token_level_rewards: torch.Tensor,
    response_mask: torch.Tensor,
    pair_group_uids: Sequence[Any],
    pair_members: Sequence[Any],
    pair_rollout_indices: Sequence[int],
    *,
    eps: float = 1e-6,
    expected_members: Sequence[str] | None = None,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Normalize the G unique group outcomes, then broadcast to every member.

    Without this the k identical copies of one joint reward would be treated
    as k independent GRPO samples, shrinking the variance and inflating the
    advantage — the k-ary version of the concern cp_grouping documents.
    """
    if token_level_rewards.ndim != 2 or response_mask.shape != token_level_rewards.shape:
        raise ValueError("token rewards and response mask must have the same 2-D shape")
    scalar_rewards = token_level_rewards.sum(dim=-1)
    uid_list = _text_list(pair_group_uids, "pair_group_uid")
    member_list = _text_list(pair_members, "pair_member")
    indices = [int(value) for value in pair_rollout_indices]
    if not (len(scalar_rewards) == len(uid_list) == len(member_list) == len(indices)):
        raise ValueError("advantage metadata does not align with rewards")
    expected = validate_group_rows(uid_list, member_list, expected_members)

    grouped: dict[str, dict[int, dict[str, int]]] = defaultdict(lambda: defaultdict(dict))
    for row, (uid, member, rollout_index) in enumerate(
            zip(uid_list, member_list, indices, strict=True)):
        if member in grouped[uid][rollout_index]:
            raise ValueError(f"duplicate member {member!r} for {(uid, rollout_index)!r}")
        grouped[uid][rollout_index][member] = row

    normalized = torch.empty_like(scalar_rewards)
    for uid, rollouts in grouped.items():
        if len(rollouts) < 2:
            raise ValueError(f"group {uid!r} needs at least two rollout outcomes")
        ordered = sorted(rollouts)
        unique_rewards = []
        for rollout_index in ordered:
            rows = rollouts[rollout_index]
            if set(rows) != expected:
                raise ValueError(
                    f"rollout {(uid, rollout_index)!r} does not contain the full group")
            member_rewards = [scalar_rewards[row] for row in rows.values()]
            first = member_rewards[0]
            for reward in member_rewards[1:]:
                if not torch.equal(first, reward):
                    raise ValueError(
                        "joint reward was not broadcast identically for "
                        f"{(uid, rollout_index)!r}")
            unique_rewards.append(first)
        group_scores = torch.stack(unique_rewards)
        advantages = (group_scores - torch.mean(group_scores)) / (
            torch.std(group_scores) + eps)
        for offset, rollout_index in enumerate(ordered):
            for row in rollouts[rollout_index].values():
                normalized[row] = advantages[offset]

    returns = normalized.unsqueeze(-1) * response_mask
    return returns, returns
