from __future__ import annotations

import math
import random
import re
from collections import defaultdict
from collections.abc import Iterable, Sequence
from typing import Any

from src.rewards.answer_reward import extract_answer_span, normalize_text, numeric_value


def match_tier(span: Any, answer: Any, numeric_tol: float = 1e-4) -> int:
    pred = normalize_text(span)
    gold = normalize_text(answer)
    if not pred or not gold:
        return 0
    if pred == gold:
        return 2
    pred_num = numeric_value(pred)
    gold_num = numeric_value(gold)
    if pred_num is not None and gold_num is not None and math.isclose(pred_num, gold_num, rel_tol=numeric_tol, abs_tol=numeric_tol):
        return 2
    if re.search(r"\w", gold):
        if re.search(rf"(?<!\w){re.escape(gold)}(?!\w)", pred):
            return 1
    elif gold in pred:
        return 1
    return 0


def is_correct(prediction: Any, answer: Any) -> bool:
    return match_tier(extract_answer_span(prediction).span, answer) > 0


def _score_member(
    prediction: Any,
    gold: Any,
    other_gold: Any,
    prefix: str,
) -> dict[str, Any]:
    extracted = extract_answer_span(prediction)
    span = extracted.span
    gold_tier = match_tier(span, gold)
    other_tier = match_tier(span, other_gold)
    highest = max(gold_tier, other_tier)
    ambiguous = highest > 0 and gold_tier == other_tier
    acc_final = gold_tier > other_tier and gold_tier > 0
    acc_strict = extracted.format_valid and acc_final
    full_tier_gold = match_tier(prediction, gold)
    full_tier_other = match_tier(prediction, other_gold)
    full_text_mentions_both = full_tier_gold > 0 and full_tier_other > 0
    return {
        f"extracted_answer_{prefix}": span,
        f"extraction_level_{prefix}": extracted.extraction_level,
        f"extraction_fallback_used_{prefix}": extracted.extraction_fallback_used,
        f"format_valid_{prefix}": extracted.format_valid,
        f"ambiguous_{prefix}": ambiguous,
        f"full_text_mentions_both_{prefix}": full_text_mentions_both,
        f"match_tier_{prefix}": gold_tier,
        f"other_match_tier_{prefix}": other_tier,
        f"acc_final_{prefix}": acc_final,
        f"acc_strict_{prefix}": acc_strict,
    }


def pair_score(row: dict[str, Any], pred_a_key: str = "prediction_a", pred_b_key: str = "prediction_b") -> dict[str, Any]:
    side_a = _score_member(row.get(pred_a_key, ""), row["answer_a"], row["answer_b"], "a")
    side_b = _score_member(row.get(pred_b_key, ""), row["answer_b"], row["answer_a"], "b")
    correct_a = bool(side_a["acc_final_a"])
    correct_b = bool(side_b["acc_final_b"])
    strict_a = bool(side_a["acc_strict_a"])
    strict_b = bool(side_b["acc_strict_b"])
    collapsed = normalize_text(side_a["extracted_answer_a"]) == normalize_text(side_b["extracted_answer_b"])
    scored = {
        "pair_id": row.get("pair_id"),
        "correct_a": correct_a,
        "correct_b": correct_b,
        "strict_correct_a": strict_a,
        "strict_correct_b": strict_b,
        "pair_correct": correct_a and correct_b,
        "strict_pair_correct": strict_a and strict_b,
        "collapsed": collapsed and normalize_text(row["answer_a"]) != normalize_text(row["answer_b"]),
        "acc_final": correct_a and correct_b,
        "acc_strict": strict_a and strict_b,
        "format_valid": bool(side_a["format_valid_a"] and side_b["format_valid_b"]),
        "ambiguous": bool(side_a["ambiguous_a"] or side_b["ambiguous_b"]),
        "full_text_mentions_both": bool(side_a["full_text_mentions_both_a"] or side_b["full_text_mentions_both_b"]),
        "extraction_fallback_used": bool(side_a["extraction_fallback_used_a"] or side_b["extraction_fallback_used_b"]),
        "extraction_level": f"{side_a['extraction_level_a']}|{side_b['extraction_level_b']}",
    }
    scored.update(side_a)
    scored.update(side_b)
    return scored


def aggregate_pair_metrics(rows: Iterable[dict[str, Any]]) -> dict[str, float]:
    scores = [pair_score(row) for row in rows]
    if not scores:
        return {
            "n_pairs": 0,
            "member_accuracy": math.nan,
            "pair_accuracy": math.nan,
            "strict_member_accuracy": math.nan,
            "strict_pair_accuracy": math.nan,
            "collapse_rate": math.nan,
            "ambiguous_rate": math.nan,
            "full_text_mentions_both_rate": math.nan,
            "format_valid_rate": math.nan,
            "extraction_fallback_rate": math.nan,
        }
    n = len(scores)
    member_correct = sum(score["correct_a"] + score["correct_b"] for score in scores)
    strict_member_correct = sum(score["strict_correct_a"] + score["strict_correct_b"] for score in scores)
    return {
        "n_pairs": float(n),
        "member_accuracy": member_correct / (2 * n),
        "pair_accuracy": sum(score["pair_correct"] for score in scores) / n,
        "strict_member_accuracy": strict_member_correct / (2 * n),
        "strict_pair_accuracy": sum(score["strict_pair_correct"] for score in scores) / n,
        "collapse_rate": sum(score["collapsed"] for score in scores) / n,
        "ambiguous_rate": sum(score["ambiguous"] for score in scores) / n,
        "full_text_mentions_both_rate": sum(score["full_text_mentions_both"] for score in scores) / n,
        "format_valid_rate": sum(score["format_valid_a"] + score["format_valid_b"] for score in scores) / (2 * n),
        "extraction_fallback_rate": sum(score["extraction_fallback_used_a"] + score["extraction_fallback_used_b"] for score in scores) / (2 * n),
    }


def aggregate_pair_metrics_by_template(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, float]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("template_id", "unknown"))].append(row)
    return {template: aggregate_pair_metrics(template_rows) for template, template_rows in sorted(grouped.items())}


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


def template_key_shuffle_null_pair_accuracy(
    rows: Sequence[dict[str, Any]],
    n_perm: int = 1000,
    seed: int = 0,
) -> dict[str, float]:
    rows = [dict(row) for row in rows]
    rng = random.Random(seed)
    observed = aggregate_pair_metrics(rows)["pair_accuracy"]
    by_template: dict[str, list[int]] = defaultdict(list)
    for idx, row in enumerate(rows):
        by_template[str(row.get("template_id", ""))].append(idx)
    null = []
    for _ in range(n_perm):
        shuffled = [dict(row) for row in rows]
        for indices in by_template.values():
            keys = [(rows[idx]["answer_a"], rows[idx]["answer_b"]) for idx in indices]
            rng.shuffle(keys)
            for idx, (answer_a, answer_b) in zip(indices, keys):
                shuffled[idx]["answer_a"] = answer_a
                shuffled[idx]["answer_b"] = answer_b
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
