from __future__ import annotations

from scripts.analyze_pilot_seed1_r19_null import (
    OTHER_PREDICTION_BUCKET,
    _existing_observed,
    chart_change_from_base,
    chart_member_diagnostics,
)


def _row(pair_id: str, answer_a: str, answer_b: str, prediction_a: str, prediction_b: str) -> dict:
    return {
        "pair_id": pair_id,
        "category": "chart_two_hop_read",
        "template_id": "starred_series_value_nine_v07",
        "answer_a": answer_a,
        "answer_b": answer_b,
        "prediction_a": prediction_a,
        "prediction_b": prediction_b,
    }


def test_chart_diagnostics_preserve_invalid_predictions_in_frequency_denominator() -> None:
    rows = [
        _row("p1", "10", "20", "<answer>10</answer>", "no tagged number"),
        _row("p2", "20", "10", "<answer>10</answer>", "<answer>10</answer>"),
    ]

    result = chart_member_diagnostics(rows)

    assert result["n_members"] == 4
    assert result["prediction_frequency"]["10"] == {"count": 3, "share": 0.75}
    assert result["prediction_frequency"][OTHER_PREDICTION_BUCKET] == {
        "count": 1,
        "share": 0.25,
    }
    assert result["accuracy_by_answer_value"]["10"]["accuracy"] == 1.0
    assert result["accuracy_by_answer_value"]["20"]["accuracy"] == 0.0


def test_chart_change_uses_step0_as_fixed_reference_for_both_diagnostics() -> None:
    base = chart_member_diagnostics(
        [_row("p1", "10", "20", "<answer>10</answer>", "<answer>10</answer>")]
    )
    checkpoint = chart_member_diagnostics(
        [_row("p1", "10", "20", "<answer>20</answer>", "<answer>20</answer>")]
    )

    change = chart_change_from_base(base, checkpoint)

    assert change["prediction_share_delta"]["10"] == -1.0
    assert change["prediction_share_delta"]["20"] == 1.0
    assert change["accuracy_delta_by_answer_value"]["10"] == -1.0
    assert change["accuracy_delta_by_answer_value"]["20"] == 1.0


def test_existing_observed_reads_the_frozen_seed1_field() -> None:
    readout = {
        "fliptrack_r19": {
            "arms": {
                "a1_real": {
                    "60": {
                        "category:chart_two_hop_read": {
                            "pair_accuracy_observed": 0.51,
                            "pair_accuracy_step0": 0.44,
                        }
                    }
                }
            }
        }
    }

    assert _existing_observed(readout, "a1_real", 60, "chart_two_hop_read") == 0.51
