from __future__ import annotations

import json
from pathlib import Path

from src.eval.layer1_blind import build_text_prompt, score_predictions


def test_mmstar_blind_prompt_matches_harness_text_without_vision_tokens() -> None:
    row = {
        "index": 1,
        "question": "Which relation holds?",
        "answer": "B",
        "A": "left",
        "B": "right",
        "C": float("nan"),
    }
    prompt = build_text_prompt(row, "mmstar")
    assert prompt == (
        "Question: Which relation holds?\n"
        "Options:\n"
        "A. left\n"
        "B. right\n"
        "Please select the correct answer from the options above. \n"
    )
    assert "<image>" not in prompt and "<|vision_" not in prompt


def test_mathvista_blind_prompt_preserves_question_verbatim_without_vision_tokens() -> None:
    row = {"question": "Hint: answer an integer.\nQuestion: What is x?"}
    prompt = build_text_prompt(row, "mathvista")
    assert prompt == row["question"]
    assert "<image>" not in prompt and "<|vision_" not in prompt


def test_blind_scoring_handles_mmstar_and_mathvista_contracts() -> None:
    mmstar_rows = [{"index": 1, "question": "Q", "answer": "B", "category": "c", "A": "x", "B": "y"}]
    scored, metrics = score_predictions(mmstar_rows, ["<answer>B</answer>"], "mmstar")
    assert scored[0]["image_removed"] is True
    assert metrics["overall"]["Acc_final"] == 1.0

    mathvista_rows = [
        {
            "index": 2,
            "question": "Q",
            "answer": "1",
            "answer_option": float("nan"),
            "choices": "[]",
            "task": "math",
        }
    ]
    _, metrics = score_predictions(mathvista_rows, ["<answer>1.0</answer>"], "mathvista")
    assert metrics["overall"]["Acc_strict"] == 1.0


def test_blind_configs_share_registered_decode_contract() -> None:
    root = Path(__file__).resolve().parents[1]
    configs = [json.loads(path.read_text(encoding="utf-8")) for path in sorted((root / "configs/eval").glob("layer1_blind_*.json"))]
    assert len(configs) == 14
    locked = {(item["system_prompt"], item["max_new_tokens"], item["seed"]) for item in configs}
    assert locked == {("Return only the final answer wrapped exactly in <answer>...</answer>.", 256, 20260710)}


def test_blink_and_mmvp_reuse_the_image_mcq_option_block_builder() -> None:
    row = {
        "index": 7,
        "question": "Which image matches?",
        "answer": "A",
        "A": "first",
        "B": "second",
    }
    expected = (
        "Question: Which image matches?\n"
        "Options:\n"
        "A. first\n"
        "B. second\n"
        "Please select the correct answer from the options above. \n"
    )
    for dataset_type in ("blink", "mmvp"):
        prompt = build_text_prompt(row, dataset_type)
        assert prompt == expected
        assert "<image>" not in prompt and "<|vision_" not in prompt


def test_hallusionbench_and_mathverse_keep_the_question_verbatim() -> None:
    row = {"question": "Is the left circle larger than the right circle?"}
    for dataset_type in ("hallusionbench", "mathverse"):
        assert build_text_prompt(row, dataset_type) == row["question"]


def test_mmmu_blind_prompt_consumes_image_markers_like_split_mmmu() -> None:
    # MMMUDataset.build_prompt runs split_MMMU, which removes "<image N>" from the
    # text as it interleaves real images; the blind mirror must delete them too.
    row = {
        "index": 9,
        "question": "Refer to <image 1> and <image 2>. What is the missing amount?",
        "answer": "B",
        "A": "ten",
        "B": "see <image 3>",
    }
    prompt = build_text_prompt(row, "mmmu")
    assert "<image" not in prompt
    assert prompt == (
        "Question: Refer to  and . What is the missing amount?\n"
        "Options:\n"
        "A. ten\n"
        "B. see \n"
        "Please select the correct answer from the options above. \n"
    )


def test_mmstar_keeps_image_markers_because_image_mcq_does_not_split_them() -> None:
    row = {"index": 3, "question": "Look at <image 1>.", "answer": "A", "A": "yes"}
    assert "<image 1>" in build_text_prompt(row, "mmstar")


def test_mixed_format_blind_scoring_routes_per_item_not_per_benchmark() -> None:
    rows = [
        {"index": 1, "question": "Q1", "answer": "B", "A": "x", "B": "y", "category": "geometry"},
        {"index": 2, "question": "Q2", "answer": "11.8", "category": "geometry"},
    ]
    scored, _ = score_predictions(rows, ["<answer>B</answer>", "<answer>11.8</answer>"], "mathverse")
    assert scored[0]["scoring_contract"] == "multiple_choice_final_span"
    assert scored[0]["option_labels"] == ["A", "B"]
    assert scored[1]["scoring_contract"] == "open_final_span"
    assert scored[1]["option_labels"] == []
    assert all(record["category"] == "geometry" for record in scored)


def test_unsupported_blind_dataset_type_still_raises() -> None:
    import pytest

    with pytest.raises(ValueError):
        build_text_prompt({"question": "Q"}, "not_a_benchmark")
