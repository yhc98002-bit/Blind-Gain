"""I10 fixtures for the dev_v2 regeneration (dispatch 2026-08-16 item 4).

Two registered changes and nothing else: the answer-balance constraint
(registered_hier_benchmark_v1.md §8, cap 0.10 on pooled member-gold shares
per type) and branch (c)'s n=5 step for the easy variant
(registered_track4_premise_v2_design_v1.md §5). The pre-fix state fails
these fixtures: the v1 batch violates the balance cap (that is exactly E2's
constant-answer degeneracy), and no instrument carried an n=5 composition.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import scripts.build_track4_premise_v2_dev_batch as v1
import scripts.build_track4_premise_v2_dev_batch_v2 as v2
from scripts.build_track4_premise_v2_gate_readout import (
    COMPOSITION_BY_EXPECT,
    REGISTERED_COMPOSITION,
    REGISTERED_COMPOSITION_V2_BRANCH_C,
)

REPO = Path(__file__).resolve().parents[1]
V1_MANIFEST = REPO / "data/track4_premise_v2_dev_v1/manifest_causal_pairs.jsonl"


def _rows(golds_by_type: dict[str, list[tuple[str, str]]]) -> list[dict]:
    return [
        {"intervention_type": itype, "answer_a": a, "answer_b": b}
        for itype, pairs in golds_by_type.items()
        for a, b in pairs
    ]


def test_balance_report_fails_a_skewed_batch() -> None:
    """A constant-heavy gold distribution (the E2 degeneracy shape) fails."""
    skewed = _rows({"fact_read": [("3", "5")] * 15 + [("1", "2")] * 5})
    report = v2.balance_report(skewed, cap=0.10)
    assert report["fact_read"]["pass"] is False
    assert report["fact_read"]["max_share"] == 15 / 40
    assert report["all_pass"] is False


def test_balance_report_passes_a_balanced_batch() -> None:
    values = [str(v) for v in range(-7, 8) if v != 0]
    pairs = [(values[i % 14], values[(i + 7) % 14]) for i in range(20)]
    report = v2.balance_report(_rows({"fact_read": pairs}), cap=0.10)
    assert report["fact_read"]["pass"] is True
    assert report["all_pass"] is True


@pytest.mark.skipif(not V1_MANIFEST.exists(), reason="v1 batch not on this host")
def test_v1_batch_fails_the_registered_balance_constraint() -> None:
    """The adversarial fixture the OLD state fails: the declared v1 batch's
    final-answer distributions are exactly what E2 diagnosed."""
    rows = [json.loads(line) for line in V1_MANIFEST.read_text().splitlines() if line.strip()]
    report = v2.balance_report(rows, cap=0.10)
    assert report["all_pass"] is False, (
        "the v1 batch should violate the 0.10 cap — E2's constant-answer "
        "degeneracy came from precisely this imbalance"
    )


def test_v2_knobs_execute_branch_c_and_nothing_else() -> None:
    assert v2.N_POINTS_V2["chained_premise_easy"] == 5
    assert v2.N_POINTS_V2["premise_transition_easy"] == 5
    for itype in ("chained_premise", "premise_transition", "fact_read"):
        assert v2.N_POINTS_V2[itype] == 20
    assert v2.TEMPLATES_V2[5] == "t4v2_coordinate_register_n5_v1"
    assert v2.COUNTS_V2 == v1.COUNTS
    assert v2.BATCH_SEED_V2 != 20260806  # fresh scenes, disjoint from v1
    assert v2.BALANCE_CAP == 0.10


def test_readout_v2_composition_differs_only_in_the_easy_types() -> None:
    assert COMPOSITION_BY_EXPECT["registered"] is REGISTERED_COMPOSITION
    assert COMPOSITION_BY_EXPECT["registered-v2-branch-c"] is REGISTERED_COMPOSITION_V2_BRANCH_C
    for itype, spec in REGISTERED_COMPOSITION.items():
        spec_v2 = REGISTERED_COMPOSITION_V2_BRANCH_C[itype]
        assert spec_v2["groups"] == spec["groups"]
        assert spec_v2["has_premise"] == spec["has_premise"]
        if itype in ("chained_premise_easy", "premise_transition_easy"):
            assert spec_v2["n_points"] == 5
            assert spec_v2["template_id"] == "t4v2_coordinate_register_n5_v1"
        else:
            assert spec_v2["n_points"] == spec["n_points"]
            assert spec_v2["template_id"] == spec["template_id"]


def test_gate_instruments_parameterize_the_batch_dir_with_v1_defaults() -> None:
    gates = (REPO / "scripts/track4_premise_v2_gates.sh").read_text(encoding="utf-8")
    assert 'DATA="${GATES_DATA_DIR:-data/track4_premise_v2_dev_v1}"' in gates
    e3 = (REPO / "scripts/run_e3_caption_stress.sh").read_text(encoding="utf-8")
    assert 'DATA="${E3_DATA_DIR:-data/track4_premise_v2_dev_v1}"' in e3
    assert 'PROV_TAG="${E3_PROV_TAG:-v1}"' in e3
