"""Canonical R19 task roles (P0.4, invariant I13).

The three R19 tasks hold different scientific roles. An average across them is
uninterpretable -- it mixes a control whose localization is supplied by the cue,
a high-baseline verification task, and the one task that actually requires search
and binding. I13 forbids any aggregate that crosses roles.

This module is the single source of truth for which template belongs to which
role, and supplies a guard that reporting code can call so new cross-role
aggregates cannot be introduced silently.

Measured base rates (R19, frozen 3B base, pair accuracy) are recorded alongside
each role because one of them contradicts a claim still present in the prose --
see NOTE on SATURATED_CONTROL below.
"""
from __future__ import annotations

from typing import Iterable

PRIMARY_ANCHOR = "primary_visual_anchor"
SATURATED_CONTROL = "saturated_positive_control_retention_canary"
ORACLE_LOCALIZED = "oracle_localized_readout_control"

ROLE_LABELS = {
    PRIMARY_ANCHOR: "primary visual anchor",
    SATURATED_CONTROL: "saturated positive control / retention canary",
    ORACLE_LOCALIZED: "oracle-localized readout control",
}

# template_id -> role
TEMPLATE_ROLES = {
    "coordinate_register_twenty_point_x_v02": PRIMARY_ANCHOR,
    "header_cued_table_code_v02": SATURATED_CONTROL,
    "starred_series_value_nine_v07": ORACLE_LOCALIZED,
}

# category_id -> role (same partition, category naming)
CATEGORY_ROLES = {
    "geometry_coordinate_indexing": PRIMARY_ANCHOR,
    "document_header_indexing": SATURATED_CONTROL,
    "chart_two_hop_read": ORACLE_LOCALIZED,
}

# Measured on R19 with the frozen base; see reports/f2d_template_decomposition_v1.md
MEASURED_BASE_PAIR_ACCURACY = {
    PRIMARY_ANCHOR: 0.4717,
    SATURATED_CONTROL: 0.8667,
    ORACLE_LOCALIZED: 0.4367,
}

# NOTE (2026-07-27). The role name `saturated_positive_control` is inherited from
# the prose, which describes this task as "saturated at 1.000 for every model
# including base" and unable to show improvement. That is not what R19 measures:
# base pair accuracy is 0.8667 (strict 0.1800) and the task moves +0.019 to +0.023
# in every trained arm, contributing 18.7% of A1's overall movement. The retention
# canary function is intact -- nothing drops -- but "saturated" is inaccurate. The
# name is kept here because the documents specify it; the discrepancy is recorded
# so reporting code and readers are not misled by the label.
SATURATION_CLAIM_IS_ACCURATE = False


def role_for_template(template_id: str) -> str:
    try:
        return TEMPLATE_ROLES[template_id]
    except KeyError:
        raise KeyError(
            f"unknown R19 template_id {template_id!r}; add it to TEMPLATE_ROLES with "
            "an explicit role before reporting on it"
        ) from None


def role_for_category(category_id: str) -> str:
    try:
        return CATEGORY_ROLES[category_id]
    except KeyError:
        raise KeyError(
            f"unknown R19 category {category_id!r}; add it to CATEGORY_ROLES with "
            "an explicit role before reporting on it"
        ) from None


def roles_of(ids: Iterable[str]) -> set[str]:
    """Roles covered by a set of template ids or category ids (either naming)."""
    out = set()
    for i in ids:
        if i in TEMPLATE_ROLES:
            out.add(TEMPLATE_ROLES[i])
        elif i in CATEGORY_ROLES:
            out.add(CATEGORY_ROLES[i])
        else:
            raise KeyError(f"unknown R19 task id {i!r}")
    return out


def crosses_roles(ids: Iterable[str]) -> bool:
    return len(roles_of(ids)) > 1


def assert_no_cross_role_aggregate(ids: Iterable[str], what: str = "aggregate") -> None:
    """Raise if `ids` spans more than one scientific role (I13).

    Call this wherever a metric is computed over a set of R19 tasks. An overall
    R19 number may still be produced for accounting purposes, but it must be
    labelled an accounting identity rather than a capability score, and it must
    not be routed through this guard.
    """
    ids = list(ids)
    roles = roles_of(ids)
    if len(roles) > 1:
        pretty = ", ".join(sorted(ROLE_LABELS[r] for r in roles))
        raise ValueError(
            f"I13 violation: {what} spans {len(roles)} scientific roles ({pretty}) "
            f"over tasks {sorted(ids)}. These tasks answer different questions and "
            "must be reported separately."
        )
