"""Fixture for P0.4 / I13 — no aggregate may cross R19 scientific roles."""
import pytest

from src.eval.task_roles import (
    CATEGORY_ROLES,
    MEASURED_BASE_PAIR_ACCURACY,
    ORACLE_LOCALIZED,
    PRIMARY_ANCHOR,
    SATURATED_CONTROL,
    SATURATION_CLAIM_IS_ACCURATE,
    TEMPLATE_ROLES,
    assert_no_cross_role_aggregate,
    crosses_roles,
    role_for_category,
    role_for_template,
    roles_of,
)

ANCHOR = "coordinate_register_twenty_point_x_v02"
HEADER = "header_cued_table_code_v02"
NINE = "starred_series_value_nine_v07"


def test_every_r19_task_has_exactly_one_role():
    assert set(TEMPLATE_ROLES.values()) == {PRIMARY_ANCHOR, SATURATED_CONTROL, ORACLE_LOCALIZED}
    assert set(CATEGORY_ROLES.values()) == set(TEMPLATE_ROLES.values())
    assert len(TEMPLATE_ROLES) == len(CATEGORY_ROLES) == 3


def test_template_and_category_namings_agree():
    assert role_for_template(ANCHOR) == role_for_category("geometry_coordinate_indexing")
    assert role_for_template(HEADER) == role_for_category("document_header_indexing")
    assert role_for_template(NINE) == role_for_category("chart_two_hop_read")


def test_the_overall_r19_aggregate_is_rejected():
    """THE guard: an all-tasks average is what I13 forbids."""
    with pytest.raises(ValueError, match="I13 violation"):
        assert_no_cross_role_aggregate([ANCHOR, HEADER, NINE], what="overall R19 pair accuracy")


def test_anchor_plus_oracle_is_rejected():
    """Even the two same-looking chart/geometry tasks answer different questions."""
    assert crosses_roles([ANCHOR, NINE])
    with pytest.raises(ValueError, match="I13 violation"):
        assert_no_cross_role_aggregate([ANCHOR, NINE])


def test_within_role_aggregate_is_allowed():
    assert_no_cross_role_aggregate([ANCHOR])
    assert_no_cross_role_aggregate([NINE])
    assert not crosses_roles([HEADER])


def test_unknown_task_fails_closed():
    """A new task must be given a role before it can be reported on."""
    with pytest.raises(KeyError):
        role_for_template("some_new_template_v01")
    with pytest.raises(KeyError):
        roles_of([ANCHOR, "some_new_template_v01"])


def test_error_names_the_roles_it_crossed():
    with pytest.raises(ValueError) as e:
        assert_no_cross_role_aggregate([ANCHOR, HEADER, NINE])
    msg = str(e.value)
    assert "primary visual anchor" in msg
    assert "oracle-localized readout control" in msg


def test_saturation_claim_is_recorded_as_inaccurate():
    """The header task is not at ceiling; the label is inherited, not measured.

    Base pair accuracy is 0.8667, and the task moves in every trained arm. This
    guards against the prose claim ("saturated at 1.000 for every model") being
    re-adopted as fact.
    """
    assert SATURATION_CLAIM_IS_ACCURATE is False
    assert MEASURED_BASE_PAIR_ACCURACY[SATURATED_CONTROL] < 0.95
    assert abs(MEASURED_BASE_PAIR_ACCURACY[SATURATED_CONTROL] - 0.8667) < 1e-4
