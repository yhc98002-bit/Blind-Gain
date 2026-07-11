from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.summarize_blind_solvability_v2 import audit_runs, build_summary
from src.eval.blind_solvability import (
    CONDITIONS,
    PILOT_ROW_SCHEMA_VERSION,
    PILOT_SCORING_MODE,
    score_item_pilot,
)
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT
from src.rewards.answer_reward import PARSER_VERSION
from src.rewards.pilot_reward import PILOT_REWARD_VERSION


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture_runs(tmp_path: Path) -> dict[str, Path]:
    source = tmp_path / "source.jsonl"
    source_rows = [
        {"split": "train", "row_index": 7, "problem": "Find x.", "answer": "3", "images": []},
        {"split": "test", "row_index": 2, "problem": "Find y.", "answer": "4", "images": []},
    ]
    source.write_text("".join(json.dumps(row) + "\n" for row in source_rows), encoding="utf-8")
    train_filter = tmp_path / "filter.json"
    train_filter.write_text("[7]\n", encoding="utf-8")
    filter_hash = _sha256(train_filter)
    source_hash = _sha256(source)
    decoding = {
        "greedy": {"temperature": 0.0, "top_p": 1.0, "n": 1},
        "sampled": {"temperature": 1.0, "top_p": 1.0, "n": 16},
        "max_tokens": 2048,
        "seed": 20260710,
    }

    runs = {}
    for condition in CONDITIONS:
        run = tmp_path / condition
        run.mkdir()
        records = []
        for source_row in source_rows:
            greedy = f"<answer>{source_row['answer']}</answer>"
            sampled = [greedy] * 8 + ["<answer>999</answer>"] * 8
            records.append(
                {
                    "schema_version": PILOT_ROW_SCHEMA_VERSION,
                    "split": source_row["split"],
                    "row_index": source_row["row_index"],
                    "qid": None,
                    "problem": source_row["problem"],
                    "ground_truth": source_row["answer"],
                    "image_sha256": [],
                    "condition": condition,
                    "source_metadata": None,
                    "source_manifest_sha256": source_hash,
                    "train_filter_sha256": filter_hash,
                    "format_prompt_sha256": "prompt",
                    "greedy_response": greedy,
                    "sampled_responses": sampled,
                    **score_item_pilot(
                        source_row["answer"],
                        greedy,
                        sampled,
                        group_size=5,
                        prompt_contract=DEFAULT_PROMPT_CONTRACT,
                    ),
                    "decoding": decoding,
                }
            )
        (run / "per_item.jsonl").write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in records),
            encoding="utf-8",
        )
        manifest = {
            "run_id": f"fixture-{condition}",
            "job_type": "l7_blind_solvability_geo3k_v2",
            "status": "complete",
            "condition": condition,
            "data_manifest": str(source),
            "data_manifest_hash": "data",
            "source_manifest_sha256": source_hash,
            "train_filter_ids": str(train_filter),
            "train_filter_sha256": filter_hash,
            "model_revision": "fixture",
            "scoring_mode": PILOT_SCORING_MODE,
            "pilot_reward_version": PILOT_REWARD_VERSION,
            "parser_version": PARSER_VERSION,
            "prompt_contract": DEFAULT_PROMPT_CONTRACT.to_dict(),
            "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
            "group_size": 5,
            "sample_count": 16,
            "sample_temperature": 1.0,
            "max_tokens": 2048,
            "format_weight": 0.5,
            "seed": 20260710,
            "decoding": decoding,
            "git_hash": "git",
            "config_hash": "config",
        }
        (run / "run_manifest.json").write_text(
            json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8"
        )
        runs[condition] = run
    return runs


def test_v2_audit_recomputes_all_scores_and_builds_summary(tmp_path: Path) -> None:
    audit, rows = audit_runs(_fixture_runs(tmp_path))

    assert audit["status"] == "pass"
    assert audit["expected_split_counts"] == {"test": 1, "train": 1}
    assert audit["recomputed_score_mismatch_count"] == 0
    summary = build_summary(rows, audit)
    assert summary["n_items"] == 2
    assert set(summary["aggregates"]) == set(CONDITIONS)


def test_v2_audit_rejects_stale_stored_q_i(tmp_path: Path) -> None:
    runs = _fixture_runs(tmp_path)
    path = runs["caption"] / "per_item.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    rows[0]["q_i"] = 0.0
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    audit, _ = audit_runs(runs)

    assert audit["status"] == "fail"
    assert audit["checks"]["recomputed_scores_match"] is False
    assert audit["recomputed_score_mismatch_fields"] == {"q_i": 1}


def test_v2_audit_rejects_shared_legacy_decoding_contract(tmp_path: Path) -> None:
    runs = _fixture_runs(tmp_path)
    for run in runs.values():
        manifest_path = run / "run_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["max_tokens"] = 512
        manifest["decoding"]["max_tokens"] = 512
        manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
        output_path = run / "per_item.jsonl"
        rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
        for row in rows:
            row["decoding"]["max_tokens"] = 512
        output_path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    audit, _ = audit_runs(runs)

    assert audit["status"] == "fail"
    assert audit["checks"]["all_run_manifests_complete_and_registered"] is False
    assert audit["checks"]["decoding_parameters_locked"] is False
