"""Fixtures for the k-ary intervention-group scoring used by ST3 arm 2.

Two properties matter most and each has a failing counterpart: the joint
reward must require EVERY member of the group (so a change-detector that only
gets the read step cannot score), and the k identical copies of one joint
outcome must not be counted as k independent GRPO samples.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.train.cp_grouping import (  # noqa: E402
    broadcast_joint_accuracy as binary_broadcast,
)
from src.train.hier_group_scoring import (  # noqa: E402
    broadcast_joint_accuracy,
    compute_group_level_grpo_advantage,
    repeated_group_metadata,
    source_grpo_uids,
    validate_group_rows,
)

ST3_MEMBERS = ("l3_a", "l3_b", "probe_a", "probe_b")


def group_batch(n_groups=2, rollouts=2, members=ST3_MEMBERS):
    uids, mems, idx = [], [], []
    for g in range(n_groups):
        for r in range(rollouts):
            for m in members:
                uids.append(f"g{g}")
                mems.append(m)
                idx.append(r)
    return uids, mems, idx


def test_joint_requires_every_member():
    uids, mems, idx = group_batch(n_groups=1, rollouts=1)
    all_right = broadcast_joint_accuracy([1, 1, 1, 1], uids, mems, idx)
    assert all_right.tolist() == [1, 1, 1, 1]
    # the read step right on both sides but the discovery step wrong -> zero
    one_probe_wrong = broadcast_joint_accuracy([1, 1, 1, 0], uids, mems, idx)
    assert one_probe_wrong.tolist() == [0, 0, 0, 0]


def test_binary_case_matches_the_pinned_implementation():
    uids = ["p", "p"]
    mems = ["a", "b"]
    idx = [0, 0]
    for scores in ([1, 1], [1, 0], [0, 0]):
        mine = broadcast_joint_accuracy(scores, uids, mems, idx)
        theirs = binary_broadcast(scores, uids, mems, idx)
        assert mine.tolist() == pytest.approx(theirs.tolist())


def test_incomplete_group_is_refused_against_the_declared_contract():
    # Every group missing the same member is invisible to inference, so the
    # ST3 reward passes its contract explicitly; that is what catches it.
    uids = ["g0"] * 3
    mems = ["l3_a", "l3_b", "probe_a"]          # probe_b missing everywhere
    with pytest.raises(ValueError, match="expected member set|full group"):
        broadcast_joint_accuracy([1, 1, 1], uids, mems, [0, 0, 0],
                                 expected_members=ST3_MEMBERS)


def test_members_repeat_across_rollouts_without_being_duplicates():
    # rollout.n > 1 means every member recurs once per rollout; treating that
    # as a duplicate would reject every real training batch.
    uids, mems, idx = group_batch(n_groups=1, rollouts=5)
    assert validate_group_rows(uids, mems, ST3_MEMBERS) == set(ST3_MEMBERS)
    joint = broadcast_joint_accuracy([1] * 20, uids, mems, idx,
                                     expected_members=ST3_MEMBERS)
    assert joint.tolist() == [1] * 20


def test_duplicate_member_within_one_rollout_is_refused():
    uids = ["g0"] * 4
    mems = ["l3_a", "l3_a", "probe_a", "probe_b"]
    with pytest.raises(ValueError, match="duplicate member"):
        broadcast_joint_accuracy([1, 1, 1, 1], uids, mems, [0, 0, 0, 0])


def test_groups_must_share_one_member_set():
    uids = ["g0"] * 4 + ["g1"] * 4
    mems = list(ST3_MEMBERS) + ["l3_a", "l3_b", "probe_a", "other"]
    with pytest.raises(ValueError, match="expected member set"):
        validate_group_rows(uids, mems)


def test_advantage_normalizes_unique_outcomes_not_copies():
    # one group, two rollouts: joint 1 then joint 0. Two UNIQUE outcomes, each
    # copied to 4 members. Normalizing over the 8 rows would be wrong.
    uids, mems, idx = group_batch(n_groups=1, rollouts=2)
    rewards = torch.tensor([[1.0], [1.0], [1.0], [1.0],
                            [0.0], [0.0], [0.0], [0.0]])
    mask = torch.ones_like(rewards)
    returns, _ = compute_group_level_grpo_advantage(rewards, mask, uids, mems, idx)
    values = returns.squeeze(-1)
    # every member of a rollout shares its advantage
    assert values[:4].tolist() == pytest.approx([values[0].item()] * 4)
    assert values[4:].tolist() == pytest.approx([values[4].item()] * 4)
    # normalization over the two unique outcomes: mean 0, symmetric
    assert values[0].item() == pytest.approx(-values[4].item(), rel=1e-3)
    expected = (torch.tensor([1.0, 0.0]) - 0.5) / (torch.std(torch.tensor([1.0, 0.0])) + 1e-6)
    assert values[0].item() == pytest.approx(expected[0].item(), rel=1e-3)


def test_advantage_refuses_unbroadcast_rewards():
    uids, mems, idx = group_batch(n_groups=1, rollouts=2)
    rewards = torch.tensor([[1.0], [0.0], [1.0], [1.0],
                            [0.0], [0.0], [0.0], [0.0]])
    with pytest.raises(ValueError, match="broadcast identically"):
        compute_group_level_grpo_advantage(rewards, torch.ones_like(rewards),
                                           uids, mems, idx)


def test_group_modes_choose_the_normalization_group():
    uids, mems, _ = group_batch(n_groups=1, rollouts=1)
    joint = source_grpo_uids(uids, mems, group_mode="joint")
    member = source_grpo_uids(uids, mems, group_mode="member")
    assert len(set(joint)) == 1          # the whole group normalizes together
    assert len(set(member)) == 4         # each member on its own


def test_repeated_metadata_matches_interleaved_rollouts():
    meta = repeated_group_metadata(["g0", "g0"], ["l3_a", "l3_b"], 3,
                                   group_mode="joint")
    assert meta["pair_group_uid"].tolist() == ["g0"] * 6
    assert meta["pair_member"].tolist() == ["l3_a"] * 3 + ["l3_b"] * 3
    assert meta["pair_rollout_index"].tolist() == [0, 1, 2, 0, 1, 2]
