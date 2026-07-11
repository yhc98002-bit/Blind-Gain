from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.summarize_blind_solvability import build_summary
from src.eval.blind_solvability import CONDITIONS, score_item
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT
from src.rewards.answer_reward import PARSER_VERSION


def _row(condition: str) -> dict[str, object]:
    greedy = "<answer>3</answer>"
    sampled = ["<answer>3</answer>"] * 8 + ["<answer>4</answer>"] * 8
    return {
        "schema_version": "blind-gains.blind-solvability.v2",
        "split": "audit",
        "row_index": 0,
        "qid": "audit-0",
        "problem": "<image>Find x.",
        "ground_truth": "3",
        "image_sha256": ["image-sha"],
        "condition": condition,
        "source_metadata": {"source": "fixture"},
        "greedy_response": greedy,
        "sampled_responses": sampled,
        **score_item("3", greedy, sampled, group_size=5),
        "decoding": {
            "greedy": {"temperature": 0.0, "top_p": 1.0, "n": 1},
            "sampled": {"temperature": 1.0, "top_p": 1.0, "n": 16},
            "max_tokens": 512,
            "seed": 20260710,
        },
    }


def _runs(tmp_path: Path, mutations: dict[str, dict[str, object]] | None = None) -> dict[str, Path]:
    result = {}
    for condition in CONDITIONS:
        run = tmp_path / condition
        run.mkdir()
        row = _row(condition)
        for key, value in (mutations or {}).get(condition, {}).items():
            row[key] = copy.deepcopy(value)
        (run / "per_item.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
        manifest = {
            "run_id": f"run-{condition}",
            "status": "complete",
            "condition": condition,
            "model_revision": "qwen-test",
            "data_manifest": "fixture.jsonl",
            "group_size": 5,
            "sample_count": 16,
            "sample_temperature": 1.0,
            "prompt_contract": DEFAULT_PROMPT_CONTRACT.to_dict(),
            "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
            "parser_version": PARSER_VERSION,
            "git_hash": "git",
            "config_hash": "config",
            "data_manifest_hash": "data",
        }
        (run / "run_manifest.json").write_text(json.dumps(manifest) + "\n", encoding="utf-8")
        result[condition] = run
    return result


def test_summary_accepts_exact_item_and_decoding_contract(tmp_path: Path) -> None:
    summary = build_summary(
        _runs(tmp_path),
        dataset_name="fixture",
        splits=("audit",),
    )

    assert summary["schema_version"] == "blind-gains.blind-solvability-summary.v4"
    assert summary["n_items"] == 1
    assert summary["evaluation_contract"]["decoding"]["sampled"]["n"] == 16


def test_summary_rejects_same_index_with_changed_scientific_item(tmp_path: Path) -> None:
    row = _row("gray")
    row["problem"] = "A different question with the same row index."
    runs = _runs(tmp_path, {"gray": {"problem": row["problem"]}})

    with pytest.raises(ValueError, match="item contract mismatch"):
        build_summary(runs, dataset_name="fixture", splits=("audit",))


def test_summary_rejects_cross_arm_decoding_drift(tmp_path: Path) -> None:
    decoding = copy.deepcopy(_row("noise")["decoding"])
    decoding["max_tokens"] = 256
    runs = _runs(tmp_path, {"noise": {"decoding": decoding}})

    with pytest.raises(ValueError, match="decoding contract mismatch"):
        build_summary(runs, dataset_name="fixture", splits=("audit",))


def test_summary_recomputes_and_rejects_stale_scores(tmp_path: Path) -> None:
    runs = _runs(tmp_path, {"caption": {"p_sample": 0.75}})

    with pytest.raises(ValueError, match="stored score mismatch"):
        build_summary(runs, dataset_name="fixture", splits=("audit",))


def test_summary_rejects_shared_but_non_greedy_decoding(tmp_path: Path) -> None:
    decoding = copy.deepcopy(_row("real")["decoding"])
    decoding["greedy"]["temperature"] = 0.5
    runs = _runs(tmp_path, {condition: {"decoding": decoding} for condition in CONDITIONS})

    with pytest.raises(ValueError, match="unregistered decoding contract"):
        build_summary(runs, dataset_name="fixture", splits=("audit",))
