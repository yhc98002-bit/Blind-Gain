from __future__ import annotations

from pathlib import Path

import pytest

from scripts.build_caption_qa_pairs import partition_rows
from src.captioning.qa_pairs import build_caption_qa_rows, build_private_caption_qa_rows


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
    rows = build_caption_qa_rows(
        release,
        key,
        captions,
        "/release",
        allow_extra_captions=True,
    )
    assert len(rows) == 1


def test_caption_qa_adapter_rejects_release_key_member_mismatch() -> None:
    release, key, captions = _fixture_rows()
    key[0]["members"][0]["member_id"] = "wrong-member"
    with pytest.raises(ValueError, match="member mismatch"):
        build_caption_qa_rows(release, key, captions, "/release")


def test_caption_qa_shards_are_deterministic_and_exhaustive() -> None:
    rows = [{"pair_id": str(index)} for index in range(10)]
    shards = partition_rows(rows, 3)
    assert [[row["pair_id"] for row in shard] for shard in shards] == [
        ["0", "3", "6", "9"],
        ["1", "4", "7"],
        ["2", "5", "8"],
    ]
    with pytest.raises(ValueError, match="positive"):
        partition_rows(rows, 0)


def test_private_caption_adapter_preserves_constructed_sides_and_is_strict() -> None:
    private = [
        {
            "pair_id": "calibration-pair",
            "question": "Read the code.",
            "category": "document",
            "template_id": "dense",
            "catch_twin_id": None,
            "answer_a": "A1",
            "answer_b": "B2",
            "image_a_path": "source/a.png",
            "image_b_path": "source/b.png",
            "image_a_sha256": "hash-a",
            "image_b_sha256": "hash-b",
        }
    ]
    captions = [
        {"image_sha256": "hash-a", "caption": "code A1"},
        {"image_sha256": "hash-b", "caption": "code B2"},
    ]

    rows = build_private_caption_qa_rows(private, captions)

    assert rows[0]["member_id_a"] == "calibration-pair:a"
    assert rows[0]["answer_b"] == "B2"
    assert rows[0]["caption_a"] == "code A1"
    with pytest.raises(ValueError, match="outside the private manifest"):
        build_private_caption_qa_rows(
            private,
            [*captions, {"image_sha256": "extra", "caption": "extra"}],
        )


def test_private_caption_launcher_is_cpu_only_and_calibration_scoped() -> None:
    launcher = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "launch_private_caption_qa_pair_build.sh"
    ).read_text(encoding="utf-8")

    assert 'job_type: "l11_private_caption_qa_pair_adapter"' in launcher
    assert "gpu_ids: []" in launcher
    assert "tensor_parallel_width: 0" in launcher
    assert 'scope: "internal-calibration-only"' in launcher
    assert "build_private_caption_qa_pairs.py" in launcher


def test_release_caption_launcher_supports_combined_store_without_losing_placement() -> None:
    launcher = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "launch_caption_qa_pair_build.sh"
    ).read_text(encoding="utf-8")

    assert "ALLOW_EXTRA_CAPTIONS" in launcher
    assert "--allow-extra-captions" in launcher
    assert "gpu_ids: []" in launcher
    assert "tensor_parallel_width: 0" in launcher
    assert "replica_count: 0" in launcher
