"""Census staging fixtures (pre-freeze cleanup): the v3 census labeled every
hier_chart variant "L1" because the generic "chart" needle shadowed
"hier_chart" under first-substring-match ordering. Stages now derive from the
manifest rows' `layer` field first, derived artifacts are not capability
items, and the doc map falls back longest-needle-first."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_generator_census", ROOT / "scripts/build_generator_census.py")
CENSUS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CENSUS)


def test_shadowing_bug_is_dead_longest_needle_wins():
    stage, source = CENSUS.stage_of("hier_chart_v1_s5_low")
    assert stage == "L1/L2/L3"
    assert "registered_hier_benchmark_v1" in source


def test_plain_chart_doc_mapping_still_applies():
    stage, source = CENSUS.stage_of("chart_v08_legend_target")
    assert stage == "L1" and "chart = L1" in source
    # the starred-series chart-v08 template contains no mapped needle and
    # stays loudly unmapped, as in v2/v3
    stage, _ = CENSUS.stage_of("starred_series_value_nine_v07")
    assert stage == "unmapped"


def test_layer_field_beats_every_map():
    stage, source = CENSUS.stage_of_variant(
        "hier_chart_v1_s5_low", {"l3"},
        Path("data/hier_v1_dev/manifest_hier_chart_v1_s5_low_l3.jsonl"))
    assert stage == "L3" and "layer" in source
    stage, _ = CENSUS.stage_of_variant(
        "hier_coord_v1_n8", {"l1", "l2", "l3", "probe"},
        Path("data/x/manifest_hier_coord_v1_n8_all.jsonl"))
    assert stage == "L1/L2/L3/L3-probe"


def test_derived_artifacts_are_not_capability_items():
    for name in ("attacker_key_hier_chart_v1.jsonl",
                 "candidates_hier_chart_v1_s5_low_l3.jsonl",
                 "caption_stress_key_hier_coord_v1.jsonl"):
        stage, source = CENSUS.stage_of_variant(
            "hier_chart_v1_s5_low", set(), Path("data/hier_v1_dev") / name)
        assert stage == "derived-artifact", name
        assert "not a capability item" in source


def test_unmapped_stays_loud():
    stage, source = CENSUS.stage_of_variant(
        "totally_new_family_v1", set(), Path("data/x/manifest_new.jsonl"))
    assert stage == "unmapped" and "needs PI/doc mapping" in source
