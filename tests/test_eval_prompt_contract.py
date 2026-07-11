from __future__ import annotations

from pathlib import Path

import hashlib
import json

import pytest

from src.eval.prompt_contract import (
    ANSWER_FORMAT_CONTRACT,
    DEFAULT_PROMPT_CONTRACT,
    format_question,
    load_prompt_contract_from_legacy_config_run_manifest,
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


def test_vlmeval_launch_and_postprocess_pin_the_run_contract() -> None:
    launch_source = (ROOT / "scripts" / "launch_vlmevalkit_eval.sh").read_text(encoding="utf-8")
    postprocess_source = (ROOT / "scripts" / "launch_vlmeval_postprocess.sh").read_text(encoding="utf-8")
    assert "prompt_contract_sha256" in launch_source
    assert "PromptContract(" in launch_source
    assert "--run-manifest ${SOURCE_RUN_DIR}/run_manifest.json" in postprocess_source


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


def _write_legacy_run(tmp_path: Path, prompts: list[str]) -> tuple[Path, Path]:
    config = tmp_path / "configs" / "eval" / "legacy.json"
    config.parent.mkdir(parents=True)
    config.write_text(
        json.dumps(
            {
                "model": {
                    f"model-{index}": {"system_prompt": prompt}
                    for index, prompt in enumerate(prompts)
                }
            }
        ),
        encoding="utf-8",
    )
    manifest = tmp_path / "run_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "config_path": str(config.relative_to(tmp_path)),
                "config_hash": hashlib.sha256(config.read_bytes()).hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    return manifest, config


def test_legacy_contract_resolution_uses_hash_pinned_per_run_config(tmp_path: Path) -> None:
    instruction = "Return only the final answer wrapped exactly in <answer>...</answer>."
    manifest, _ = _write_legacy_run(tmp_path, [instruction])

    contract = load_prompt_contract_from_legacy_config_run_manifest(manifest, tmp_path)

    assert contract.instruction == instruction
    assert contract.response_format == "single_final_answer_tag"


def test_legacy_contract_resolution_rejects_config_drift(tmp_path: Path) -> None:
    manifest, config = _write_legacy_run(
        tmp_path, ["Return only <answer>the answer</answer>."]
    )
    config.write_text("{}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="config hash mismatch"):
        load_prompt_contract_from_legacy_config_run_manifest(manifest, tmp_path)


def test_legacy_contract_resolution_rejects_ambiguous_or_untagged_prompts(
    tmp_path: Path,
) -> None:
    ambiguous_manifest, _ = _write_legacy_run(
        tmp_path / "ambiguous",
        ["Use <answer>x</answer>.", "Use <answer>y</answer>."],
    )
    with pytest.raises(ValueError, match="exactly one nonempty system_prompt"):
        load_prompt_contract_from_legacy_config_run_manifest(
            ambiguous_manifest, tmp_path / "ambiguous"
        )

    untagged_manifest, _ = _write_legacy_run(tmp_path / "untagged", ["Return one answer."])
    with pytest.raises(ValueError, match="does not register the answer-tag contract"):
        load_prompt_contract_from_legacy_config_run_manifest(
            untagged_manifest, tmp_path / "untagged"
        )
