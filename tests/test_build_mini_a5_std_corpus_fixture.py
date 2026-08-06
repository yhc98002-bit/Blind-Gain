"""Adversarial fixtures (I10) for the Mini-A5 arm-1 std-corpus projection.

Each fixture plants the output a naive implementation of section 2 R1 of
docs/registered_mini_a5_gate1_completion_v1.md would produce, and requires
audit_std_projection to reject it. The correct projection is the positive
control and must pass.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from scripts.build_mini_a5_std_corpus import (
    COLUMNS,
    SYNTHETIC_UID_PREFIX,
    audit_std_projection,
    parquet_bytes,
    project_std_rows,
)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


@pytest.fixture()
def fixture_corpus(tmp_path: Path):
    """A miniature frozen paired corpus: 3 pairs with distinct image bytes."""
    corpus = tmp_path / "data" / "mini_fixture_v1"
    (corpus / "images").mkdir(parents=True)
    source_rows = []
    pairs_rows = []
    for index in range(3):
        uid = f"m6_fixture{index:04d}"
        images = {}
        for member in ("a", "b"):
            payload = f"png-bytes-{uid}-{member}".encode()
            path = corpus / "images" / f"{uid}_{member}.png"
            path.write_bytes(payload)
            images[member] = (
                str(path.relative_to(tmp_path)),
                _sha256_bytes(payload),
            )
        for member in ("a", "b"):
            source_rows.append(
                {
                    "problem": f"<image>What is value {index}?",
                    "answer": str(10 + index) if member == "a" else str(90 + index),
                    "images": [images[member][0]],
                    "pair_group_uid": uid,
                    "pair_member": member,
                    "template_id": "fixture_template_v1",
                    "category": "fixture_category",
                }
            )
        pairs_rows.append(
            {
                "pair_group_uid": uid,
                "image_a_path": images["a"][0],
                "image_a_sha256": images["a"][1],
                "image_b_path": images["b"][0],
                "image_b_sha256": images["b"][1],
            }
        )
    return tmp_path, source_rows, pairs_rows


def _audit(fixture, std_rows, **kwargs):
    root, source_rows, pairs_rows = fixture
    return audit_std_projection(source_rows, std_rows, pairs_rows, root, **kwargs)


def test_registered_projection_passes(fixture_corpus):
    _, source_rows, _ = fixture_corpus
    std_rows = project_std_rows(source_rows)
    result = _audit(fixture_corpus, std_rows)
    assert result["errors"] == []
    assert result["checks"]["status_pass"]
    assert len(std_rows) == len(source_rows)
    assert all(tuple(row.keys()) == COLUMNS for row in std_rows)


def test_naive_pair_passthrough_fails(fixture_corpus):
    """Naive: keep the paired corpus and just rename the uids. The second
    pseudo-member is then the counterfactual partner, not the same scene."""
    _, source_rows, _ = fixture_corpus
    std_rows = copy.deepcopy(source_rows)
    for row in std_rows:
        row["pair_group_uid"] = f"{SYNTHETIC_UID_PREFIX}{row['pair_group_uid']}"
    result = _audit(fixture_corpus, std_rows)
    assert not result["checks"]["status_pass"]
    assert not result["checks"]["row_for_row_identity_with_member_a"]


def test_naive_original_uid_kept_fails(fixture_corpus):
    """Naive: duplicate member a but keep the original pair_group_uid,
    colliding with real uids."""
    _, source_rows, _ = fixture_corpus
    std_rows = []
    for index in range(0, len(source_rows), 2):
        for member in ("a", "b"):
            row = copy.deepcopy(source_rows[index])
            row["pair_member"] = member
            std_rows.append(row)
    result = _audit(fixture_corpus, std_rows)
    assert not result["checks"]["status_pass"]
    assert not result["checks"]["synthetic_uids_disjoint_from_real_uids"]


def test_naive_block_layout_fails(fixture_corpus):
    """Naive: first all 'a' copies, then all 'b' copies (no adjacency)."""
    _, source_rows, _ = fixture_corpus
    projected = project_std_rows(source_rows)
    std_rows = [row for row in projected if row["pair_member"] == "a"] + [
        row for row in projected if row["pair_member"] == "b"
    ]
    result = _audit(fixture_corpus, std_rows)
    assert not result["checks"]["status_pass"]
    assert not result["checks"]["adjacent_pseudo_pairs"]


def test_naive_member_b_image_swap_fails(fixture_corpus):
    """Naive: relabel the members but leave the second slot pointing at the
    member-b rendering (duplicates metadata, not the scene)."""
    _, source_rows, _ = fixture_corpus
    std_rows = project_std_rows(source_rows)
    for index in range(1, len(std_rows), 2):
        b_source = source_rows[index]
        std_rows[index]["images"] = [str(path) for path in b_source["images"]]
    result = _audit(fixture_corpus, std_rows)
    assert not result["checks"]["status_pass"]
    assert not result["checks"]["no_member_b_rendering_referenced"]


def test_schema_drift_fails(fixture_corpus):
    _, source_rows, _ = fixture_corpus
    extra = project_std_rows(source_rows)
    for row in extra:
        row["delta_q"] = 0.0
    result_extra = _audit(fixture_corpus, extra)
    assert not result_extra["checks"]["seven_column_schema"]

    missing = project_std_rows(source_rows)
    for row in missing:
        del row["category"]
    result_missing = _audit(fixture_corpus, missing)
    assert not result_missing["checks"]["seven_column_schema"]


def test_tampered_image_bytes_fail(fixture_corpus):
    root, source_rows, _ = fixture_corpus
    std_rows = project_std_rows(source_rows)
    target = root / std_rows[0]["images"][0]
    target.write_bytes(b"tampered")
    result = _audit(fixture_corpus, std_rows)
    assert not result["checks"]["image_sha256_matches_pairs_record"]
    assert not result["checks"]["status_pass"]


def test_projection_is_deterministic(fixture_corpus):
    _, source_rows, _ = fixture_corpus
    assert parquet_bytes(project_std_rows(source_rows)) == parquet_bytes(
        project_std_rows(copy.deepcopy(source_rows))
    )


def test_non_adjacent_source_refused(fixture_corpus):
    _, source_rows, _ = fixture_corpus
    shuffled = source_rows[1:] + source_rows[:1]
    with pytest.raises(ValueError):
        project_std_rows(shuffled)
