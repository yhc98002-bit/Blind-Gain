from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.audit_pilot_geo3k_step100_eval import audit_run
from scripts.run_pilot_geo3k_step100_eval import REGISTERED_DECODING, ROW_SCHEMA_VERSION
from src.eval.blind_solvability import PILOT_SCORING_MODE, score_greedy_item_pilot
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT
from src.rewards.answer_reward import PARSER_VERSION
from src.rewards.pilot_reward import PILOT_REWARD_VERSION


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(tmp_path: Path) -> Path:
    source = tmp_path / "source.jsonl"
    source_rows = [
        {"split": "test", "row_index": 0, "problem": "Find x.", "answer": "3", "images": []},
        {"split": "test", "row_index": 1, "problem": "Find y.", "answer": "4", "images": []},
    ]
    source.write_text(
        "".join(json.dumps(row) + "\n" for row in source_rows),
        encoding="utf-8",
    )
    training_run = tmp_path / "training"
    training_run.mkdir()
    training_manifest = training_run / "run_manifest.json"
    training_manifest.write_text('{"status":"complete"}\n', encoding="utf-8")
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()
    index = checkpoint / "model.safetensors.index.json"
    index.write_text('{"weight_map":{}}\n', encoding="utf-8")
    r19_marker = tmp_path / "step100_fliptrack_complete.json"
    r19_marker.write_text(
        json.dumps(
            {
                "status": "complete",
                "global_step": 100,
                "checkpoint_path": str(checkpoint),
                "checkpoint_index_sha256": _sha256(index),
                "checks": {"evaluation": True, "aggregate": True},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    retention = tmp_path / "RAW_STATE_RELOCATED.json"
    retention.write_text(
        json.dumps(
            {
                "merged_checkpoint_sha256": "merged-hash",
                "merged_checkpoint_files": [
                    {
                        "file": "checkpoint/model.safetensors.index.json",
                        "sha256": _sha256(index),
                        "size_bytes": index.stat().st_size,
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    run = tmp_path / "evaluation"
    run.mkdir()
    output = run / "per_item.jsonl"
    rows = []
    for source_row in source_rows:
        response = f"<answer>{source_row['answer']}</answer>"
        rows.append(
            {
                "schema_version": ROW_SCHEMA_VERSION,
                "arm": "a2b_noimage",
                "global_step": 100,
                "split": "test",
                "row_index": source_row["row_index"],
                "qid": None,
                "problem": source_row["problem"],
                "ground_truth": source_row["answer"],
                "image_sha256": [],
                "condition": "none",
                "source_metadata": None,
                "source_manifest_sha256": _sha256(source),
                "source_training_manifest_sha256": _sha256(training_manifest),
                "format_prompt_sha256": "prompt-hash",
                "model_revision": str(checkpoint),
                "checkpoint_index_sha256": _sha256(index),
                "greedy_response": response,
                "decoding": REGISTERED_DECODING,
                **score_greedy_item_pilot(
                    source_row["answer"], response, DEFAULT_PROMPT_CONTRACT
                ),
            }
        )
    output.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    manifest = {
        "run_id": "fixture",
        "job_type": "m2_pilot_geo3k_step100_eval",
        "status": "complete",
        "exit_code": 0,
        "artifacts_exist": True,
        "arm": "a2b_noimage",
        "condition": "none",
        "global_step": 100,
        "expected_row_count": 2,
        "tensor_parallel_width": 1,
        "replica_count": 1,
        "decoding": REGISTERED_DECODING,
        "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
        "parser_version": PARSER_VERSION,
        "pilot_reward_version": PILOT_REWARD_VERSION,
        "scoring_mode": PILOT_SCORING_MODE,
        "expected_artifacts": [str(output)],
        "data_manifest": str(source),
        "source_manifest_sha256": _sha256(source),
        "source_training_run": str(training_run),
        "source_training_manifest_sha256": _sha256(training_manifest),
        "model_revision": str(checkpoint),
        "checkpoint_index_sha256": _sha256(index),
        "r19_completion_marker": str(r19_marker),
        "r19_completion_marker_sha256": _sha256(r19_marker),
        "checkpoint_provenance_mode": "retention_marker",
        "retention_status": "verified",
        "retention_marker": str(retention),
        "retention_marker_sha256": _sha256(retention),
        "merged_checkpoint_sha256": "merged-hash",
    }
    (run / "run_manifest.json").write_text(
        json.dumps(manifest, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return run


def test_audit_recomputes_scores_and_provenance(tmp_path: Path) -> None:
    result = audit_run(_fixture(tmp_path), root=tmp_path, expected_row_count=2)

    assert result["status"] == "pass"
    assert all(result["checks"].values())
    assert result["row_count"] == 2
    assert result["score_recomputation_mismatch_count"] == 0
    assert result["performance_values_reported"] is False


def test_audit_rejects_false_strict_accounting(tmp_path: Path) -> None:
    run = _fixture(tmp_path)
    output = run / "per_item.jsonl"
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    rows[0]["acc_strict"] = False
    output.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )

    result = audit_run(run, root=tmp_path, expected_row_count=2)

    assert result["status"] == "fail"
    assert result["checks"]["scores_recompute"] is False
    assert result["checks"]["strict_identity"] is False
    assert result["score_recomputation_mismatch_fields"] == {"acc_strict": 1}


def test_audit_accepts_r19_index_provenance_without_relocation(tmp_path: Path) -> None:
    run = _fixture(tmp_path)
    manifest_path = run / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    retention = Path(manifest["retention_marker"])
    retention.unlink()
    manifest.update(
        checkpoint_provenance_mode="r19_marker_index",
        retention_status="absent",
        retention_marker=None,
        retention_marker_sha256=None,
        merged_checkpoint_sha256=None,
    )
    manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")

    result = audit_run(run, root=tmp_path, expected_row_count=2)

    assert result["status"] == "pass"
    assert result["checks"]["relocation_decoupled"] is True


def test_audit_rejects_truncated_output(tmp_path: Path) -> None:
    run = _fixture(tmp_path)
    output = run / "per_item.jsonl"
    output.write_text(output.read_text(encoding="utf-8").splitlines()[0] + "\n", encoding="utf-8")

    result = audit_run(run, root=tmp_path, expected_row_count=2)

    assert result["status"] == "fail"
    assert result["checks"]["row_count"] is False
    assert result["checks"]["row_identity_and_order"] is False
