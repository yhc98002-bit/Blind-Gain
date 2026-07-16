from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.prepare_mini_a5_fixed_subsets import (
    PLUMBING_VAL_PER_TEMPLATE,
    STEP0_PER_TEMPLATE,
    build_fixed_subsets,
)


def _fixtures() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    pairs: list[dict[str, str]] = []
    training: list[dict[str, str]] = []
    count = STEP0_PER_TEMPLATE + PLUMBING_VAL_PER_TEMPLATE
    for template in ("t1", "t2", "t3"):
        for index in range(count):
            uid = f"{template}-{index:03d}"
            pairs.append({"pair_group_uid": uid, "template_id": template})
            training.extend(
                [
                    {"pair_group_uid": uid, "pair_member": "a"},
                    {"pair_group_uid": uid, "pair_member": "b"},
                ]
            )
    return pairs, training


def test_fixed_subsets_are_balanced_disjoint_and_pair_complete() -> None:
    pairs, training = _fixtures()
    payload = build_fixed_subsets(pairs, training)
    assert len(payload["step0_pairs"]) == 3 * STEP0_PER_TEMPLATE
    assert len(payload["plumbing_val_rows"]) == 3 * PLUMBING_VAL_PER_TEMPLATE * 2
    assert not set(payload["step0_pair_ids"]) & set(payload["plumbing_val_pair_ids"])
    for index in range(0, len(payload["plumbing_val_rows"]), 2):
        rows = payload["plumbing_val_rows"][index : index + 2]
        assert rows[0]["pair_group_uid"] == rows[1]["pair_group_uid"]
        assert [row["pair_member"] for row in rows] == ["a", "b"]


def test_fixed_subset_rejects_single_member_validation_pair() -> None:
    pairs, training = _fixtures()
    broken = deepcopy(training)
    broken.pop()
    with pytest.raises(ValueError, match="validation pairs are malformed"):
        build_fixed_subsets(pairs, broken)
