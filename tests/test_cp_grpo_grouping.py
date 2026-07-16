from __future__ import annotations

import numpy as np
import pytest
import torch

from src.rewards.cp_grpo_reward import compute_member_score, compute_score
from src.train.cp_grouping import (
    broadcast_joint_accuracy,
    compute_pair_level_grpo_advantage,
    repeated_pair_metadata,
)


def _reward_input(
    uid: str, member: str, rollout: int, response: str, answer: str = "1"
) -> dict[str, object]:
    return {
        "response": response,
        "ground_truth": answer,
        "pair_group_uid": uid,
        "pair_member": member,
        "pair_rollout_index": rollout,
    }


def test_pair_reward_is_keyed_not_positionally_paired() -> None:
    rows = [
        _reward_input("p2", "b", 0, "<answer>1</answer>"),
        _reward_input("p1", "a", 0, "<answer>1</answer>"),
        _reward_input("p2", "a", 0, "<answer>0</answer>"),
        _reward_input("p1", "b", 0, "<answer>1</answer>"),
    ]

    scores = compute_score(rows)

    assert [score["overall"] for score in scores] == [0.0, 1.0, 0.0, 1.0]


def test_old_positional_pairing_fixture_now_fails_loudly() -> None:
    rows = [
        {"response": "<answer>1</answer>", "ground_truth": "1"},
        {"response": "<answer>1</answer>", "ground_truth": "1"},
    ]
    with pytest.raises(KeyError, match="pair_group_uid"):
        compute_score(rows)


@pytest.mark.parametrize(
    "members, message",
    [(["a"], "does not contain members a and b"), (["a", "a"], "duplicate member")],
)
def test_malformed_pair_rollouts_are_rejected(members: list[str], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        broadcast_joint_accuracy(
            [1.0] * len(members), ["p1"] * len(members), members, [0] * len(members)
        )


def test_repeated_metadata_uses_shared_uid_and_stable_rollout_index() -> None:
    metadata = repeated_pair_metadata(["p1", "p1"], ["a", "b"], rollout_n=3)
    assert metadata["uid"].tolist() == ["p1"] * 6
    assert metadata["pair_member"].tolist() == ["a", "a", "a", "b", "b", "b"]
    assert metadata["pair_rollout_index"].tolist() == [0, 1, 2, 0, 1, 2]


def test_validation_metadata_supports_one_greedy_response_per_member() -> None:
    metadata = repeated_pair_metadata(["p1", "p1"], ["a", "b"], rollout_n=1)
    assert metadata["uid"].tolist() == ["p1", "p1"]
    assert metadata["pair_rollout_index"].tolist() == [0, 0]


def test_pair_advantage_exactly_matches_unique_grpo_then_broadcast() -> None:
    pair_scores = torch.tensor([0.0, 1.0, 1.0, 0.0, 1.0])
    # Deliberately interleave and permute members to exercise metadata joins.
    order = [5, 0, 6, 1, 7, 2, 8, 3, 9, 4]
    duplicated = torch.cat([pair_scores, pair_scores])[order]
    members = np.array(["a"] * 5 + ["b"] * 5, dtype=object)[order]
    rollouts = np.array(list(range(5)) * 2, dtype=np.int64)[order]
    token_rewards = torch.zeros((10, 3), dtype=torch.float32)
    token_rewards[:, -1] = duplicated
    mask = torch.ones_like(token_rewards)

    advantages, returns = compute_pair_level_grpo_advantage(
        token_rewards,
        mask,
        ["p1"] * 10,
        members,
        rollouts,
    )

    expected_unique = (pair_scores - pair_scores.mean()) / (pair_scores.std() + 1e-6)
    expected = torch.cat([expected_unique, expected_unique])[order]
    assert torch.equal(advantages, returns)
    assert torch.allclose(advantages[:, 0], expected)
    assert torch.allclose(advantages[:, 1], expected)


def test_naive_duplicate_normalization_is_not_the_registered_equivalence() -> None:
    unique = torch.tensor([0.0, 1.0, 1.0, 0.0, 1.0])
    duplicated = torch.cat([unique, unique])
    unique_adv = (unique - unique.mean()) / (unique.std() + 1e-6)
    naive = (duplicated - duplicated.mean()) / (duplicated.std() + 1e-6)
    assert not torch.allclose(naive[:5], unique_adv)


def test_pair_advantage_rejects_unbroadcast_joint_reward() -> None:
    rewards = torch.tensor([[0.0], [1.0], [1.0], [1.0]])
    with pytest.raises(ValueError, match="not broadcast identically"):
        compute_pair_level_grpo_advantage(
            rewards,
            torch.ones_like(rewards),
            ["p1"] * 4,
            ["a", "b", "a", "b"],
            [0, 0, 1, 1],
        )


def test_same_data_control_uses_member_accuracy_only() -> None:
    rows = [
        _reward_input("p1", "a", 0, "<answer>1</answer>"),
        _reward_input("p1", "b", 0, "<answer>0</answer>"),
    ]
    scores = compute_member_score(rows)
    assert [score["overall"] for score in scores] == [1.0, 0.0]
    assert all(score["pair_joint_accuracy"] == 0.0 for score in scores)
