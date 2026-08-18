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
* `broadcast_group_mean`   — a per-member quantity averaged over the group,
  for terms that must stay broadcast-identical (the format term)
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
    """uid -> the DISTINCT members seen for that group.

    Deliberately not a duplicate check: with `rollout.n > 1` every member
    appears once per rollout, so duplicates are only meaningful at the
    (group, rollout) key — where `broadcast_joint_accuracy` and
    `compute_group_level_grpo_advantage` enforce them.
    """
    uid_list = _text_list(uids, "pair_group_uid")
    member_list = _text_list(members, "pair_member")
    if len(uid_list) != len(member_list):
        raise ValueError("group uid and member sequences differ in length")
    seen: dict[str, set[str]] = defaultdict(set)
    for uid, member in zip(uid_list, member_list, strict=True):
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
        # Inference can only catch groups that disagree with each other; a
        # batch where EVERY group is missing the same member is invisible.
        # Callers that know the group contract (the ST3 reward does) must pass
        # expected_members so an under-specified joint reward cannot slip by.
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


def _grouped_rows(uids: list[str], members: list[str], indices: list[int],
                  expected: set[str]) -> dict[tuple[str, int], dict[str, int]]:
    """(group, rollout) -> {member: row}, refusing duplicates and part-groups.

    The key is (pair_group_uid, pair_rollout_index): the k-th rollout of every
    member is judged together, so a group outcome reflects one coherent sample
    of the whole intervention group rather than a mix of rollouts.
    """
    grouped: dict[tuple[str, int], dict[str, int]] = defaultdict(dict)
    for row, (uid, member, rollout_index) in enumerate(
            zip(uids, members, indices, strict=True)):
        key = (uid, rollout_index)
        if member in grouped[key]:
            raise ValueError(f"duplicate member {member!r} for rollout {key!r}")
        grouped[key][member] = row
    for key, rows in grouped.items():
        if set(rows) != expected:
            raise ValueError(
                f"rollout {key!r} does not contain the full group "
                f"{sorted(expected)}; found {sorted(rows)}")
    return grouped


def _broadcast(scores: Sequence[float], uids: Sequence[Any], members: Sequence[Any],
               rollout_indices: Sequence[int], expected_members: Sequence[str] | None,
               reduce: str) -> torch.Tensor:
    values = torch.tensor([float(score) for score in scores], dtype=torch.float64)
    uid_list = _text_list(uids, "pair_group_uid")
    member_list = _text_list(members, "pair_member")
    indices = [int(value) for value in rollout_indices]
    if not (len(values) == len(uid_list) == len(member_list) == len(indices)):
        raise ValueError("group metadata does not align with scores")
    expected = validate_group_rows(uid_list, member_list, expected_members)
    grouped = _grouped_rows(uid_list, member_list, indices, expected)

    output = torch.empty_like(values)
    for rows in grouped.values():
        stacked = torch.stack([values[row] for row in rows.values()])
        if reduce == "product":
            reduced = torch.prod(stacked)
        elif reduce == "mean":
            reduced = torch.mean(stacked)
        else:
            raise ValueError(f"unknown reduction {reduce!r}")
        for row in rows.values():
            output[row] = reduced
    return output


def broadcast_joint_accuracy(scores: Sequence[float], uids: Sequence[Any],
                             members: Sequence[Any],
                             rollout_indices: Sequence[int],
                             *, expected_members: Sequence[str] | None = None
                             ) -> torch.Tensor:
    """Product of member accuracies, on every member of each (group, rollout).

    The k-ary generalisation of acc(a)*acc(b): 1 only when the model got the
    whole intervention group right within one sample.
    """
    return _broadcast(scores, uids, members, rollout_indices, expected_members,
                      "product")


def broadcast_group_mean(scores: Sequence[float], uids: Sequence[Any],
                         members: Sequence[Any], rollout_indices: Sequence[int],
                         *, expected_members: Sequence[str] | None = None
                         ) -> torch.Tensor:
    """Mean of a per-member quantity, broadcast to every member of the group.

    Used for the format term: a per-member format score would differ across
    members of one rollout, which `compute_group_level_grpo_advantage` refuses
    (the group reward must be broadcast identically). Averaging first keeps the
    reward shape of the member arm while staying broadcast-identical.
    """
    return _broadcast(scores, uids, members, rollout_indices, expected_members,
                      "mean")


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

    flat = _grouped_rows(uid_list, member_list, indices, expected)
    grouped: dict[str, dict[int, dict[str, int]]] = defaultdict(dict)
    for (uid, rollout_index), rows in flat.items():
        grouped[uid][rollout_index] = rows

    normalized = torch.empty_like(scalar_rewards)
    for uid, rollouts in grouped.items():
        if len(rollouts) < 2:
            raise ValueError(f"group {uid!r} needs at least two rollout outcomes")
        ordered = sorted(rollouts)
        unique_rewards = []
        for rollout_index in ordered:
            rows = rollouts[rollout_index]
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
