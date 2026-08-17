"""Fixtures for matcher v3 (dispatch 2026-08-16b ruling 2): tier-1 containment
replaced by sign-aware parsed-numeric equality. Every case below is scored
WRONG by the old containment rule and right by v3, or is a legitimate lenient
match that must survive."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.eval.fliptrack_metrics import (  # noqa: E402
    MATCHER_VERSION,
    match_tier,
    pair_score,
)


def test_sign_collision_rejected():
    # the exact bug: 721/785 lenient credits in the hierarchy runs
    assert match_tier("-1", "1") == 0
    assert match_tier("<answer>-1</answer>", "1") == 0
    assert match_tier("-7", "7") == 0
    assert match_tier("1", "-1") == 0


def test_digit_containment_rejected():
    assert match_tier("15", "5") == 0
    assert match_tier("150", "5") == 0
    assert match_tier("-15", "5") == 0


def test_decimal_containment_rejected():
    assert match_tier("0.5", "5") == 0
    assert match_tier("5.5", "5") == 0


def test_exact_and_numeric_equivalence_still_tier_2():
    assert match_tier("5", "5") == 2
    assert match_tier("5.0", "5") == 2
    assert match_tier("-3", "-3") == 2


def test_legitimate_embedded_number_still_credited():
    # credit must survive; the exact tier may be 1 (lenient) or 2 (the
    # canonical matcher parses the span outright, e.g. "answer: 90")
    assert match_tier("x = 5 m", "5") == 1
    assert match_tier("the value is -3 units", "-3") == 1
    assert match_tier("answer: 90", "90") >= 1


def test_non_numeric_golds_keep_containment():
    assert match_tier("the series Harbor", "Harbor") == 1
    assert match_tier("Harbor", "Harbor") == 2
    assert match_tier("Harborside", "Harbor") == 0


def test_pair_score_stamps_matcher_version():
    row = {"pair_id": "p", "answer_a": "1", "answer_b": "4",
           "prediction_a": "<answer>-1</answer>", "prediction_b": "<answer>4</answer>"}
    scored = pair_score(row)
    assert scored["matcher_version"] == MATCHER_VERSION
    assert scored["parser_version"] == "canonical-v2"  # extractor unchanged
    assert scored["correct_a"] is False  # was True under containment
    assert scored["correct_b"] is True


def test_frozen_r20_copy_is_untouched():
    frozen = (ROOT / "src/fliptrack/frozen_r20/fliptrack_metrics.py").read_text()
    assert "MATCHER_VERSION" not in frozen
    assert "(?<!\\w)" in frozen  # the frozen snapshot keeps containment
