from __future__ import annotations

import pytest

from src.captioning.qa_pairs import build_caption_qa_rows


def _fixture_rows() -> tuple[list[dict], list[dict], list[dict]]:
    release = [
        {
            "pair_id": "opaque-pair",
            "question": "Which value?",
            "members": [
                {
                    "member_id": "member-b",
                    "image_sha256": "hash-b",
                    "image_path": "images/b.png",
                },
                {
                    "member_id": "member-a",
                    "image_sha256": "hash-a",
                    "image_path": "images/a.png",
                },
            ],
        }
    ]
    key = [
        {
            "pair_id": "opaque-pair",
            "source_pair_id": "source-pair",
            "category": "test",
            "template_id": "template",
            "catch_twin_id": None,
            "members": [
                {"member_id": "member-a", "source_side": "a", "answer": "11"},
                {"member_id": "member-b", "source_side": "b", "answer": "29"},
            ],
        }
    ]
    captions = [
        {"image_sha256": "hash-b", "caption": "caption b"},
        {"image_sha256": "hash-a", "caption": "caption a"},
    ]
    return release, key, captions


def test_caption_qa_adapter_restores_source_sides_after_member_shuffle() -> None:
    release, key, captions = _fixture_rows()
    rows = build_caption_qa_rows(release, key, captions, "/release")
    assert len(rows) == 1
    assert rows[0]["answer_a"] == "11"
    assert rows[0]["caption_a"] == "caption a"
    assert rows[0]["image_a_sha256"] == "hash-a"
    assert rows[0]["answer_b"] == "29"
    assert rows[0]["caption_b"] == "caption b"
    assert rows[0]["image_b_path"] == "/release/images/b.png"


def test_caption_qa_adapter_requires_exact_caption_coverage() -> None:
    release, key, captions = _fixture_rows()
    with pytest.raises(ValueError, match="missing caption"):
        build_caption_qa_rows(release, key, captions[:1], "/release")
    captions.append({"image_sha256": "extra", "caption": "not in release"})
    with pytest.raises(ValueError, match="outside the release"):
        build_caption_qa_rows(release, key, captions, "/release")


def test_caption_qa_adapter_rejects_release_key_member_mismatch() -> None:
    release, key, captions = _fixture_rows()
    key[0]["members"][0]["member_id"] = "wrong-member"
    with pytest.raises(ValueError, match="member mismatch"):
        build_caption_qa_rows(release, key, captions, "/release")
