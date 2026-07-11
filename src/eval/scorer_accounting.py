from __future__ import annotations

from fractions import Fraction
from typing import Any, Iterable


def _rate(rows: list[dict[str, Any]], field: str) -> Fraction:
    if not rows:
        raise ValueError("scorer gain accounting requires nonempty row sets")
    return Fraction(sum(bool(row[field]) for row in rows), len(rows))


def strict_gain_decomposition(
    before: Iterable[dict[str, Any]], after: Iterable[dict[str, Any]]
) -> dict[str, Fraction]:
    before = list(before)
    after = list(after)
    answer_gain = _rate(after, "acc_final") - _rate(before, "acc_final")
    strict_gain = _rate(after, "acc_strict") - _rate(before, "acc_strict")
    g_format = (
        _rate(after, "acc_strict")
        - _rate(after, "acc_final")
        - _rate(before, "acc_strict")
        + _rate(before, "acc_final")
    )
    if strict_gain != answer_gain + g_format:
        raise AssertionError("StrictGain accounting identity is violated")
    return {
        "StrictGain": strict_gain,
        "AnswerGain": answer_gain,
        "G_format": g_format,
    }
