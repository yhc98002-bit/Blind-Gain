"""Loader validation fixtures for the v2 intervention-group schema (I15).

Registered in docs/registered_track4_premise_v2_design_v1.md. Two properties
are load-bearing and proven here rather than assumed:

  * cross-version refusal in BOTH directions — the v1 loader refuses v2
    groups and the v2 loader refuses v1 groups; neither ever silently
    accepts the other's version;
  * the premise structural rules fail closed — a lying premise_transition
    flag, a premise-moving invariance twin, a half-specified premise group,
    and a stray premise label on a negative control are each rejected.
"""
import copy

import pytest

from src.train.intervention_group_schema import (
    SCHEMA_VERSION,
    SCHEMA_VERSION_V2,
    InterventionGroupSchemaError,
    validate_batch_v2,
    validate_group,
    validate_group_v2,
)


def good_group_v1():
    """The P0.3 fixture group, unchanged: what the frozen v1 loader accepts."""
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


def good_group_v2():
    """A premise_transition group as built by the Track-4 v2 generator."""
    return {
        "schema_version": SCHEMA_VERSION_V2,
        "group_uid": "t4v2-grp-0001",
        "scene_program_id": "t4v2_ab12cd34ef56aa00",
        "intervention_type": "premise_transition",
        "question": "Consider the point nearest to point K4. "
                    "What is the x-coordinate of that nearest point?",
        "premise": {"question": "Which labeled point is nearest to point K4?"},
        "original": {"image_path": "a.png", "image_sha256": "aa", "answer": "3",
                     "premise_answer": "M3"},
        "members": [
            {"member_uid": "m1", "kind": "causal", "answer": "-5",
             "image_path": "b.png", "image_sha256": "bb",
             "premise_answer": "W7", "premise_transition": True},
            {"member_uid": "m2", "kind": "invariance", "answer": "3",
             "image_path": "c.png", "image_sha256": "cc",
             "premise_answer": "M3"},
            {"member_uid": "m3", "kind": "negative_control", "answer": "3",
             "condition": "no_image"},
            {"member_uid": "m4", "kind": "negative_control", "answer": "3",
             "condition": "mismatched_real",
             "image_path": "z.png", "image_sha256": "zz"},
        ],
        "difficulty": {"n_points": 20, "margin_a": 1.0, "margin_b": 1.0, "margin_d3": 1.0},
        "blind_solvability": {"q_real": None, "q_blind": None,
                              "measurement_state": "pending"},
    }


# ---------------------------------------------------------------- cross-version

def test_v1_loader_refuses_v2_group():
    with pytest.raises(InterventionGroupSchemaError, match="refuses groups of an unknown version"):
        validate_group(good_group_v2())


def test_v2_loader_refuses_v1_group():
    with pytest.raises(InterventionGroupSchemaError, match="refuses groups of any other version"):
        validate_group_v2(good_group_v1())


def test_v1_loader_still_accepts_v1():
    assert validate_group(good_group_v1())["group_uid"] == "grp-0001"


def test_v2_loader_accepts_v2():
    assert validate_group_v2(good_group_v2())["group_uid"] == "t4v2-grp-0001"


# ----------------------------------------------------------------- premise rules

def test_lying_premise_transition_flag_true_is_rejected():
    """Flag says transition but the premise golds are equal — an invariance-style
    item would be scored as a transition."""
    g = good_group_v2()
    g["members"][0]["premise_answer"] = "M3"  # equals original's
    with pytest.raises(InterventionGroupSchemaError, match="premise_transition flag"):
        validate_group_v2(g)


def test_lying_premise_transition_flag_false_is_rejected():
    g = good_group_v2()
    g["members"][0]["premise_transition"] = False  # golds actually differ
    with pytest.raises(InterventionGroupSchemaError, match="premise_transition flag"):
        validate_group_v2(g)


def test_missing_premise_transition_flag_is_rejected():
    g = good_group_v2()
    del g["members"][0]["premise_transition"]
    with pytest.raises(InterventionGroupSchemaError, match="boolean premise_transition"):
        validate_group_v2(g)


def test_invariance_member_moving_the_premise_is_rejected():
    g = good_group_v2()
    g["members"][1]["premise_answer"] = "W7"
    with pytest.raises(InterventionGroupSchemaError, match="invariance but its premise_answer"):
        validate_group_v2(g)


def test_member_missing_premise_answer_in_premise_group_is_rejected():
    g = good_group_v2()
    del g["members"][1]["premise_answer"]
    with pytest.raises(InterventionGroupSchemaError, match="non-empty premise_answer"):
        validate_group_v2(g)


def test_original_missing_premise_answer_in_premise_group_is_rejected():
    g = good_group_v2()
    del g["original"]["premise_answer"]
    with pytest.raises(InterventionGroupSchemaError, match="original must carry"):
        validate_group_v2(g)


def test_premise_answer_without_declared_premise_is_rejected():
    """Half-specified premise metadata fails closed in the other direction too."""
    g = good_group_v2()
    g["intervention_type"] = "fact_read"
    del g["premise"]
    del g["original"]["premise_answer"]
    del g["members"][1]["premise_answer"]
    # causal member still carries premise fields -> refuse
    with pytest.raises(InterventionGroupSchemaError, match="no premise"):
        validate_group_v2(g)


def test_negative_control_with_premise_answer_is_rejected():
    g = good_group_v2()
    g["members"][2]["premise_answer"] = "M3"
    with pytest.raises(InterventionGroupSchemaError, match="negative_control must not carry premise_answer"):
        validate_group_v2(g)


def test_non_premise_group_passes():
    g = good_group_v2()
    g["intervention_type"] = "fact_read"
    del g["premise"]
    del g["original"]["premise_answer"]
    del g["members"][0]["premise_answer"]
    del g["members"][0]["premise_transition"]
    del g["members"][1]["premise_answer"]
    assert validate_group_v2(g)["intervention_type"] == "fact_read"


# ------------------------------------------------------ v1 rules survive in v2

def test_v2_causal_member_sharing_the_original_answer_is_rejected():
    g = good_group_v2()
    g["members"][0]["answer"] = "3"
    with pytest.raises(InterventionGroupSchemaError, match="causal but its answer equals"):
        validate_group_v2(g)


def test_v2_group_without_invariance_member_is_rejected():
    g = good_group_v2()
    g["members"] = [m for m in g["members"] if m["kind"] != "invariance"]
    with pytest.raises(InterventionGroupSchemaError, match="no invariance member"):
        validate_group_v2(g)


def test_v2_missing_intervention_type_is_rejected():
    g = good_group_v2()
    del g["intervention_type"]
    with pytest.raises(InterventionGroupSchemaError, match="missing required fields"):
        validate_group_v2(g)


def test_v2_no_image_control_with_image_path_is_rejected():
    g = good_group_v2()
    g["members"][2]["image_path"] = "sneaky.png"
    with pytest.raises(InterventionGroupSchemaError, match="no_image control must not carry"):
        validate_group_v2(g)


def test_v2_mismatched_real_without_image_is_rejected():
    g = good_group_v2()
    del g["members"][3]["image_path"]
    with pytest.raises(InterventionGroupSchemaError, match="mismatched_real control needs"):
        validate_group_v2(g)


# ------------------------------------------------- measurement-state semantics

def test_pending_with_numeric_q_is_rejected():
    g = good_group_v2()
    g["blind_solvability"]["q_real"] = 0.5
    with pytest.raises(InterventionGroupSchemaError, match="pending blind_solvability.q_real must be null"):
        validate_group_v2(g)


def test_measured_with_null_q_is_rejected():
    g = good_group_v2()
    g["blind_solvability"]["measurement_state"] = "measured"
    with pytest.raises(InterventionGroupSchemaError, match="must be a probability"):
        validate_group_v2(g)


def test_measured_with_consistent_q_passes():
    g = good_group_v2()
    g["blind_solvability"] = {"q_real": 0.6, "q_blind": 0.1, "delta_q": 0.5,
                              "measurement_state": "measured"}
    assert validate_group_v2(g, require_measured=True)


def test_measured_with_stale_delta_q_is_rejected():
    g = good_group_v2()
    g["blind_solvability"] = {"q_real": 0.6, "q_blind": 0.1, "delta_q": 0.9,
                              "measurement_state": "measured"}
    with pytest.raises(InterventionGroupSchemaError, match="delta_q disagrees"):
        validate_group_v2(g)


def test_training_loader_refuses_pending_groups():
    """The rule that keeps unmeasured dev groups out of any optimizer step."""
    g = good_group_v2()
    with pytest.raises(InterventionGroupSchemaError, match="training loader refuses"):
        validate_group_v2(g, require_measured=True)


def test_missing_measurement_state_is_rejected():
    g = good_group_v2()
    del g["blind_solvability"]["measurement_state"]
    with pytest.raises(InterventionGroupSchemaError, match="measurement_state"):
        validate_group_v2(g)


# --------------------------------------------------------------------- batches

def test_batch_rejects_duplicate_group_uids():
    a, b = good_group_v2(), copy.deepcopy(good_group_v2())
    with pytest.raises(InterventionGroupSchemaError, match="duplicate group_uid"):
        validate_batch_v2([a, b])


def test_batch_of_distinct_groups_passes():
    a, b = good_group_v2(), copy.deepcopy(good_group_v2())
    b["group_uid"] = "t4v2-grp-0002"
    assert len(validate_batch_v2([a, b])) == 2


def test_batch_require_measured_passthrough():
    a = good_group_v2()
    with pytest.raises(InterventionGroupSchemaError, match="training loader refuses"):
        validate_batch_v2([a], require_measured=True)
