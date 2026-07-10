from src.decon.calibration import select_distinct_negatives, threshold_summary
from src.decon.ocr_calibration import calibrate_ocr_pairs


def test_threshold_summary_separates_planted_duplicates_from_negatives() -> None:
    higher = threshold_summary([0.99, 0.97], [0.20, 0.40], 0.95, 0.90, higher_is_duplicate=True)
    assert higher["positive_remove_recall"] == 1.0
    assert higher["negative_inspect_fpr"] == 0.0

    lower = threshold_summary([0, 4], [20, 30], 6, 10, higher_is_duplicate=False)
    assert lower["positive_remove_recall"] == 1.0
    assert lower["negative_inspect_fpr"] == 0.0


def test_negative_sampler_rejects_identical_generic_questions() -> None:
    source = {
        "record_id": "source",
        "image_sha256": "a",
        "question": "Find x.",
        "phash64": "0000000000000000",
        "dhash64": "0000000000000000",
    }
    duplicate_question = {
        "record_id": "bad",
        "image_sha256": "b",
        "question": "FIND X!",
        "phash64": "ffffffffffffffff",
        "dhash64": "ffffffffffffffff",
    }
    distinct = {
        "record_id": "good",
        "image_sha256": "c",
        "question": "Which animal appears in the photograph?",
        "phash64": "ffffffffffffffff",
        "dhash64": "ffffffffffffffff",
    }
    selected = select_distinct_negatives([source], [duplicate_question, distinct], seed=7)
    assert [row["record_id"] for row in selected] == ["good"]


def test_ocr_calibration_reports_eligible_planted_and_negative_pairs() -> None:
    pairs = [
        {
            "source_image_sha256": "source",
            "transformed_image_sha256": "positive",
            "negative_image_sha256": "negative",
        }
    ]
    entries = [
        {"image_sha256": "source", "text": "Triangle ABC angle forty two", "line_count": 2},
        {"image_sha256": "positive", "text": "Triangle ABC angle forty two", "line_count": 2},
        {"image_sha256": "negative", "text": "Invoice total seven hundred dollars", "line_count": 2},
    ]
    result = calibrate_ocr_pairs(pairs, entries)
    assert result["eligible_positive_pairs"] == 1
    assert result["eligible_negative_pairs"] == 1
    assert result["ocr_char5_jaccard"]["positive_remove_recall"] == 1.0
    assert result["ocr_char5_jaccard"]["negative_inspect_fpr"] == 0.0
