from __future__ import annotations

from pathlib import Path

import json

import pytest

from src.eval.prompt_contract import (
    ANSWER_FORMAT_CONTRACT,
    DEFAULT_PROMPT_CONTRACT,
    format_question,
    load_prompt_contract_from_run_manifest,
    response_satisfies_contract,
)


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


def test_contract_valid_requires_one_nonempty_final_answer_tag() -> None:
    assert response_satisfies_contract("reasoning\n<answer>5</answer>")
    assert not response_satisfies_contract(r"reasoning \boxed{5}")
    assert not response_satisfies_contract("Answer: 5")
    assert not response_satisfies_contract("<answer></answer>")
    assert not response_satisfies_contract("<answer>5</answer> trailing")
    assert not response_satisfies_contract("<answer>5</answer><answer>6</answer>")


def test_prompt_contract_is_loaded_and_hash_checked_per_run(tmp_path: Path) -> None:
    manifest = tmp_path / "run_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "prompt_contract": DEFAULT_PROMPT_CONTRACT.to_dict(),
                "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
            }
        ),
        encoding="utf-8",
    )
    assert load_prompt_contract_from_run_manifest(manifest) == DEFAULT_PROMPT_CONTRACT
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["prompt_contract_sha256"] = "0" * 64
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        load_prompt_contract_from_run_manifest(manifest)
