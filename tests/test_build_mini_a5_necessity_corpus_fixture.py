"""Adversarial fixtures (I10) for the Mini-A5 arm-3 necessity resample.

Each fixture plants the output a naive implementation of section 2 R2 of
docs/registered_mini_a5_gate1_completion_v1.md would produce, and requires
audit_necessity_resample to reject it. The registered construction is the
positive control and must pass, including the empirical draw-frequency audit.
"""
from __future__ import annotations

import copy

import numpy as np
import pytest

from scripts.build_mini_a5_necessity_corpus import (
    BUILD_SEED,
    COLUMNS,
    FLOOR_WEIGHT,
    SYNTHETIC_UID_PREFIX,
    audit_necessity_resample,
    build_delta_q_records,
    compute_weight,
    draw_indices,
    materialize_rows,
    parquet_bytes,
)

ITEM_COUNT = 600
TEMPLATES = ("fixture_template_a", "fixture_template_b", "fixture_template_c")


@pytest.fixture()
def fixture_inputs():
    """600 synthetic frozen member rows plus both T3 per-item passes.

    The first half of the items is strongly image-dependent
    (q_real=15/16, q_blind=1/16, dq=+14/16); the second half is
    blind-solvable-or-worse (q_real=1/16, q_blind=4/16, dq=-3/16), so the
    registered law clips it to the 1/16 floor and the draw is ~15:1 skewed --
    skewed enough that weight-ignoring naive draws fail the frequency audit.
    """
    source_rows = []
    real_rows = []
    none_rows = []
    for index in range(ITEM_COUNT):
        pair_index = index // 2
        member = "a" if index % 2 == 0 else "b"
        uid = f"m6_fixture{pair_index:04d}"
        source_rows.append(
            {
                "problem": f"<image>What is value {index}?",
                "answer": str(1000 + index),
                "images": [f"data/fixture/images/{uid}_{member}.png"],
                "pair_group_uid": uid,
                "pair_member": member,
                "template_id": TEMPLATES[index % 3],
                "category": "fixture_category",
            }
        )
        image_dependent = index < ITEM_COUNT // 2
        q_real = 15.0 / 16.0 if image_dependent else 1.0 / 16.0
        q_blind = 1.0 / 16.0 if image_dependent else 4.0 / 16.0
        for condition, rows, p_sample in (
            ("real", real_rows, q_real),
            ("none", none_rows, q_blind),
        ):
            rows.append(
                {
                    "condition": condition,
                    "row_index": index,
                    "qid": f"{uid}:{member}",
                    "sample_count": 16,
                    "p_sample": p_sample,
                }
            )
    records = build_delta_q_records(real_rows, none_rows, source_rows)
    probabilities = np.array([r["draw_probability"] for r in records], dtype=float)
    return source_rows, real_rows, none_rows, records, probabilities


def _registered_build(source_rows, probabilities):
    indices = draw_indices(probabilities, ITEM_COUNT, BUILD_SEED)
    return materialize_rows(source_rows, indices)


def test_registered_resample_passes(fixture_inputs):
    source_rows, _, _, records, probabilities = fixture_inputs
    nec_rows, source_map = _registered_build(source_rows, probabilities)
    result = audit_necessity_resample(source_rows, records, nec_rows, source_map)
    assert result["errors"] == []
    assert result["checks"]["status_pass"]
    assert result["checks"]["empirical_draw_frequency_consistent"]
    assert len(nec_rows) == ITEM_COUNT
    assert all(tuple(row.keys()) == COLUMNS for row in nec_rows)
    # The clipped half sits exactly at the floor; the ratio stays within 17.
    floor_weights = [r["weight"] for r in records if r["delta_q"] < 0]
    assert floor_weights and all(w == FLOOR_WEIGHT for w in floor_weights)


def test_naive_uniform_draw_fails(fixture_inputs):
    """Naive: sample uniformly, ignoring w_i entirely (selection never happens)."""
    source_rows, _, _, records, _ = fixture_inputs
    rng = np.random.default_rng(BUILD_SEED)
    indices = rng.choice(ITEM_COUNT, size=ITEM_COUNT, replace=True)
    nec_rows, source_map = materialize_rows(source_rows, indices)
    result = audit_necessity_resample(source_rows, records, nec_rows, source_map)
    assert not result["checks"]["status_pass"]
    assert not result["checks"]["empirical_draw_frequency_consistent"]
    assert not result["checks"]["draw_reproducible_from_build_seed"]


def test_naive_permutation_without_replacement_fails(fixture_inputs):
    """Naive: keep every item exactly once (a shuffle, not a weighted draw)."""
    source_rows, _, _, records, _ = fixture_inputs
    indices = np.random.default_rng(BUILD_SEED).permutation(ITEM_COUNT)
    nec_rows, source_map = materialize_rows(source_rows, indices)
    result = audit_necessity_resample(source_rows, records, nec_rows, source_map)
    assert not result["checks"]["status_pass"]
    assert not result["checks"]["empirical_draw_frequency_consistent"]


def test_naive_floorless_weights_fail(fixture_inputs):
    """Naive: w = max(dq, 0) without the 1/16 floor -- negative-dq items are
    stranded with zero probability (support collapse)."""
    source_rows, _, _, records, _ = fixture_inputs
    stranded = copy.deepcopy(records)
    total = sum(max(r["delta_q"], 0.0) for r in stranded)
    for record in stranded:
        record["weight"] = max(record["delta_q"], 0.0)
        record["draw_probability"] = record["weight"] / total
    probabilities = np.array([r["draw_probability"] for r in stranded], dtype=float)
    indices = draw_indices(probabilities, ITEM_COUNT, BUILD_SEED)
    nec_rows, source_map = materialize_rows(source_rows, indices)
    result = audit_necessity_resample(source_rows, stranded, nec_rows, source_map)
    assert not result["checks"]["status_pass"]
    assert not result["checks"]["weight_law_exact"]
    assert not result["checks"]["support_complete_and_ratio_bounded"]


def test_naive_reward_scaling_schema_fails(fixture_inputs):
    """Naive: implement necessity as a per-row reward weight column instead of
    draw probabilities (I1 violation: the schema must never carry dq)."""
    source_rows, _, _, records, probabilities = fixture_inputs
    nec_rows, source_map = _registered_build(source_rows, probabilities)
    scaled = copy.deepcopy(nec_rows)
    for row, record in zip(scaled, source_map):
        row["delta_q_weight"] = records[record["source_row_index"]]["weight"]
    result = audit_necessity_resample(source_rows, records, scaled, source_map)
    assert not result["checks"]["status_pass"]
    assert not result["checks"]["seven_column_schema"]


def test_naive_per_slot_uid_fails(fixture_inputs):
    """Naive: give every slot its own uid instead of adjacent a/b pseudo-pairs
    (breaks the member-mode loader/reward pair contract)."""
    source_rows, _, _, records, probabilities = fixture_inputs
    indices = draw_indices(probabilities, ITEM_COUNT, BUILD_SEED)
    nec_rows, source_map = materialize_rows(source_rows, indices)
    broken = copy.deepcopy(nec_rows)
    for slot, row in enumerate(broken):
        row["pair_group_uid"] = f"{SYNTHETIC_UID_PREFIX}{slot:06d}"
    result = audit_necessity_resample(source_rows, records, broken, source_map)
    assert not result["checks"]["status_pass"]
    assert not result["checks"]["adjacent_synthetic_pseudo_pairs"]


def test_naive_original_uid_passthrough_fails(fixture_inputs):
    """Naive: keep the frozen pair_group_uid/pair_member on the drawn rows,
    colliding with real uids (and duplicating them across slots)."""
    source_rows, _, _, records, probabilities = fixture_inputs
    indices = draw_indices(probabilities, ITEM_COUNT, BUILD_SEED)
    nec_rows, source_map = materialize_rows(source_rows, indices)
    passthrough = copy.deepcopy(nec_rows)
    for row, record in zip(passthrough, source_map):
        source = source_rows[record["source_row_index"]]
        row["pair_group_uid"] = source["pair_group_uid"]
        row["pair_member"] = source["pair_member"]
    result = audit_necessity_resample(source_rows, records, passthrough, source_map)
    assert not result["checks"]["status_pass"]
    assert not result["checks"]["synthetic_uids_disjoint_from_real_uids"]


def test_tampered_slot_content_fails(fixture_inputs):
    source_rows, _, _, records, probabilities = fixture_inputs
    nec_rows, source_map = _registered_build(source_rows, probabilities)
    tampered = copy.deepcopy(nec_rows)
    tampered[7]["answer"] = "999999"
    result = audit_necessity_resample(source_rows, records, tampered, source_map)
    assert not result["checks"]["status_pass"]
    assert not result["checks"]["slots_byte_identical_to_source"]


def test_wrong_build_seed_fails(fixture_inputs):
    """A draw from any other seed is not the registered draw, even when its
    frequencies look fine."""
    source_rows, _, _, records, probabilities = fixture_inputs
    indices = draw_indices(probabilities, ITEM_COUNT, seed=0)
    nec_rows, source_map = materialize_rows(source_rows, indices)
    result = audit_necessity_resample(source_rows, records, nec_rows, source_map)
    assert not result["checks"]["status_pass"]
    assert not result["checks"]["draw_reproducible_from_build_seed"]


def test_draw_is_deterministic(fixture_inputs):
    source_rows, _, _, _, probabilities = fixture_inputs
    first, _ = _registered_build(source_rows, probabilities)
    second, _ = _registered_build(source_rows, probabilities)
    assert parquet_bytes(first) == parquet_bytes(second)


def test_weight_law_constants():
    assert compute_weight(0.5) == 0.5 + FLOOR_WEIGHT
    assert compute_weight(0.0) == FLOOR_WEIGHT
    assert compute_weight(-0.25) == FLOOR_WEIGHT
    assert FLOOR_WEIGHT == 1.0 / 16.0


def test_misaligned_qid_refused(fixture_inputs):
    source_rows, real_rows, none_rows, _, _ = fixture_inputs
    broken = copy.deepcopy(real_rows)
    broken[3]["qid"] = "m6_fixture9999:a"
    with pytest.raises(ValueError, match="qid"):
        build_delta_q_records(broken, none_rows, source_rows)


def test_non_sixteenth_p_sample_refused(fixture_inputs):
    source_rows, real_rows, none_rows, _, _ = fixture_inputs
    broken = copy.deepcopy(real_rows)
    broken[5]["p_sample"] = 0.33
    with pytest.raises(ValueError, match="1/16"):
        build_delta_q_records(broken, none_rows, source_rows)
