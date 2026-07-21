from src.rewards.answer_reward import (
    PARSER_VERSION,
    answer_reward,
    answers_match,
    extract_answer_span,
    extract_final_answer,
    normalize_answer,
)
from src.rewards.cp_grpo_reward import compute_score as compute_cp_score


def test_extract_answer_tag_wins():
    assert extract_final_answer("reasoning\n<answer> 42 </answer>") == "42"


def test_extract_boxed_answer():
    assert extract_final_answer("Therefore \\boxed{17}.") == "17"


def test_extract_nested_boxed_answer():
    assert extract_final_answer("Therefore \\boxed{\\frac{1}{2}}.") == "\\frac{1}{2}"


def test_normalize_numeric_equivalence():
    assert answers_match("$1,200.00", "1200")
    assert answers_match("50%", "0.5")
    assert answers_match("1/2", "0.5")
    assert answers_match("\\boxed{\\frac{1}{2}}", "0.5")


def test_reward_is_binary():
    assert answer_reward("Final answer: left", "left") == 1.0
    assert answer_reward("Final answer: right", "left") == 0.0


def test_cp_pair_reward_requires_both_members():
    rows = [
        {
            "response": "left",
            "ground_truth": "left",
            "pair_group_uid": "pair-1",
            "pair_member": "a",
            "pair_rollout_index": 0,
        },
        {
            "response": "right",
            "ground_truth": "right",
            "pair_group_uid": "pair-1",
            "pair_member": "b",
            "pair_rollout_index": 0,
        },
    ]
    assert [item["overall"] for item in compute_cp_score(rows)] == [1.0, 1.0]
    rows[1]["response"] = "left"
    assert [item["overall"] for item in compute_cp_score(rows)] == [0.0, 0.0]


def test_normalize_strips_terminal_punctuation():
    assert normalize_answer(" Answer: Blue. ") == "blue"


def test_canonical_v2_normalizes_latex_presentation_wrappers():
    assert PARSER_VERSION == "canonical-v2"
    assert answers_match(r"<answer>\( \sqrt{21} \)</answer>", r"\sqrt { 21 }")
    assert answers_match(r"<answer>$\left(5\right)$</answer>", "(5)")
    assert answers_match(r"<answer>\text{5}</answer>", "5")
    assert extract_answer_span("<answer>1</answer>").parser_version == PARSER_VERSION


def test_canonical_v2_strips_only_compatible_or_unopposed_units():
    assert answers_match("<answer>5 meters</answer>", "5")
    assert answers_match("<answer>163 degrees</answer>", "163")
    assert answers_match(r"<answer>163^\circ</answer>", "163")
    assert answers_match(r"<answer>6\sqrt{2} inches</answer>", r"6 \sqrt 2")
    assert not answers_match("<answer>5 cm</answer>", "5 m")
    assert not answers_match(r"<answer>5\text{ cm}</answer>", r"5\text{ m}")


def test_canonical_v2_does_not_strip_answer_words_that_end_like_units():
    assert not answers_match("<answer>left</answer>", "le")
    assert not answers_match("<answer>diagram</answer>", "diagra")
