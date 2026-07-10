from scripts.postprocess_vlmeval_predictions import score_mcq_prediction


def test_mcq_postprocessor_uses_final_span_and_format_decomposition() -> None:
    scored = score_mcq_prediction("Reasoning mentions B.\n<answer>A</answer>", "A", list("ABCD"))
    assert scored["acc_final"] is True
    assert scored["acc_strict"] is True
    assert scored["ambiguous"] is False


def test_mcq_postprocessor_marks_untagged_fallback_separately() -> None:
    scored = score_mcq_prediction("A", "A", list("ABCD"))
    assert scored["acc_final"] is True
    assert scored["acc_strict"] is False
    assert scored["format_valid"] is False


def test_mcq_postprocessor_rejects_multiple_winning_labels() -> None:
    scored = score_mcq_prediction("<answer>A or B</answer>", "A", list("ABCD"))
    assert scored["acc_final"] is False
    assert scored["ambiguous"] is True


def test_mcq_postprocessor_does_not_treat_article_as_option_a() -> None:
    scored = score_mcq_prediction(
        "D: The buildings beside a lake",
        "D",
        list("ABCD"),
        {"A": "sky", "B": "bridge", "C": "lake", "D": "buildings"},
    )
    assert scored["winning_labels"] == ["D"]
    assert scored["acc_final"] is True


def test_mcq_postprocessor_can_resolve_full_option_text() -> None:
    scored = score_mcq_prediction(
        "The buildings",
        "D",
        list("ABCD"),
        {"A": "The bridge", "B": "The lake", "C": "The skyline", "D": "The buildings"},
    )
    assert scored["winning_labels"] == ["D"]
    assert scored["acc_final"] is True
