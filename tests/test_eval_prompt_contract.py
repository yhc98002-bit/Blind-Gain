from __future__ import annotations

from pathlib import Path

from src.eval.prompt_contract import ANSWER_FORMAT_CONTRACT, format_question


ROOT = Path(__file__).resolve().parents[1]


def test_shared_eval_contract_requires_answer_tags() -> None:
    assert "<answer>" in ANSWER_FORMAT_CONTRACT
    assert "</answer>" in ANSWER_FORMAT_CONTRACT
    assert format_question("What is x?").endswith(ANSWER_FORMAT_CONTRACT)


def test_image_and_caption_evaluators_import_the_same_contract() -> None:
    image_source = (ROOT / "scripts/eval_qwen_vl_fliptrack.py").read_text(encoding="utf-8")
    caption_source = (ROOT / "scripts/eval_caption_qa_fliptrack.py").read_text(encoding="utf-8")
    assert "from src.eval.prompt_contract import format_question" in image_source
    assert "from src.eval.prompt_contract import ANSWER_FORMAT_CONTRACT" in caption_source
    assert "format_question(question)" in image_source
    assert "ANSWER_FORMAT_CONTRACT" in caption_source
