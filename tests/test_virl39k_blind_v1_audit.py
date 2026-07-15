from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.summarize_blind_solvability_virl39k_v1 import audit_runs, build_summary
from src.eval.blind_solvability import CONDITIONS, PILOT_ROW_SCHEMA_VERSION, PILOT_SCORING_MODE, score_item_pilot
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT
from src.rewards.answer_reward import PARSER_VERSION
from src.rewards.pilot_reward import (
    DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS,
    PILOT_REWARD_VERSION,
    SYMBOLIC_GRADER_GUARD_VERSION,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(tmp_path: Path) -> tuple[dict[str, Path], Path, Path, Path]:
    image_a = tmp_path / "a.png"
    image_b = tmp_path / "b.png"
    image_a.write_bytes(b"image-a")
    image_b.write_bytes(b"image-b")
    rows = [
        {
            "split": "audit",
            "row_index": 0,
            "qid": "fixture-0",
            "problem": "<image> What is one?",
            "answer": "1",
            "images": [{"path": str(image_a), "sha256": _sha256(image_a)}],
            "metadata": {
                "source": "fixture",
                "category": "math",
                "answer_type": "numeric",
                "image_count_bucket": "1",
            },
        },
        {
            "split": "audit",
            "row_index": 1,
            "qid": "fixture-1",
            "problem": "<image><image> What is two?",
            "answer": "2",
            "images": [
                {"path": str(image_a), "sha256": _sha256(image_a)},
                {"path": str(image_b), "sha256": _sha256(image_b)},
            ],
            "metadata": {
                "source": "fixture",
                "category": "math",
                "answer_type": "numeric",
                "image_count_bucket": "2-3",
            },
        },
    ]
    source = tmp_path / "sample.jsonl"
    source.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    spec = tmp_path / "sample.json"
    spec.write_text(
        json.dumps(
            {
                "sample_size": 2,
                "source_counts": {"fixture": 2},
                "category_counts": {"math": 2},
                "answer_type_counts": {"numeric": 2},
                "image_count_counts": {"1": 1, "2": 1},
                "image_references": 3,
                "unique_images": 2,
                "max_images_per_item": 2,
            }
        ),
        encoding="utf-8",
    )
    prompt = tmp_path / "prompt.jinja"
    prompt.write_text("{{ content }} return <answer>x</answer>", encoding="utf-8")
    caption_run = tmp_path / "caption-store"
    caption_run.mkdir()
    (caption_run / "run_manifest.json").write_text(
        json.dumps({"status": "complete", "max_new_tokens": 384}), encoding="utf-8"
    )

    runs = {}
    decoding = {
        "greedy": {"temperature": 0.0, "top_p": 1.0, "n": 1},
        "sampled": {"temperature": 1.0, "top_p": 1.0, "n": 16},
        "max_tokens": 2048,
        "seed": 20260710,
    }
    for condition in CONDITIONS:
        run = tmp_path / condition
        run.mkdir()
        output_rows = []
        for source_row in rows:
            gold = source_row["answer"]
            correct = f"<answer>{gold}</answer>"
            sampled = [correct] * 8 + ["<answer>wrong</answer>"] * 8
            scored = score_item_pilot(
                gold,
                correct,
                sampled,
                group_size=5,
                prompt_contract=DEFAULT_PROMPT_CONTRACT,
                format_weight=0.5,
            )
            output_rows.append(
                {
                    "schema_version": PILOT_ROW_SCHEMA_VERSION,
                    "split": source_row["split"],
                    "row_index": source_row["row_index"],
                    "qid": source_row["qid"],
                    "problem": source_row["problem"],
                    "ground_truth": gold,
                    "image_sha256": [image["sha256"] for image in source_row["images"]],
                    "condition": condition,
                    "source_metadata": source_row["metadata"],
                    "source_manifest_sha256": _sha256(source),
                    "train_filter_sha256": None,
                    "format_prompt_sha256": _sha256(prompt),
                    "greedy_response": correct,
                    "sampled_responses": sampled,
                    **scored,
                    "decoding": decoding,
                }
            )
        (run / "per_item.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in output_rows), encoding="utf-8"
        )
        manifest = {
            "status": "complete",
            "exit_code": 0,
            "job_type": "l10_virl39k_blind_solvability_v1",
            "condition": condition,
            "data_manifest": str(source),
            "source_manifest_sha256": _sha256(source),
            "sample_spec": str(spec),
            "sample_spec_sha256": _sha256(spec),
            "sample_size": 2,
            "max_images_per_item": 2,
            "format_prompt_sha256": _sha256(prompt),
            "train_filter_ids": None,
            "train_filter_sha256": None,
            "model_revision": "artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct",
            "parser_version": PARSER_VERSION,
            "pilot_reward_version": PILOT_REWARD_VERSION,
            "scoring_mode": PILOT_SCORING_MODE,
            "prompt_contract": DEFAULT_PROMPT_CONTRACT.to_dict(),
            "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
            "group_size": 5,
            "sample_count": 16,
            "sample_temperature": 1,
            "max_tokens": 2048,
            "format_weight": 0.5,
            "symbolic_grader_guard_version": SYMBOLIC_GRADER_GUARD_VERSION,
            "symbolic_grader_timeout_seconds": DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS,
            "seed": 20260710,
            "decoding": decoding,
            "caption_source_run": str(caption_run) if condition == "caption" else None,
        }
        (run / "run_manifest.json").write_text(json.dumps(manifest) + "\n", encoding="utf-8")
        runs[condition] = run
    return runs, source, spec, prompt


def test_virl_audit_recomputes_scores_and_multi_image_contract(tmp_path: Path) -> None:
    runs, source, spec, prompt = _fixture(tmp_path)
    audit, rows = audit_runs(runs, source, spec, prompt)

    assert audit["status"] == "fail"
    assert audit["checks"]["row_count_exact_4096"] is False
    assert all(value for key, value in audit["checks"].items() if key != "row_count_exact_4096")
    assert audit["frozen_sample_statistics"]["image_count_counts"] == {"1": 1, "2": 1}

    audit["status"] = "pass"
    summary = build_summary(rows, audit)
    assert summary["n_items"] == 2
    assert summary["aggregates"]["real"]["by_category"]["math"]["n"] == 2


def test_virl_audit_rejects_condition_with_missing_frozen_row(tmp_path: Path) -> None:
    runs, source, spec, prompt = _fixture(tmp_path)
    gray_output = runs["gray"] / "per_item.jsonl"
    gray_output.write_text(gray_output.read_text(encoding="utf-8").splitlines()[0] + "\n", encoding="utf-8")

    audit, _ = audit_runs(runs, source, spec, prompt)

    assert audit["status"] == "fail"
    assert audit["checks"]["row_identity_equal_to_frozen_sample"] is False
    assert audit["row_counts"]["gray"] == 1


def test_virl_audit_rejects_missing_symbolic_guard_stamp(tmp_path: Path) -> None:
    runs, source, spec, prompt = _fixture(tmp_path)
    manifest_path = runs["noise"] / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.pop("symbolic_grader_timeout_seconds")
    manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")

    audit, _ = audit_runs(runs, source, spec, prompt)

    assert audit["status"] == "fail"
    assert audit["checks"]["symbolic_grader_guard_locked"] is False


def test_virl_audit_binds_exact_7b_job_and_model_identity(tmp_path: Path) -> None:
    runs, source, spec, prompt = _fixture(tmp_path)
    expected_job = "m8_virl39k_7b_blind_solvability_v1"
    expected_model = (
        "Qwen/Qwen2.5-VL-7B-Instruct@cc594898137f460bfe9f0759e9844b3ce807cfb5"
    )
    for run in runs.values():
        manifest_path = run / "run_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["job_type"] = expected_job
        manifest["model_revision"] = expected_model
        manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")

    audit, _ = audit_runs(
        runs,
        source,
        spec,
        prompt,
        expected_job_type=expected_job,
        expected_model_revision=expected_model,
    )

    assert audit["expected_job_type"] == expected_job
    assert audit["expected_model_revision"] == expected_model
    assert all(
        value
        for name, value in audit["checks"].items()
        if name != "row_count_exact_4096"
    )

    gray_manifest = runs["gray"] / "run_manifest.json"
    payload = json.loads(gray_manifest.read_text(encoding="utf-8"))
    payload["model_revision"] = "wrong-model"
    gray_manifest.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    rejected, _ = audit_runs(
        runs,
        source,
        spec,
        prompt,
        expected_job_type=expected_job,
        expected_model_revision=expected_model,
    )
    assert rejected["checks"]["all_run_manifests_complete_and_registered"] is False
