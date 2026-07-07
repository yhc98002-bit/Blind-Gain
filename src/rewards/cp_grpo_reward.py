from __future__ import annotations

from typing import Any

from src.rewards.answer_reward import answers_match


def cp_pair_reward(prediction_a: Any, answer_a: Any, prediction_b: Any, answer_b: Any) -> float:
    return 1.0 if answers_match(prediction_a, answer_a) and answers_match(prediction_b, answer_b) else 0.0


def batch_cp_pair_reward(rows: list[dict[str, Any]]) -> list[float]:
    required = {"prediction_a", "answer_a", "prediction_b", "answer_b"}
    rewards = []
    for row in rows:
        missing = required - row.keys()
        if missing:
            raise KeyError(f"missing CP-GRPO reward fields: {sorted(missing)}")
        rewards.append(cp_pair_reward(row["prediction_a"], row["answer_a"], row["prediction_b"], row["answer_b"]))
    return rewards

