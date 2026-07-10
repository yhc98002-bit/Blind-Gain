from __future__ import annotations

from typing import Any, Iterable

import random

import numpy as np

from src.decon.core import dhash, hamming, jaccard, normalize_text, phash, word_ngrams


def threshold_summary(
    positives: Iterable[float],
    negatives: Iterable[float],
    remove_threshold: float,
    inspect_threshold: float,
    higher_is_duplicate: bool,
) -> dict[str, Any]:
    positive = np.asarray(list(positives), dtype=np.float64)
    negative = np.asarray(list(negatives), dtype=np.float64)
    if not len(positive) or not len(negative):
        raise ValueError("calibration requires positive and negative examples")
    if higher_is_duplicate:
        remove_positive = positive >= remove_threshold
        inspect_positive = positive >= inspect_threshold
        remove_negative = negative >= remove_threshold
        inspect_negative = negative >= inspect_threshold
    else:
        remove_positive = positive <= remove_threshold
        inspect_positive = positive <= inspect_threshold
        remove_negative = negative <= remove_threshold
        inspect_negative = negative <= inspect_threshold
    return {
        "n_positive": int(len(positive)),
        "n_negative": int(len(negative)),
        "remove_threshold": remove_threshold,
        "inspect_threshold": inspect_threshold,
        "positive_remove_recall": float(remove_positive.mean()),
        "positive_inspect_recall": float(inspect_positive.mean()),
        "negative_remove_fpr": float(remove_negative.mean()),
        "negative_inspect_fpr": float(inspect_negative.mean()),
        "positive_quantiles": {
            str(q): float(np.quantile(positive, q)) for q in (0.0, 0.05, 0.5, 0.95, 1.0)
        },
        "negative_quantiles": {
            str(q): float(np.quantile(negative, q)) for q in (0.0, 0.05, 0.5, 0.95, 1.0)
        },
    }


def select_distinct_negatives(rows: list[dict[str, Any]], pool: list[dict[str, Any]], seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    negatives = []
    for row in rows:
        row_question = normalize_text(row["question"])
        row_shingles = word_ngrams(row["question"])
        row_p = int(row["phash64"], 16)
        row_d = int(row["dhash64"], 16)
        candidates = [
            candidate
            for candidate in pool
            if candidate["image_sha256"] != row["image_sha256"]
            and normalize_text(candidate["question"]) != row_question
            and jaccard(row_shingles, word_ngrams(candidate["question"])) < 0.3
            and min(
                hamming(row_p, int(candidate["phash64"], 16)),
                hamming(row_d, int(candidate["dhash64"], 16)),
            )
            > 10
        ]
        if not candidates:
            raise ValueError(f"no distinct calibration negative for {row['record_id']}")
        negatives.append(rng.choice(candidates))
    return negatives
