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
    assert len(configs) == 4
    locked = {(item["system_prompt"], item["max_new_tokens"], item["seed"]) for item in configs}
    assert locked == {("Return only the final answer wrapped exactly in <answer>...</answer>.", 256, 20260710)}
