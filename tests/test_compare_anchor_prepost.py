from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.compare_anchor_prepost import compare_runs


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_run(root: Path, name: str, correct: list[bool], *, changed_problem: bool = False) -> Path:
    run = root / name
    run.mkdir()
    rows = []
    identities = [("train", 0), ("test", 0)]
    for index, ((split, row_index), is_correct) in enumerate(zip(identities, correct)):
        rows.append(
            {
                "split": split,
                "row_index": row_index,
                "problem": "changed" if changed_problem and index == 1 else f"problem-{index}",
                "ground_truth": str(index),
                "image_sha256": [f"image-{index}"],
                "qid": None,
                "source_metadata": None,
                "greedy_correct": is_correct,
                "greedy_canonical_correct": is_correct,
                "greedy_contract_valid": True,
                "greedy_acc_strict": is_correct,
                "p_sample": float(is_correct),
                "mean_sampled_training_reward": float(is_correct),
                "mean_sampled_format_reward": 1.0,
            }
        )
    output = run / "per_item.jsonl"
    output.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    manifest = {
        "status": "complete",
        "exit_code": 0,
        "job_type": "l7_blind_solvability_geo3k_v2_guarded_rescore",
        "guarded_rescore_version": "l7-guarded-rescore-v1",
        "condition": "real",
        "data_manifest": "data.jsonl",
        "data_manifest_hash": "data-hash",
        "source_manifest_sha256": "source-hash",
        "train_filter_ids": "ids.json",
        "train_filter_sha256": "filter-hash",
        "format_prompt_sha256": "prompt-hash",
        "prompt_contract_sha256": "contract-hash",
        "parser_version": "canonical-v2",
        "pilot_reward_version": "pilot-reward-v1",
        "scoring_mode": "pilot-reward-v1+canonical-v2",
        "decoding": {"max_tokens": 2048},
        "sample_count": 16,
        "sample_temperature": 1.0,
        "group_size": 5,
        "max_tokens": 2048,
        "format_weight": 0.5,
        "symbolic_grader_guard_version": "posix-itimer-v1",
        "symbolic_grader_timeout_seconds": 5.0,
        "model_revision": name,
        "output_sha256": _sha256(output),
    }
    (run / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return run


def test_compare_anchor_prepost_uses_paired_items(tmp_path: Path) -> None:
    before = _make_run(tmp_path, "base", [False, False])
    after = _make_run(tmp_path, "step100", [True, True])

    result = compare_runs(before, after, bootstrap_draws=100, seed=7)

    assert result["status"] == "pass"
    assert result["splits"]["test"]["metrics"]["pilot_accuracy"]["delta"] == 1.0
    assert result["splits"]["test"]["pilot_accuracy_transitions"]["after_only"] == 1


def test_compare_anchor_prepost_rejects_same_identity_with_changed_item(tmp_path: Path) -> None:
    before = _make_run(tmp_path, "base", [False, False])
    after = _make_run(tmp_path, "step100", [True, True], changed_problem=True)

    result = compare_runs(before, after, bootstrap_draws=10)

    assert result["status"] == "fail"
    assert result["checks"]["row_identity_sets_identical"]
    assert not result["checks"]["item_content_identical"]
    assert result["item_content_mismatches"] == [["test", 0]]


def test_compare_anchor_prepost_rejects_manifest_output_hash_drift(tmp_path: Path) -> None:
    before = _make_run(tmp_path, "base", [False, False])
    after = _make_run(tmp_path, "step100", [True, True])
    output = after / "per_item.jsonl"
    output.write_text(
        output.read_text(encoding="utf-8").replace('{"split":', '{ "split":', 1),
        encoding="utf-8",
    )

    result = compare_runs(before, after, bootstrap_draws=10)

    assert result["status"] == "fail"
    assert not result["checks"]["manifest_output_hashes_match"]
