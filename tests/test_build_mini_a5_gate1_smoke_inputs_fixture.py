"""Adversarial fixtures (I10) for the Gate-1 T7 smoke/step-0 input builder.

Each fixture plants the output a naive slicing implementation would produce
and requires audit_gate1_smoke_inputs to reject it; the registered slices are
the positive control for both arms.
"""
from __future__ import annotations

import copy

import pytest

from scripts.build_mini_a5_gate1_smoke_inputs import (
    SMOKE_PAIRS,
    STEP0_OFFSET_PAIRS,
    STEP0_PAIRS,
    audit_gate1_smoke_inputs,
    build_smoke_subset,
    build_step0_sample,
    pairs_image_index,
)

PAIR_COUNT = STEP0_OFFSET_PAIRS + STEP0_PAIRS + 4  # corpus larger than both slices


def _make_arm(arm: str):
    """A miniature Gate-1 corpus for one arm plus frozen pair records."""
    pairs_rows = []
    corpus_rows = []
    source_map = []
    for pair_index in range(PAIR_COUNT):
        uid = f"m6_fx{pair_index:06d}"
        pairs_rows.append(
            {
                "pair_group_uid": uid,
                "image_a_path": f"data/fx/images/{uid}_a.png",
                "image_a_sha256": f"sha_a_{pair_index:06d}",
                "image_b_path": f"data/fx/images/{uid}_b.png",
                "image_b_sha256": f"sha_b_{pair_index:06d}",
            }
        )
        for slot_member in ("a", "b"):
            slot = 2 * pair_index + (0 if slot_member == "a" else 1)
            if arm == "std":
                synthetic_uid = f"std1_{uid}"
                source_member = "a"
                source_pair = pair_index
            else:
                synthetic_uid = f"nec1_{pair_index:06d}"
                # A necessity-style draw: members of one pseudo-pair come from
                # different frozen rows (and possibly different members).
                source_pair = (pair_index * 7 + (3 if slot_member == "b" else 0)) % PAIR_COUNT
                source_member = "a" if (slot % 3) else "b"
            source_uid = f"m6_fx{source_pair:06d}"
            corpus_rows.append(
                {
                    "problem": f"<image>Question {source_pair} {source_member}?",
                    "answer": f"{source_pair}{source_member}",
                    "images": [f"data/fx/images/{source_uid}_{source_member}.png"],
                    "pair_group_uid": synthetic_uid,
                    "pair_member": slot_member,
                    "template_id": f"fx_template_{source_pair % 3}",
                    "category": "fx_category",
                }
            )
            source_map.append(
                {
                    "slot": slot,
                    "pair_group_uid": synthetic_uid,
                    "pair_member": slot_member,
                    "source_row_index": 2 * source_pair
                    + (0 if source_member == "a" else 1),
                    "source_qid": f"{source_uid}:{source_member}",
                }
            )
    image_index = pairs_image_index(pairs_rows)
    if arm == "std":
        source_map = []
    return corpus_rows, source_map, image_index


@pytest.fixture(params=["std", "necessity"])
def arm_fixture(request):
    arm = request.param
    corpus_rows, source_map, image_index = _make_arm(arm)
    smoke_rows = build_smoke_subset(corpus_rows)
    step0_sample = build_step0_sample(arm, corpus_rows, source_map, image_index)
    return arm, corpus_rows, source_map, image_index, smoke_rows, step0_sample


def _audit(arm_fixture, smoke_rows, step0_sample):
    arm, corpus_rows, source_map, image_index, _, _ = arm_fixture
    return audit_gate1_smoke_inputs(
        arm, corpus_rows, smoke_rows, step0_sample, source_map, image_index
    )


def test_registered_slices_pass(arm_fixture):
    _, _, _, _, smoke_rows, step0_sample = arm_fixture
    result = _audit(arm_fixture, smoke_rows, step0_sample)
    assert result["errors"] == []
    assert result["checks"]["status_pass"]
    assert len(smoke_rows) == 2 * SMOKE_PAIRS
    assert len(step0_sample) == STEP0_PAIRS


def test_naive_overlapping_step0_slice_fails(arm_fixture):
    """Naive: start the step-0 sample at pseudo-pair 0, overlapping the smoke
    subset instead of staying disjoint."""
    _, _, _, _, smoke_rows, step0_sample = arm_fixture
    overlapping = copy.deepcopy(step0_sample)
    overlapping[0]["pair_group_uid"] = smoke_rows[0]["pair_group_uid"]
    result = _audit(arm_fixture, smoke_rows, overlapping)
    assert not result["checks"]["status_pass"]
    assert not result["checks"]["step0_pairs_identical_to_registered_slice"]


def test_naive_offset_smoke_slice_fails(arm_fixture):
    """Naive: a one-row-shifted smoke slice (breaks identity and adjacency)."""
    _, corpus_rows, _, _, _, step0_sample = arm_fixture
    shifted = [dict(row) for row in corpus_rows[1 : 2 * SMOKE_PAIRS + 1]]
    result = _audit(arm_fixture, shifted, step0_sample)
    assert not result["checks"]["status_pass"]
    assert not result["checks"]["smoke_rows_identical_to_corpus_prefix"]


def test_tampered_smoke_row_fails(arm_fixture):
    _, _, _, _, smoke_rows, step0_sample = arm_fixture
    tampered = copy.deepcopy(smoke_rows)
    tampered[5]["answer"] = "tampered"
    result = _audit(arm_fixture, tampered, step0_sample)
    assert not result["checks"]["status_pass"]
    assert not result["checks"]["smoke_rows_identical_to_corpus_prefix"]


def test_wrong_member_image_record_fails(arm_fixture):
    """Naive: resolve the step-0 image sha against the wrong frozen member
    (e.g. member b for a std pseudo-pair that kept only member a)."""
    _, _, _, _, smoke_rows, step0_sample = arm_fixture
    swapped = copy.deepcopy(step0_sample)
    record = swapped[0]
    record["image_b_sha256"] = record["image_b_sha256"] + "_wrong"
    result = _audit(arm_fixture, smoke_rows, swapped)
    assert not result["checks"]["status_pass"]
    assert not result["checks"]["step0_pairs_identical_to_registered_slice"]


def test_truncated_step0_sample_fails(arm_fixture):
    _, _, _, _, smoke_rows, step0_sample = arm_fixture
    result = _audit(arm_fixture, smoke_rows, step0_sample[:-1])
    assert not result["checks"]["status_pass"]
    assert not result["checks"]["step0_pair_count_exact"]


def test_std_member_b_source_refused():
    """The std arm maps every row to the kept member-a rendering; a builder
    that maps pseudo-member b to the counterfactual partner must be refused."""
    corpus_rows, source_map, image_index = _make_arm("std")
    broken = copy.deepcopy(corpus_rows)
    row = broken[2 * STEP0_OFFSET_PAIRS + 1]
    row["images"] = [row["images"][0].replace("_a.png", "_b.png")]
    with pytest.raises(ValueError, match="image path"):
        build_step0_sample("std", broken, source_map, image_index)
