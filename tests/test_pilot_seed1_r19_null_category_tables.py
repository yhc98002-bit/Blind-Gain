from __future__ import annotations

import pytest

from scripts.render_pilot_seed1_r19_null_category_tables import combined_rows


def _fixtures() -> tuple[dict, dict]:
    cells = []
    arms = ("a1_real", "a2_gray", "a2b_noimage", "a3_caption")
    categories = ("chart", "document", "geometry")
    for arm in arms:
        for checkpoint in (0, 60, 100):
            for category in categories:
                cells.append(
                    {
                        "arm": arm,
                        "checkpoint": checkpoint,
                        "category_id": category,
                        "category_display_name": category,
                        "n_pairs": 1,
                        "observed_pair_accuracy": 0.4 if checkpoint == 0 else 0.5,
                        "null_mean": 0.2,
                        "p_value_ge_observed": 0.01,
                    }
                )
    readout = {"fliptrack_r19": {"arms": {}}}
    for arm in arms:
        readout["fliptrack_r19"]["arms"][arm] = {}
        for checkpoint in (60, 100):
            readout["fliptrack_r19"]["arms"][arm][str(checkpoint)] = {
                f"category:{category}": {
                    "pair_accuracy_step0": 0.4,
                    "pair_accuracy_observed": 0.5,
                    "delta_pair_accuracy": {"estimate": 0.1, "ci95": [0.0, 0.2]},
                }
                for category in categories
            }
    return {"key_shuffle_cells": cells}, readout


def test_combined_table_preserves_registered_delta_and_null_side_by_side() -> None:
    null_payload, readout = _fixtures()

    rows = combined_rows(null_payload, readout)

    assert len(rows) == 36
    checkpoint = next(row for row in rows if row["checkpoint"] == 60)
    assert checkpoint["delta_pair_accuracy"] == 0.1
    assert checkpoint["delta_ci95"] == [0.0, 0.2]
    assert checkpoint["null_mean"] == 0.2


def test_combined_table_rejects_observed_value_drift() -> None:
    null_payload, readout = _fixtures()
    readout["fliptrack_r19"]["arms"]["a1_real"]["60"]["category:chart"][
        "pair_accuracy_observed"
    ] = 0.6

    with pytest.raises(ValueError, match="mismatch"):
        combined_rows(null_payload, readout)
