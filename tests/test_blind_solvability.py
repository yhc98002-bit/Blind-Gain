from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from src.analysis.blind_solvability import real_blind_quadrants, summarize_condition
from src.eval.blind_solvability import build_conditioned_messages, pass_at_k, score_item


FORMAT = "{{ content | trim }} Return <answer>value</answer>."


def _row(path: Path) -> dict[str, object]:
    return {
        "split": "train",
        "row_index": 7,
        "problem": "<image>Find x.",
        "answer": "3",
        "images": [{"path": str(path), "sha256": "image-hash"}],
    }


def test_conditions_remove_or_replace_image_content_without_question_leakage(tmp_path: Path) -> None:
    image = tmp_path / "diagram.png"
    Image.new("RGB", (20, 12), "red").save(image)
    row = _row(image)

    real, real_paths = build_conditioned_messages(row, FORMAT, "real", tmp_path / "cache")
    gray, gray_paths = build_conditioned_messages(row, FORMAT, "gray", tmp_path / "cache")
    none, none_paths = build_conditioned_messages(row, FORMAT, "none", tmp_path / "cache")
    caption, caption_paths = build_conditioned_messages(
        row,
        FORMAT,
        "caption",
        tmp_path / "cache",
        captions={"image-hash": "A red triangle labeled x."},
    )

    assert real_paths == [str(image)]
    assert any(item["type"] == "image" for item in real[0]["content"])
    with Image.open(gray_paths[0]) as conditioned:
        assert np.all(np.asarray(conditioned) == 128)
    assert not any(item["type"] == "image" for item in none[0]["content"])
    assert none_paths == []
    assert "Find x" in none[0]["content"][0]["text"]
    caption_text = "".join(item["text"] for item in caption[0]["content"])
    assert "A red triangle labeled x" in caption_text
    assert caption_paths == []


def test_pass_at_k_and_item_scoring_use_all_sixteen_samples() -> None:
    assert pass_at_k(16, 0, 5) == 0.0
    assert pass_at_k(16, 16, 5) == 1.0
    assert pass_at_k(16, 1, 5) == 5 / 16
    samples = ["<answer>3</answer>"] * 4 + ["<answer>8</answer>"] * 12
    result = score_item("3", "<answer>3</answer>", samples, group_size=5)
    assert result["p_greedy"] == 1.0
    assert result["sample_correct_count"] == 4
    assert result["p_sample"] == 0.25
    assert result["pass_at_k16"] == 1.0
    assert result["variance_proxy"] == 0.1875


def test_summary_and_real_blind_quadrants() -> None:
    rows = [
        {"split": "train", "row_index": 0, "greedy_correct": True, "p_greedy": 1, "p_sample": 0.5, "pass_at_g": 0.8, "pass_at_k16": 1, "variance_proxy": 0.25},
        {"split": "train", "row_index": 1, "greedy_correct": False, "p_greedy": 0, "p_sample": 0, "pass_at_g": 0, "pass_at_k16": 0, "variance_proxy": 0},
    ]
    summary = summarize_condition(rows, seed=20260710)
    assert summary["n"] == 2
    blind = [dict(rows[0], greedy_correct=False), dict(rows[1], greedy_correct=True)]
    assert real_blind_quadrants(rows, blind) == {
        "both_correct": 0,
        "real_only": 1,
        "blind_only": 1,
        "neither_correct": 0,
    }
