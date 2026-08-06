"""Adversarial fixtures (I10) for the Mini-A5 blind-solvability manifest
converter (prework ledger T2).

Each fixture plants an output a naive train.jsonl -> geometry-manifest
converter would produce and requires audit_manifest to reject it.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path

import pytest

from scripts.build_mini_a5_blind_solvability_manifest import (
    audit_manifest,
    convert_rows,
)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


@pytest.fixture()
def fixture_corpus(tmp_path: Path):
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
            images[member] = (str(path.relative_to(tmp_path)), _sha256_bytes(payload))
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


def _audit(fixture, manifest_rows):
    root, source_rows, pairs_rows = fixture
    return audit_manifest(source_rows, manifest_rows, pairs_rows, root)


def test_correct_conversion_passes(fixture_corpus):
    root, source_rows, _ = fixture_corpus
    manifest_rows = convert_rows(source_rows, root)
    result = _audit(fixture_corpus, manifest_rows)
    assert result["errors"] == []
    assert result["checks"]["status_pass"]
    for row in manifest_rows:
        assert set(row) == {
            "schema_version", "split", "row_index", "qid",
            "problem", "answer", "images", "metadata",
        }
        assert all(set(image) == {"path", "sha256"} for image in row["images"])


def test_naive_sha_of_path_string_fails(fixture_corpus):
    """Naive: hash the path string instead of the file bytes."""
    root, source_rows, _ = fixture_corpus
    manifest_rows = convert_rows(source_rows, root)
    for row in manifest_rows:
        for image in row["images"]:
            image["sha256"] = _sha256_bytes(image["path"].encode())
    result = _audit(fixture_corpus, manifest_rows)
    assert not result["checks"]["image_sha256_matches_file_and_pairs_record"]
    assert not result["checks"]["status_pass"]


def test_naive_member_a_sha_reused_for_b_fails(fixture_corpus):
    """Naive: reuse member a's sha256 for member b's row (per-pair caching bug)."""
    root, source_rows, _ = fixture_corpus
    manifest_rows = convert_rows(source_rows, root)
    for index in range(1, len(manifest_rows), 2):
        manifest_rows[index]["images"][0]["sha256"] = manifest_rows[index - 1]["images"][0][
            "sha256"
        ]
    result = _audit(fixture_corpus, manifest_rows)
    assert not result["checks"]["image_sha256_matches_file_and_pairs_record"]


def test_reordered_rows_fail(fixture_corpus):
    """Naive: rows re-sorted (e.g. by qid) so row_index no longer matches the
    frozen order the Delta-q join depends on."""
    root, source_rows, _ = fixture_corpus
    manifest_rows = convert_rows(source_rows, root)
    manifest_rows = manifest_rows[::-1]
    result = _audit(fixture_corpus, manifest_rows)
    assert not result["checks"]["row_index_contiguous_in_frozen_order"]
    assert not result["checks"]["status_pass"]


def test_dropped_row_fails(fixture_corpus):
    root, source_rows, _ = fixture_corpus
    manifest_rows = convert_rows(source_rows, root)[:-1]
    result = _audit(fixture_corpus, manifest_rows)
    assert not result["checks"]["row_count_matches_source"]


def test_duplicate_qid_fails(fixture_corpus):
    root, source_rows, _ = fixture_corpus
    manifest_rows = convert_rows(source_rows, root)
    manifest_rows[1]["qid"] = manifest_rows[0]["qid"]
    result = _audit(fixture_corpus, manifest_rows)
    assert not result["checks"]["qid_unique_and_derived"]


def test_mutated_problem_text_fails(fixture_corpus):
    """Naive: prompt text 'normalized' during conversion (whitespace strip)."""
    root, source_rows, _ = fixture_corpus
    manifest_rows = convert_rows(source_rows, root)
    manifest_rows[0]["problem"] = manifest_rows[0]["problem"].replace("<image>", "")
    result = _audit(fixture_corpus, manifest_rows)
    assert not result["checks"]["byte_correspondence_with_frozen_rows"]


def test_tampered_image_file_fails(fixture_corpus):
    root, source_rows, _ = fixture_corpus
    manifest_rows = convert_rows(source_rows, root)
    (root / manifest_rows[0]["images"][0]["path"]).write_bytes(b"tampered")
    result = _audit(fixture_corpus, manifest_rows)
    assert not result["checks"]["image_sha256_matches_file_and_pairs_record"]


def test_conversion_deterministic(fixture_corpus):
    root, source_rows, _ = fixture_corpus
    first = convert_rows(source_rows, root)
    second = convert_rows(copy.deepcopy(source_rows), root)
    assert first == second
