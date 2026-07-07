from __future__ import annotations

import math
import random
import re
from collections.abc import Iterable
from typing import Any


def normalize_text(value: Any) -> str:
    text = str(value).strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"^[\"'`]+|[\"'`]+$", "", text)
    text = re.sub(r"[.,;:!?]+$", "", text)
    return text


def is_correct(prediction: Any, answer: Any) -> bool:
    pred = normalize_text(prediction)
    gold = normalize_text(answer)
    if pred == gold:
        return True
    if gold:
        if re.search(r"\w", gold):
            if re.search(rf"(?<!\w){re.escape(gold)}(?!\w)", pred):
                return True
        elif gold in pred:
            return True
    return gold in pred.split("\n")[-1].split(" | ")


def pair_score(row: dict[str, Any], pred_a_key: str = "prediction_a", pred_b_key: str = "prediction_b") -> dict[str, Any]:
    correct_a = is_correct(row.get(pred_a_key, ""), row["answer_a"])
    correct_b = is_correct(row.get(pred_b_key, ""), row["answer_b"])
    collapsed = normalize_text(row.get(pred_a_key, "")) == normalize_text(row.get(pred_b_key, ""))
    return {
        "pair_id": row.get("pair_id"),
        "correct_a": correct_a,
        "correct_b": correct_b,
        "pair_correct": correct_a and correct_b,
        "collapsed": collapsed and normalize_text(row["answer_a"]) != normalize_text(row["answer_b"]),
    }


def aggregate_pair_metrics(rows: Iterable[dict[str, Any]]) -> dict[str, float]:
    scores = [pair_score(row) for row in rows]
    if not scores:
        return {"n_pairs": 0, "member_accuracy": math.nan, "pair_accuracy": math.nan, "collapse_rate": math.nan}
    n = len(scores)
    member_correct = sum(score["correct_a"] + score["correct_b"] for score in scores)
    return {
        "n_pairs": float(n),
        "member_accuracy": member_correct / (2 * n),
        "pair_accuracy": sum(score["pair_correct"] for score in scores) / n,
        "collapse_rate": sum(score["collapsed"] for score in scores) / n,
    }


def bootstrap_ci(values: list[float], n_boot: int = 2000, alpha: float = 0.05, seed: int = 0) -> tuple[float, float]:
    if not values:
        return (math.nan, math.nan)
    rng = random.Random(seed)
    means = []
    for _ in range(n_boot):
        sample = [values[rng.randrange(len(values))] for _ in values]
        means.append(sum(sample) / len(sample))
    means.sort()
    lo = means[int((alpha / 2) * len(means))]
    hi = means[min(len(means) - 1, int((1 - alpha / 2) * len(means)))]
    return lo, hi


def pair_accuracy_ci(rows: Iterable[dict[str, Any]], n_boot: int = 2000, seed: int = 0) -> tuple[float, float]:
    values = [float(pair_score(row)["pair_correct"]) for row in rows]
    return bootstrap_ci(values, n_boot=n_boot, seed=seed)


def permutation_null_pair_accuracy(
    rows: list[dict[str, Any]],
    n_perm: int = 1000,
    seed: int = 0,
    pred_a_key: str = "prediction_a",
    pred_b_key: str = "prediction_b",
) -> dict[str, float]:
    rng = random.Random(seed)
    observed = aggregate_pair_metrics(rows)["pair_accuracy"]
    null = []
    for _ in range(n_perm):
        shuffled = []
        for row in rows:
            row = dict(row)
            if rng.random() < 0.5:
                row[pred_a_key], row[pred_b_key] = row.get(pred_b_key, ""), row.get(pred_a_key, "")
            shuffled.append(row)
        null.append(aggregate_pair_metrics(shuffled)["pair_accuracy"])
    p_ge = (sum(x >= observed for x in null) + 1) / (len(null) + 1)
    return {"observed": observed, "null_mean": sum(null) / len(null), "p_ge": p_ge}


def mcnemar_exact(rows_a: Iterable[dict[str, Any]], rows_b: Iterable[dict[str, Any]]) -> dict[str, float]:
    a_scores = {row.get("pair_id"): pair_score(row)["pair_correct"] for row in rows_a}
    b_scores = {row.get("pair_id"): pair_score(row)["pair_correct"] for row in rows_b}
    common = sorted(set(a_scores) & set(b_scores))
    b01 = sum((not a_scores[k]) and b_scores[k] for k in common)
    b10 = sum(a_scores[k] and (not b_scores[k]) for k in common)
    n = b01 + b10
    if n == 0:
        p = 1.0
    else:
        k = min(b01, b10)
        p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / (2**n))
    return {"n_common": float(len(common)), "b01": float(b01), "b10": float(b10), "p_value": p}
