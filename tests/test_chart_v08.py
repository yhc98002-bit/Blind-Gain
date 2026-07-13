from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from src.fliptrack.render_chart_v08 import (
    COLORS,
    adjacent_crossing_count,
    generate_chart_v08_pairs,
    minimum_palette_distance,
    palette_distance_report,
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
        assert verifier["diagnostic_contract_version"] == "chart-v08-necessity-v2"
        assert verifier["diagnostic_scoring_rule"] == (
            "score_each_intervention_against_original_member_answer"
        )
        for member in ("a", "b"):
            assert Path(verifier[f"diagnostic_no_star_{member}_path"]).is_file()
            assert Path(verifier[f"diagnostic_random_star_{member}_path"]).is_file()
            assert verifier[f"diagnostic_random_implied_answer_{member}"] != int(
                row[f"answer_{member}"]
            )
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
        target_x = verifier["target_x"] - 1
        assert verifier["adjacent_crossing_count_a"] == adjacent_crossing_count(
            values_a, target_x
        )
        assert verifier["adjacent_crossing_count_b"] == adjacent_crossing_count(
            values_b, target_x
        )


def test_chart_v08_palette_has_enforced_perceptual_separation() -> None:
    assert len(set(COLORS)) == 6
    assert minimum_palette_distance() >= 25.0
    distances = palette_distance_report()
    assert distances["normal"] >= 25.0
    assert min(value for mode, value in distances.items() if mode != "normal") >= 15.0


def test_chart_v08_refuses_to_overwrite_generated_artifacts(tmp_path: Path) -> None:
    output = tmp_path / "v08"
    rows = generate_chart_v08_pairs(output, n_per_subfamily=1, seed=59)
    first_image = Path(rows[0]["image_a_path"])
    original = first_image.read_bytes()

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        generate_chart_v08_pairs(output, n_per_subfamily=1, seed=59)

    assert first_image.read_bytes() == original
