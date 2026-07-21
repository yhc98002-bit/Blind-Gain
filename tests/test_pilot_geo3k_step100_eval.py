from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.run_pilot_geo3k_step100_eval import (
    REGISTERED_DECODING,
    ROW_SCHEMA_VERSION,
    load_validated_resume_prefix,
)
from src.eval.blind_solvability import score_greedy_item_pilot
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT


ROOT = Path(__file__).resolve().parents[1]


def test_greedy_pilot_scoring_splits_extractor_and_contract_validity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shadow = tmp_path / "must-not-be-written.jsonl"
    monkeypatch.setenv("BLIND_GAINS_REWARD_SHADOW_LOG", str(shadow))

    strict = score_greedy_item_pilot(
        "5",
        "<answer>5</answer>",
        DEFAULT_PROMPT_CONTRACT,
    )
    fallback = score_greedy_item_pilot(
        "5",
        r"The result is \boxed{5}.",
        DEFAULT_PROMPT_CONTRACT,
    )

    assert strict["acc_final"] is True
    assert strict["contract_valid"] is True
    assert strict["acc_strict"] is True
    assert fallback["acc_final"] is True
    assert fallback["extractor_valid"] is True
    assert fallback["contract_valid"] is False
    assert fallback["acc_strict"] is False
    assert not shadow.exists()


def _resume_row() -> dict[str, object]:
    return {
        "schema_version": ROW_SCHEMA_VERSION,
        "arm": "a2b_noimage",
        "global_step": 100,
        "split": "test",
        "row_index": 0,
        "problem": "Find x.",
        "ground_truth": "5",
        "image_sha256": [],
        "condition": "none",
        "model_revision": "checkpoint",
        "checkpoint_index_sha256": "index-hash",
        "source_manifest_sha256": "source-hash",
        "source_training_manifest_sha256": "training-hash",
        "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
        "decoding": REGISTERED_DECODING,
        "greedy_response": "<answer>5</answer>",
        "training_reward": 1.0,
        "acc_final": True,
        "acc_strict": True,
        "extractor_valid": True,
        "contract_valid": True,
        "canonical_eval_reward": 1.0,
        "native_r1v_shadow_reward": 1.0,
        "reward_disagreement_reason": "none",
    }


def test_resume_rejects_checkpoint_substitution(tmp_path: Path) -> None:
    path = tmp_path / "resume.jsonl"
    path.write_text(json.dumps(_resume_row()) + "\n", encoding="utf-8")
    rows = [
        {
            "split": "test",
            "row_index": 0,
            "problem": "Find x.",
            "answer": "5",
            "images": [],
        }
    ]

    with pytest.raises(ValueError, match="checkpoint_index_sha256"):
        load_validated_resume_prefix(
            path,
            rows,
            arm="a2b_noimage",
            condition="none",
            model_revision="checkpoint",
            checkpoint_index_sha256="different-index-hash",
            source_manifest_sha256="source-hash",
            source_training_manifest_sha256="training-hash",
        )


def test_resume_rejects_global_step_substitution(tmp_path: Path) -> None:
    path = tmp_path / "resume.jsonl"
    row = _resume_row()
    row["global_step"] = 150
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    rows = [
        {
            "split": "test",
            "row_index": 0,
            "problem": "Find x.",
            "answer": "5",
            "images": [],
        }
    ]

    with pytest.raises(ValueError, match="global_step"):
        load_validated_resume_prefix(
            path,
            rows,
            arm="a2b_noimage",
            condition="none",
            model_revision="checkpoint",
            checkpoint_index_sha256="index-hash",
            source_manifest_sha256="source-hash",
            source_training_manifest_sha256="training-hash",
        )


def test_launcher_rejects_missing_inputs_before_contacting_node(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            "bash",
            "scripts/launch_pilot_geo3k_step100_eval.sh",
            "a1_real",
            "an12",
            "4",
            str(tmp_path / "missing-run"),
            str(tmp_path / "missing-marker.json"),
            str(tmp_path / "missing-checkpoint"),
            "-",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "required input is absent" in result.stderr
    assert "Could not resolve hostname" not in result.stderr


def test_launcher_records_locked_tp1_contract() -> None:
    source = (ROOT / "scripts/launch_pilot_geo3k_step100_eval.sh").read_text(
        encoding="utf-8"
    )

    assert 'EVALUATION_JOB_TYPE="m2_pilot_geo3k_step100_eval"' in source
    assert 'EVALUATION_JOB_TYPE="m3_pilot_geo3k_checkpoint_eval"' in source
    assert "job_type: $job_type" in source
    assert "tensor_parallel_width: 1" in source
    assert "replica_count: 1" in source
    assert "expected_row_count: 601" in source
    assert "--max-tokens ${MAX_TOKENS}" in source
    assert "(.checks | type == \"object\" and length > 0 and all(.[]; . == true))" in source
    assert 'CHECKPOINT_PROVENANCE_MODE="r19_marker_index"' in source
    assert 'RETENTION_STATUS="absent"' in source
    assert "R19 marker does not bind the current merged checkpoint index" in source
    assert "retention marker does not bind" not in source
