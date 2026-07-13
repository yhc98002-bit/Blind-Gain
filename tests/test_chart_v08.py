from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from src.fliptrack.render_chart_v08 import (
    COLORS,
    generate_chart_v08_pairs,
    minimum_palette_distance,
)


def test_chart_v08_has_two_uncued_two_hop_subfamilies(tmp_path: Path) -> None:
    rows = generate_chart_v08_pairs(tmp_path / "v08", n_per_subfamily=2, seed=31)

    assert len(rows) == 4
    assert {row["template_id"] for row in rows} == {
        "chart_v08_legend_target_flip",
        "chart_v08_point_value_flip",
    }
    for row in rows:
        verifier = row["verifier_results"]
        assert row["answer_a"] != row["answer_b"]
        assert verifier["answer_pointing_cue"] is False
        assert verifier["target_point_circled"] is False
        assert verifier["target_point_highlighted"] is False
        assert verifier["target_point_arrowed"] is False
        assert verifier["dual_coding"] is True
        assert verifier["series_count"] in {5, 6}
        assert Path(verifier["diagnostic_no_star_path"]).is_file()
        assert Path(verifier["diagnostic_random_star_path"]).is_file()
        with Image.open(row["changed_region_mask_a"]) as mask:
            assert np.any(np.asarray(mask) > 0)


def test_chart_v08_pair_mechanics_are_exact(tmp_path: Path) -> None:
    rows = generate_chart_v08_pairs(tmp_path / "v08", n_per_subfamily=3, seed=47)

    for row in rows:
        verifier = row["verifier_results"]
        values_a = verifier["values_a"]
        values_b = verifier["values_b"]
        if row["template_id"] == "chart_v08_legend_target_flip":
            assert values_a == values_b
            assert verifier["target_series_a"] != verifier["target_series_b"]
            assert verifier["mask_semantics"] == "star_region"
        else:
            changed = [
                (series_index, x_index)
                for series_index, (left, right) in enumerate(zip(values_a, values_b))
                for x_index, (value_a, value_b) in enumerate(zip(left, right))
                if value_a != value_b
            ]
            assert changed == [
                (verifier["target_series_a"], verifier["target_x"] - 1)
            ]
            assert verifier["target_series_a"] == verifier["target_series_b"]
            assert verifier["mask_semantics"] == "marker_and_affected_segments"


def test_chart_v08_palette_has_enforced_perceptual_separation() -> None:
    assert len(set(COLORS)) == 6
    assert minimum_palette_distance() >= 25.0
