from src.decon.calibration import threshold_summary


def test_threshold_summary_separates_planted_duplicates_from_negatives() -> None:
    higher = threshold_summary([0.99, 0.97], [0.20, 0.40], 0.95, 0.90, higher_is_duplicate=True)
    assert higher["positive_remove_recall"] == 1.0
    assert higher["negative_inspect_fpr"] == 0.0

    lower = threshold_summary([0, 4], [20, 30], 6, 10, higher_is_duplicate=False)
    assert lower["positive_remove_recall"] == 1.0
    assert lower["negative_inspect_fpr"] == 0.0
