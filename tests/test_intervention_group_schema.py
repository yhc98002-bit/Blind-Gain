"""Loader validation fixture for the intervention-group schema (P0.3 / I15)."""
import copy

import pytest

from src.train.intervention_group_schema import (
    SCHEMA_VERSION,
    InterventionGroupSchemaError,
    validate_batch,
    validate_group,
)


def good_group():
    return {
        "schema_version": SCHEMA_VERSION,
        "group_uid": "grp-0001",
        "scene_program_id": "prog-nine-series-0042",
        "question": "What is the x-coordinate of the point nearest to X2?",
        "original": {"image_path": "a.png", "image_sha256": "aa", "answer": "3"},
        "members": [
            {"member_uid": "m1", "kind": "causal", "answer": "-1",
             "image_path": "b.png", "image_sha256": "bb"},
            {"member_uid": "m2", "kind": "invariance", "answer": "3",
             "image_path": "c.png", "image_sha256": "cc"},
            {"member_uid": "m3", "kind": "negative_control", "answer": "3",
             "condition": "no_image"},
        ],
        "difficulty": {"n_labels": 20, "min_separation": 0.4},
        "blind_solvability": {"q_real": 0.62, "q_blind": 0.14, "delta_q": 0.48},
    }


def test_valid_group_passes():
    assert validate_group(good_group())["group_uid"] == "grp-0001"


def test_causal_member_sharing_the_original_answer_is_rejected():
    """The defect that would silently reduce R_causal to answer reward."""
    g = good_group()
    g["members"][0]["answer"] = "3"
    with pytest.raises(InterventionGroupSchemaError, match="causal but its answer equals"):
        validate_group(g)


def test_invariance_member_changing_the_answer_is_rejected():
    g = good_group()
    g["members"][1]["answer"] = "-1"
    with pytest.raises(InterventionGroupSchemaError, match="invariance but its answer"):
        validate_group(g)


def test_group_without_invariance_member_is_rejected():
    """I5 — causal-only reward is satisfiable by a change detector."""
    g = good_group()
    g["members"] = [m for m in g["members"] if m["kind"] != "invariance"]
    with pytest.raises(InterventionGroupSchemaError, match="no invariance member"):
        validate_group(g)


def test_group_without_causal_member_is_rejected():
    g = good_group()
    g["members"] = [m for m in g["members"] if m["kind"] != "causal"]
    with pytest.raises(InterventionGroupSchemaError, match="no causal member"):
        validate_group(g)


def test_unknown_schema_version_fails_closed():
    g = good_group()
    g["schema_version"] = "blind-gains.intervention-group.v2"
    with pytest.raises(InterventionGroupSchemaError, match="refuses groups of an unknown version"):
        validate_group(g)


def test_missing_required_field_is_rejected():
    for field in ("group_uid", "scene_program_id", "members", "blind_solvability", "difficulty"):
        g = good_group()
        del g[field]
        with pytest.raises(InterventionGroupSchemaError, match="missing required fields"):
            validate_group(g)


def test_duplicate_member_uid_is_rejected():
    g = good_group()
    g["members"][1]["member_uid"] = "m1"
    with pytest.raises(InterventionGroupSchemaError, match="duplicate member_uid"):
        validate_group(g)


def test_bad_negative_control_condition_is_rejected():
    g = good_group()
    g["members"][2]["condition"] = "slightly_blurred"
    with pytest.raises(InterventionGroupSchemaError, match="negative_control condition"):
        validate_group(g)


def test_inconsistent_delta_q_is_rejected():
    """C1 samples on delta_q; a stale stored copy would silently reweight training."""
    g = good_group()
    g["blind_solvability"]["delta_q"] = 0.9
    with pytest.raises(InterventionGroupSchemaError, match="delta_q disagrees"):
        validate_group(g)


def test_out_of_range_q_is_rejected():
    g = good_group()
    g["blind_solvability"]["q_blind"] = 1.4
    with pytest.raises(InterventionGroupSchemaError, match="must be a probability"):
        validate_group(g)


def test_batch_rejects_duplicate_group_uids():
    a, b = good_group(), copy.deepcopy(good_group())
    with pytest.raises(InterventionGroupSchemaError, match="duplicate group_uid"):
        validate_batch([a, b])


def test_batch_of_distinct_groups_passes():
    a, b = good_group(), copy.deepcopy(good_group())
    b["group_uid"] = "grp-0002"
    assert len(validate_batch([a, b])) == 2
