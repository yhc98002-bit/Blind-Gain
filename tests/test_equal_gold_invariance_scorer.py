"""Adversarial fixture for P0.2 — the equal-gold invariance scorer.

The pre-fix scorer computed, for every member:

    acc_final = gold_tier > other_tier and gold_tier > 0

On an invariance item the two members share one gold, so `gold_tier` and
`other_tier` are computed from the same string and `gold_tier > other_tier` is
never true. Every response scored wrong regardless of content, and every match
was flagged ambiguous. These cases fail on the pre-fix code and pass after it.

Causal pairs (distinct golds) must be completely unaffected -- R19 contains no
equal-gold pairs, so no Paper-1 result may move. The last two cases lock that in.
"""
from src.eval.fliptrack_metrics import golds_equivalent, pair_score

CONTRACT = None


def _row(pred_a, pred_b, gold_a, gold_b):
    return {
        "pair_id": "fixture",
        "prediction_a": pred_a,
        "prediction_b": pred_b,
        "answer_a": gold_a,
        "answer_b": gold_b,
    }


def test_equal_gold_correct_answer_scores_correct():
    """THE regression: both members right on a shared gold must score correct."""
    s = pair_score(_row("<answer>7</answer>", "<answer>7</answer>", "7", "7"), prompt_contract=CONTRACT)
    assert s["correct_a"] is True, "pre-fix scorer returns False here"
    assert s["correct_b"] is True, "pre-fix scorer returns False here"
    assert s["pair_correct"] is True
    assert s["ambiguous"] is False, "pre-fix scorer flags every equal-gold match ambiguous"


def test_equal_gold_wrong_answer_still_scores_wrong():
    """The fix must not turn the scorer into a rubber stamp."""
    s = pair_score(_row("<answer>4</answer>", "<answer>9</answer>", "7", "7"), prompt_contract=CONTRACT)
    assert s["correct_a"] is False
    assert s["correct_b"] is False
    assert s["pair_correct"] is False


def test_equal_gold_one_member_wrong_fails_the_pair():
    s = pair_score(_row("<answer>7</answer>", "<answer>4</answer>", "7", "7"), prompt_contract=CONTRACT)
    assert s["correct_a"] is True
    assert s["correct_b"] is False
    assert s["pair_correct"] is False


def test_numerically_equal_golds_count_as_equal():
    """'3' and '3.0' are one gold, not two competing ones."""
    assert golds_equivalent("3", "3.0") is True
    s = pair_score(_row("<answer>3</answer>", "<answer>3.0</answer>", "3", "3.0"), prompt_contract=CONTRACT)
    assert s["pair_correct"] is True


def test_equal_gold_flag_is_exposed():
    s = pair_score(_row("<answer>7</answer>", "<answer>7</answer>", "7", "7"), prompt_contract=CONTRACT)
    assert s["equal_gold_a"] is True and s["equal_gold_b"] is True


def test_causal_pair_discrimination_is_unchanged():
    """Distinct golds keep the discriminative criterion -- R19 must not move."""
    s = pair_score(_row("<answer>3</answer>", "<answer>-1</answer>", "3", "-1"), prompt_contract=CONTRACT)
    assert s["pair_correct"] is True
    assert s["equal_gold_a"] is False

    # answering the other member's gold is still wrong on a causal pair
    swapped = pair_score(_row("<answer>-1</answer>", "<answer>3</answer>", "3", "-1"), prompt_contract=CONTRACT)
    assert swapped["correct_a"] is False
    assert swapped["correct_b"] is False


def test_causal_pair_ambiguity_guard_survives():
    """A response naming both golds stays ambiguous and uncredited."""
    s = pair_score(_row("<answer>3 or -1</answer>", "<answer>3 or -1</answer>", "3", "-1"), prompt_contract=CONTRACT)
    assert s["ambiguous"] is True
    assert s["pair_correct"] is False
