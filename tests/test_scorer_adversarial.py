from src.eval.fliptrack_metrics import pair_score
from src.rewards.answer_reward import extract_answer_span


def _row(prediction, answer_a="left", answer_b="right"):
    return {
        "pair_id": "p",
        "prediction_a": prediction,
        "prediction_b": "<answer>right</answer>",
        "answer_a": answer_a,
        "answer_b": answer_b,
    }


def test_question_echo_listing_options_does_not_win_without_final_answer():
    score = pair_score(_row("Question options: left or right."))
    assert score["correct_a"] is False
    assert score["extraction_level_a"] == "lastline"


def test_hedged_final_span_naming_both_golds_is_ambiguous():
    score = pair_score(_row("<answer>left or right</answer>"))
    assert score["correct_a"] is False
    assert score["ambiguous_a"] is True


def test_cot_mentions_both_then_unique_final_answer_is_correct_with_diagnostic():
    pred = "The options are left and right. I considered right.\nAnswer: left"
    score = pair_score(_row(pred))
    assert score["correct_a"] is True
    assert score["full_text_mentions_both_a"] is True


def test_nested_boxed_fraction_extracts_balanced_span():
    extracted = extract_answer_span(r"Work here. \boxed{\frac{1}{2}}")
    assert extracted.span == r"\frac{1}{2}"
    assert extracted.extraction_level == "boxed"


def test_strict_numeric_winner_is_not_ambiguous():
    row = {
        "pair_id": "p",
        "prediction_a": "<answer>7</answer>",
        "prediction_b": "<answer>7.5</answer>",
        "answer_a": "7",
        "answer_b": "7.5",
    }
    score = pair_score(row)
    assert score["correct_b"] is True
    assert score["ambiguous_b"] is False


def test_final_answer_can_contradict_reasoning_and_still_controls_score():
    pred = "The reasoning says right repeatedly.\nFinal answer: left"
    score = pair_score(_row(pred))
    assert score["correct_a"] is True


def test_empty_output_is_incorrect_fulltext_fallback():
    score = pair_score(_row(""))
    assert score["correct_a"] is False
    assert score["extraction_level_a"] == "fulltext"
    assert score["extraction_fallback_used_a"] is True


def test_format_only_output_with_no_answer_is_incorrect():
    score = pair_score(_row("Answer:"))
    assert score["correct_a"] is False
    assert score["extractor_valid_a"] is True
    assert score["contract_valid_a"] is False
    assert score["format_valid_a"] is False


def test_unparseable_rambling_with_both_golds_is_guarded_by_lastline():
    score = pair_score(_row("left right"))
    assert score["correct_a"] is False
    assert score["ambiguous_a"] is True


def test_boxed_answer_is_extractor_valid_but_not_registered_contract_valid():
    score = pair_score(_row(r"\boxed{left}"))
    assert score["correct_a"] is True
    assert score["extractor_valid_a"] is True
    assert score["contract_valid_a"] is False
    assert score["acc_strict_a"] is False


def test_scoring_rows_stamp_parser_and_prompt_contract_versions():
    score = pair_score(_row("<answer>left</answer>"))
    assert score["parser_version"] == "canonical-v2"
    assert score["prompt_contract_id"] == "answer-tags-v1"
    assert len(score["prompt_contract_sha256"]) == 64
