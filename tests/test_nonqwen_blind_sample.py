from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.eval_nonqwen_blind_sample import (
    PARSER_VERSION,
    SCHEMA_VERSION,
    score_prediction,
    select_shard,
    validate_resume_prefix,
)


def test_canonical_scoring_separates_extractor_and_contract_validity() -> None:
    strict = score_prediction("<answer>5</answer>", "5")
    fallback = score_prediction("Answer: 5", "5")

    assert strict["acc_final"] is True
    assert strict["contract_valid"] is True
    assert strict["acc_strict"] is True
    assert fallback["acc_final"] is True
    assert fallback["extractor_valid"] is True
    assert fallback["contract_valid"] is False
    assert fallback["acc_strict"] is False


def test_shard_selection_is_disjoint_and_complete() -> None:
    rows = [{"row_index": index} for index in range(11)]

    shards = [select_shard(rows, 3, index, None) for index in range(3)]

    flattened = [row["row_index"] for shard in shards for row in shard]
    assert sorted(flattened) == list(range(11))
    assert len(flattened) == len(set(flattened))


def test_resume_prefix_rejects_backend_drift(tmp_path: Path) -> None:
    rows = [{"row_index": 7, "qid": "q7"}]
    resume = tmp_path / "result.partial"
    resume.write_text(
        json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "row_index": 7,
                "qid": "q7",
                "backend": "gemma3",
                "condition": "none",
                "source_manifest_sha256": "a" * 64,
                "caption_store_sha256": None,
                "decoding": {
                    "temperature": 0.0,
                    "top_p": 1.0,
                    "n": 1,
                    "max_new_tokens": 2048,
                },
                "parser_version": PARSER_VERSION,
                "runtime": {
                    "backend": "gemma3",
                    "generation_callable": True,
                    "processor_use_fast": False,
                    "torch_version": "2.6.0+cu118",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="backend"):
        validate_resume_prefix(
            resume,
            rows,
            backend="internvl3",
            condition="none",
            source_hash="a" * 64,
            caption_hash=None,
            max_new_tokens=2048,
        )


def test_resume_prefix_accepts_exact_contract(tmp_path: Path) -> None:
    rows = [{"row_index": 7, "qid": "q7"}]
    resume = tmp_path / "result.partial"
    payload = {
        "schema_version": SCHEMA_VERSION,
        "row_index": 7,
        "qid": "q7",
        "backend": "internvl3",
        "condition": "caption",
        "source_manifest_sha256": "a" * 64,
        "caption_store_sha256": "b" * 64,
        "decoding": {
            "temperature": 0.0,
            "top_p": 1.0,
            "n": 1,
            "max_new_tokens": 2048,
        },
        "parser_version": PARSER_VERSION,
        "runtime": {
            "backend": "internvl3",
            "generation_callable": True,
            "generation_shim_applied": True,
            "generation_config_ready": True,
            "timm_version": "0.9.12",
            "use_flash_attn": False,
        },
    }
    resume.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    lines = validate_resume_prefix(
        resume,
        rows,
        backend="internvl3",
        condition="caption",
        source_hash="a" * 64,
        caption_hash="b" * 64,
        max_new_tokens=2048,
    )

    assert len(lines) == 1


def test_blind_launcher_pins_tp1_greedy_and_frozen_caption_store() -> None:
    root = Path(__file__).resolve().parents[1]
    launcher = (root / "scripts/launch_nonqwen_blind_sample.sh").read_text(
        encoding="utf-8"
    )

    assert 'tensor_parallel_width: 1' in launcher
    assert 'replica_count: 1' in launcher
    assert 'decoding: {temperature: 0.0, top_p: 1.0, n: 1}' in launcher
    assert 'virl39k_blind_sample_4096.jsonl' in launcher
    assert 'virl39k_sample4096_qwen25vl3b_captionstore384_20260710T094300Z' in launcher
    assert 'refusing to overwrite immutable non-Qwen blind run' in launcher
    assert 'aggregate_nonqwen_blind_sample.py' in launcher
    assert 'expected_artifacts: [$output, $metrics]' in launcher
    assert 'BLIND_GAINS_NONQWEN_PYTHON' in launcher
    assert 'runtime_python: $runtime_python' in launcher
    assert 'runtime_audit_sha256:' in launcher
    assert 'runtime_freeze_sha256:' in launcher
