from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from src.analysis.blind_solvability import real_blind_quadrants, summarize_condition
from src.eval.blind_solvability import build_conditioned_messages, pass_at_k, score_item, vllm_multimodal_limits
from scripts.summarize_blind_solvability import render_markdown


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


def test_vllm_reserves_no_visual_tokens_for_text_only_conditions() -> None:
    assert vllm_multimodal_limits("real") == {"image": 1, "video": 0}
    assert vllm_multimodal_limits("real", max_images=8) == {"image": 8, "video": 0}
    assert vllm_multimodal_limits("caption") == {"image": 0, "video": 0}
    assert vllm_multimodal_limits("none") == {"image": 0, "video": 0}


def test_summary_and_real_blind_quadrants() -> None:
    rows = [
        {"split": "train", "row_index": 0, "greedy_correct": True, "p_greedy": 1, "p_sample": 0.5, "pass_at_g": 0.8, "pass_at_k16": 1, "variance_proxy": 0.25},
        {"split": "train", "row_index": 1, "greedy_correct": False, "p_greedy": 0, "p_sample": 0, "pass_at_g": 0, "pass_at_k16": 0, "variance_proxy": 0},
    ]
    summary = summarize_condition(rows, seed=20260710)
    assert summary["n"] == 2
    assert summary["p_sample_distribution"]["zero"]["mean"] == 0.5
    assert summary["p_sample_distribution"]["mid_0p2_0p8"]["mean"] == 0.5
    blind = [dict(rows[0], greedy_correct=False), dict(rows[1], greedy_correct=True)]
    assert real_blind_quadrants(rows, blind) == {
        "both_correct": 0,
        "real_only": 1,
        "blind_only": 1,
        "neither_correct": 0,
    }


def test_markdown_renderer_exposes_registered_metrics() -> None:
    metric = {"mean": 0.5, "ci_low": 0.4, "ci_high": 0.6}
    condition_summary = {
        "metrics": {
            name: metric
            for name in ("p_greedy", "p_sample", "pass_at_g", "pass_at_k16", "variance_proxy")
        },
        "p_sample_midband_0p2_0p8": metric,
        "p_sample_distribution": {
            name: metric for name in ("zero", "low_0_0p2", "mid_0p2_0p8", "high_0p8_1", "one")
        },
    }
    summary = {
        "n_items": 2,
        "runs": {condition: {"run_dir": f"runs/{condition}"} for condition in ("real", "gray", "noise", "none", "caption")},
        "aggregates": {
            condition: {split: condition_summary for split in ("all", "train", "test")}
            for condition in ("real", "gray", "noise", "none", "caption")
        },
        "real_blind_greedy_quadrants": {
            condition: {
                split: {"both_correct": 1, "real_only": 0, "blind_only": 0, "neither_correct": 1}
                for split in ("all", "train", "test")
            }
            for condition in ("gray", "noise", "none", "caption")
        },
    }
    rendered = render_markdown(summary)
    assert "pass@G=5" in rendered
    assert "p in [0.2, 0.8]" in rendered
    assert "Greedy real-vs-blind quadrants" in rendered
    assert "Sample-p distribution" in rendered


def test_markdown_renderer_supports_single_audit_split() -> None:
    metric = {"mean": 0.5, "ci_low": 0.4, "ci_high": 0.6}
    condition_summary = {
        "metrics": {
            name: metric
            for name in ("p_greedy", "p_sample", "pass_at_g", "pass_at_k16", "variance_proxy")
        },
        "p_sample_midband_0p2_0p8": metric,
        "p_sample_distribution": {
            name: metric for name in ("zero", "low_0_0p2", "mid_0p2_0p8", "high_0p8_1", "one")
        },
    }
    summary = {
        "dataset_name": "ViRL39K-4096",
        "splits": ["audit"],
        "n_items": 1,
        "runs": {condition: {"run_dir": f"runs/{condition}"} for condition in ("real", "gray", "noise", "none", "caption")},
        "aggregates": {
            condition: {split: condition_summary for split in ("all", "audit")}
            for condition in ("real", "gray", "noise", "none", "caption")
        },
        "real_blind_greedy_quadrants": {
            condition: {
                split: {"both_correct": 0, "real_only": 0, "blind_only": 0, "neither_correct": 1}
                for split in ("all", "audit")
            }
            for condition in ("gray", "noise", "none", "caption")
        },
    }
    rendered = render_markdown(summary)
    assert "# ViRL39K-4096 Blind-Solvability Audit" in rendered
    assert "| real | audit |" in rendered
