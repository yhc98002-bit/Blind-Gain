from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.run_blind_solvability_v2 import load_validated_v2_resume_prefix
from src.eval.blind_solvability import (
    PILOT_ROW_SCHEMA_VERSION,
    PILOT_SCORING_MODE,
    jeffreys_smoothed_probability,
    load_geometry_rows,
    load_train_filter_ids,
    mixed_group_probability,
    score_item_pilot,
)
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT
from src.rewards.answer_reward import PARSER_VERSION
from src.rewards.pilot_reward import (
    DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS,
    PILOT_REWARD_VERSION,
    SYMBOLIC_GRADER_GUARD_VERSION,
)


def _write_manifest(path: Path) -> None:
    rows = [
        {"split": "train", "row_index": 0, "problem": "p0", "answer": "0", "images": []},
        {"split": "train", "row_index": 1, "problem": "p1", "answer": "1", "images": []},
        {"split": "test", "row_index": 0, "problem": "t0", "answer": "2", "images": []},
    ]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_filtered_loader_keeps_exact_train_ids_and_untouched_test(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.jsonl"
    _write_manifest(manifest)

    rows = load_geometry_rows(manifest, train_filter_ids={1})

    assert [(row["split"], row["row_index"]) for row in rows] == [("train", 1), ("test", 0)]


def test_filtered_loader_fails_on_unknown_train_id(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.jsonl"
    _write_manifest(manifest)

    with pytest.raises(ValueError, match="absent from the selected manifest"):
        load_geometry_rows(manifest, train_filter_ids={1, 999})


def test_unfiltered_audit_split_does_not_require_train_filter(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.jsonl"
    _write_manifest(manifest)

    rows = load_geometry_rows(manifest, splits=("test",), train_filter_ids=None)

    assert [(row["split"], row["row_index"]) for row in rows] == [("test", 0)]


def test_train_filter_rejects_duplicate_or_boolean_ids(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text("[1, 1]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        load_train_filter_ids(duplicate)

    boolean = tmp_path / "boolean.json"
    boolean.write_text("[true]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="non-negative integers"):
        load_train_filter_ids(boolean)


def test_jeffreys_q_is_nonzero_at_raw_probability_boundary() -> None:
    p_i = jeffreys_smoothed_probability(16, 0)

    assert p_i == pytest.approx(0.5 / 17.0)
    assert mixed_group_probability(p_i, 5) > 0.0


def test_pilot_scoring_records_exact_reward_and_canonical_comparison(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inherited_shadow = tmp_path / "must-not-be-written.jsonl"
    monkeypatch.setenv("BLIND_GAINS_REWARD_SHADOW_LOG", str(inherited_shadow))
    wrong = ["<answer>4</answer>"] * 16
    scored = score_item_pilot(
        "3",
        "<answer>3</answer>",
        wrong,
        group_size=5,
        prompt_contract=DEFAULT_PROMPT_CONTRACT,
    )

    assert scored["scoring_mode"] == PILOT_SCORING_MODE
    assert scored["pilot_reward_version"] == PILOT_REWARD_VERSION
    assert scored["symbolic_grader_guard_version"] == SYMBOLIC_GRADER_GUARD_VERSION
    assert scored["symbolic_grader_timeout_seconds"] == (
        DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS
    )
    assert scored["greedy_training_reward"] == 1.0
    assert scored["sample_correct_count"] == 0
    assert scored["p_sample"] == 0.0
    assert scored["p_i_jeffreys"] == pytest.approx(0.5 / 17.0)
    assert scored["q_i"] > 0.0
    assert scored["canonical_p_sample"] == 0.0
    assert len(scored["sampled_reward_disagreement_reasons"]) == 16
    assert not inherited_shadow.exists()


def _resume_row() -> dict[str, object]:
    return {
        "schema_version": PILOT_ROW_SCHEMA_VERSION,
        "split": "train",
        "row_index": 0,
        "problem": "p0",
        "ground_truth": "0",
        "image_sha256": [],
        "condition": "none",
        "scoring_mode": PILOT_SCORING_MODE,
        "pilot_reward_version": PILOT_REWARD_VERSION,
        "parser_version": PARSER_VERSION,
        "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
        "source_manifest_sha256": "source-hash",
        "train_filter_sha256": "filter-hash",
        "sampled_responses": ["<answer>0</answer>"] * 16,
        "p_i_jeffreys": 0.5,
        "q_i": 0.5,
        "greedy_training_reward": 1.0,
        "mean_sampled_training_reward": 1.0,
        "canonical_p_sample": 1.0,
        "sampled_reward_disagreement_reasons": ["none"] * 16,
        "decoding": {
            "greedy": {"temperature": 0.0, "top_p": 1.0, "n": 1},
            "sampled": {"temperature": 1.0, "top_p": 1.0, "n": 16},
            "max_tokens": 2048,
            "seed": 20260710,
        },
    }


def test_v2_resume_rejects_legacy_512_token_output(tmp_path: Path) -> None:
    row = _resume_row()
    row["decoding"]["max_tokens"] = 512
    path = tmp_path / "legacy.jsonl"
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    source = [{"split": "train", "row_index": 0, "problem": "p0", "answer": "0", "images": []}]

    with pytest.raises(ValueError, match="decoding"):
        load_validated_v2_resume_prefix(
            path,
            source,
            condition="none",
            batch_size=1,
            seed=20260710,
            source_manifest_sha256="source-hash",
            train_filter_sha256="filter-hash",
        )
