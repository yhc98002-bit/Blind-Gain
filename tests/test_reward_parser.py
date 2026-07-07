from src.rewards.answer_reward import answer_reward, answers_match, extract_final_answer, normalize_answer
from src.rewards.cp_grpo_reward import cp_pair_reward


def test_extract_answer_tag_wins():
    assert extract_final_answer("reasoning\n<answer> 42 </answer>") == "42"


def test_extract_boxed_answer():
    assert extract_final_answer("Therefore \\boxed{17}.") == "17"


def test_normalize_numeric_equivalence():
    assert answers_match("$1,200.00", "1200")
    assert answers_match("50%", "0.5")
    assert answers_match("1/2", "0.5")


def test_reward_is_binary():
    assert answer_reward("Final answer: left", "left") == 1.0
    assert answer_reward("Final answer: right", "left") == 0.0


def test_cp_pair_reward_requires_both_members():
    assert cp_pair_reward("left", "left", "right", "right") == 1.0
    assert cp_pair_reward("left", "left", "left", "right") == 0.0


def test_normalize_strips_terminal_punctuation():
    assert normalize_answer(" Answer: Blue. ") == "blue"

