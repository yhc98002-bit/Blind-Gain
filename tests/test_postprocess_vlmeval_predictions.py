import subprocess
import sys
from pathlib import Path

from scripts.postprocess_vlmeval_predictions import _choice_payload, score_mcq_prediction, score_open_prediction


def test_postprocessor_entrypoint_resolves_project_imports_outside_repo(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "postprocess_vlmeval_predictions.py"
    completed = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


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


def test_open_postprocessor_uses_numeric_equivalence_and_format_decomposition() -> None:
    tagged = score_open_prediction("<answer>1.0</answer>", "1")
    plain = score_open_prediction("Reasoning\n1.0", "1")
    assert tagged["acc_final"] is True and tagged["acc_strict"] is True
    assert plain["acc_final"] is True and plain["acc_strict"] is False


def test_mathvista_choice_payload_uses_serialized_choices_and_answer_option() -> None:
    payload = _choice_payload(
        {
            "answer": "145 degrees",
            "answer_option": "C",
            "choices": "['135 degrees', '140 degrees', '145 degrees', '150 degrees']",
        }
    )
    assert payload == (
        ["A", "B", "C", "D"],
        {"A": "135 degrees", "B": "140 degrees", "C": "145 degrees", "D": "150 degrees"},
        "C",
    )
