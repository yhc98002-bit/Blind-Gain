from __future__ import annotations

from pathlib import Path

import pytest

from src.eval.parser_agreement import agreement_rows, build_r1v_messages


def test_r1v_messages_bind_each_marker_to_the_matching_image() -> None:
    row = {
        "row_index": 7,
        "problem": "<image>Compare <image> and solve.",
        "images": [{"path": "first.png"}, {"path": "second.png"}],
    }
    messages = build_r1v_messages(row, "{{ content }} FORMAT")
    content = messages[0]["content"]
    assert [item["image"] for item in content if item["type"] == "image"] == ["first.png", "second.png"]
    assert content[-1]["text"].endswith("FORMAT")


def test_parser_agreement_enforces_sample_floor_and_directions() -> None:
    rows = [
        {"response": "<answer>1</answer>", "ground_truth": "1", "source_row_index": index}
        for index in range(300)
    ]

    scored, metrics = agreement_rows(rows, lambda response, gold: 0.0)

    assert metrics["agreement"] == 0.0
    assert metrics["canonical_only"] == 300
    assert scored[0]["disagreement_direction"] == "canonical_only"
    with pytest.raises(ValueError, match="at least 300"):
        agreement_rows(rows[:299], lambda response, gold: 1.0)


def test_parser_agreement_launcher_has_immutable_shards() -> None:
    launcher = Path("scripts/launch_parser_agreement_generation.sh").read_text(encoding="utf-8")
    assert "Refusing to overwrite parser-agreement run" in launcher
    assert "expected_shards" in launcher
    assert "TRANSFORMERS_OFFLINE=1" in launcher
