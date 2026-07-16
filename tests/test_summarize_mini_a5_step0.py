from __future__ import annotations

from pathlib import Path

from scripts.summarize_mini_a5_step0 import build_summary
from src.rewards.cp_grpo_reward import compute_member_score, compute_score


def _complete_pair_rows() -> list[dict[str, object]]:
    reward_inputs = []
    for member, ground_truth in (("a", "1"), ("b", "2")):
        for rollout_index in range(5):
            reward_inputs.append(
                {
                    "response": f"<answer>{ground_truth}</answer>",
                    "ground_truth": ground_truth,
                    "pair_group_uid": "p1",
                    "pair_member": member,
                    "pair_rollout_index": rollout_index,
                }
            )
    cp = compute_score(reward_inputs)
    member = compute_member_score(reward_inputs)
    return [
        {
            **reward_input,
            "template_id": "t1",
            "cp_joint_reward": cp_score["overall"],
            "member_reward": member_score["overall"],
            "reward_disagreement_reason_code": member_score[
                "reward_disagreement_reason_code"
            ],
            "sample_manifest_sha256": "sample",
            "format_prompt_sha256": "prompt",
            "model_revision": "model",
            "seed": 1,
            "rollout_n": 5,
            "temperature": 1.0,
            "top_p": 1.0,
            "max_tokens": 2048,
            "parser_version": "canonical-v2",
            "pilot_reward_version": "pilot-reward-v1",
            "cp_reward_version": "cp-grpo-reward-v1",
        }
        for reward_input, cp_score, member_score in zip(
            reward_inputs, cp, member, strict=True
        )
    ]


def test_incomplete_pair_returns_failed_summary_instead_of_crashing(tmp_path: Path) -> None:
    rows = _complete_pair_rows()[:-1]
    predictions = tmp_path / "predictions.jsonl"
    predictions.touch()
    summary = build_summary(rows, predictions)
    assert summary["status"] == "fail"
    assert not summary["checks"]["all_pairs_complete"]
    assert summary["overall"]["cp_unique_pair_outcomes"]["n"] == 0


def test_reward_tampering_is_detected(tmp_path: Path) -> None:
    rows = _complete_pair_rows()
    rows[0]["member_reward"] = 0.0
    predictions = tmp_path / "predictions.jsonl"
    predictions.touch()
    summary = build_summary(rows, predictions)
    assert summary["status"] == "fail"
    assert summary["reward_recompute_mismatches"] == 1
