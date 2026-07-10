from __future__ import annotations

from typing import Any, Iterable

import numpy as np


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
