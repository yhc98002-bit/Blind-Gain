"""The ST3 arm-2 reward must have arm 1's reward SHAPE, differing only in the
intervention: joint (premise-gated) accuracy in place of member accuracy.

`pilot_reward.compute_score` -- what arm 1 runs -- returns
`(1 - fw) * accuracy + fw * format`. If arm 2 dropped the format term the two
arms would differ in two ways at once and the comparison would not isolate the
mechanism, so these fixtures pin the arithmetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.rewards import igpo_reward  # noqa: E402

MEMBERS = ("l3", "probe")


def batch(rollouts=1, groups=1):
    rows = []
    for g in range(groups):
        for r in range(rollouts):
            for member in MEMBERS:
                rows.append({"response": "x", "ground_truth": "1",
                             "pair_group_uid": f"g{g}", "pair_member": member,
                             "pair_rollout_index": r})
    return rows


def fake_scores(accuracy, fmt):
    def _scores(reward_inputs, timeout_seconds):
        return [{"response": "x", "ground_truth": "1",
                 "extracted": type("E", (), {"span": "1", "extraction_level": "t"})(),
                 "accuracy": a, "canonical_eval_reward": a, "format": f,
                 "mathruler_error": None, "reward_disagreement": 0.0,
                 "reward_disagreement_reason": "none",
                 "reward_disagreement_reason_code": 0}
                for a, f in zip(accuracy, fmt)]
    return _scores


def test_group_is_the_side_not_the_mother():
    assert igpo_reward.ST3_GROUP_MEMBERS == ("l3", "probe")


def test_joint_gates_the_read_on_the_premise(monkeypatch):
    rows = batch()
    # read right, probe wrong -> the read must not score
    monkeypatch.setattr(igpo_reward, "_member_scores", fake_scores([1.0, 0.0], [1.0, 1.0]))
    out = igpo_reward.compute_score(rows, format_weight=0.0)
    assert [o["overall"] for o in out] == pytest.approx([0.0, 0.0])
    assert [o["group_joint_accuracy"] for o in out] == pytest.approx([0.0, 0.0])
    # both right -> it scores
    monkeypatch.setattr(igpo_reward, "_member_scores", fake_scores([1.0, 1.0], [1.0, 1.0]))
    out = igpo_reward.compute_score(rows, format_weight=0.0)
    assert [o["overall"] for o in out] == pytest.approx([1.0, 1.0])


def test_reward_shape_matches_the_member_arm(monkeypatch):
    rows = batch()
    monkeypatch.setattr(igpo_reward, "_member_scores", fake_scores([1.0, 1.0], [1.0, 0.0]))
    joint = igpo_reward.compute_score(rows, format_weight=0.5)
    # (1-fw)*joint + fw*mean(format) = 0.5*1 + 0.5*0.5
    assert [o["overall"] for o in joint] == pytest.approx([0.75, 0.75])
    member = igpo_reward.compute_member_score(rows, format_weight=0.5)
    # the control keeps each member's OWN format, as pilot_reward does
    assert [o["overall"] for o in member] == pytest.approx([1.0, 0.5])


def test_format_weight_is_validated():
    with pytest.raises(ValueError, match="format_weight"):
        igpo_reward.compute_score(batch(), format_weight=1.5)


def test_incomplete_group_is_refused(monkeypatch):
    rows = [r for r in batch() if r["pair_member"] == "l3"]
    monkeypatch.setattr(igpo_reward, "_member_scores", fake_scores([1.0], [1.0]))
    with pytest.raises(ValueError, match="expected member set|full group"):
        igpo_reward.compute_score(rows)
