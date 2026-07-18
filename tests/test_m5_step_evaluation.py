from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from scripts import finalize_m5_step_evaluation as finalizer
from scripts.run_pilot_geo3k_step100_eval import M5_ROW_SCHEMA_VERSION, REGISTERED_DECODING
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT


ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def _fixture_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, step: int = 150):
    source_run = tmp_path / "source-run"
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir(parents=True)
    index = checkpoint / "model.safetensors.index.json"
    index.write_text('{"weight_map":{"x":"model.safetensors"}}\n', encoding="utf-8")
    source_snapshot = tmp_path / "source-snapshot.json"
    _write_json(source_snapshot, {"status": "running", "target_global_step": 400})

    geometry_manifest = tmp_path / "geometry.jsonl"
    geometry_rows = [
        {
            "split": "test",
            "row_index": row_index,
            "problem": f"problem-{row_index}",
            "answer": str(row_index),
            "images": [],
        }
        for row_index in range(601)
    ]
    geometry_manifest.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in geometry_rows),
        encoding="utf-8",
    )
    monkeypatch.setattr(finalizer, "GEO3K_MANIFEST", geometry_manifest)

    geo_run = tmp_path / "geo-run"
    geo_manifest = {
        "status": "complete",
        "exit_code": 0,
        "artifacts_exist": True,
        "job_type": "m5_geo3k_checkpoint_eval",
        "arm": "anchor_real",
        "condition": "real",
        "global_step": step,
        "expected_row_count": 601,
        "row_schema_version": M5_ROW_SCHEMA_VERSION,
        "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
        "decoding": REGISTERED_DECODING,
        "performance_values_opened": False,
        "source_training_run": str(source_run),
        "model_revision": str(checkpoint),
        "checkpoint_index_sha256": _sha256(index),
        "source_training_manifest_snapshot": str(source_snapshot),
        "source_training_manifest_sha256": _sha256(source_snapshot),
        "data_manifest": str(geometry_manifest),
        "source_manifest_sha256": _sha256(geometry_manifest),
    }
    _write_json(geo_run / "run_manifest.json", geo_manifest)
    output_rows = []
    for source in geometry_rows:
        output_rows.append(
            {
                "schema_version": M5_ROW_SCHEMA_VERSION,
                "arm": "anchor_real",
                "global_step": step,
                "split": "test",
                "row_index": source["row_index"],
                "problem": source["problem"],
                "ground_truth": source["answer"],
                "image_sha256": [],
                "condition": "real",
                "model_revision": str(checkpoint),
                "checkpoint_index_sha256": _sha256(index),
                "source_manifest_sha256": _sha256(geometry_manifest),
                "source_training_manifest_sha256": _sha256(source_snapshot),
                "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
                "decoding": REGISTERED_DECODING,
                "greedy_response": f"<answer>{source['answer']}</answer>",
                "training_reward": 1.0,
                "acc_final": True,
                "acc_strict": True,
                "extractor_valid": True,
                "contract_valid": True,
                "canonical_eval_reward": 1.0,
                "native_r1v_shadow_reward": 1.0,
                "reward_disagreement_reason": "none",
            }
        )
    (geo_run / "per_item.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in output_rows),
        encoding="utf-8",
    )

    def r19(mode: str):
        evaluation = tmp_path / f"r19-{mode}"
        aggregate = tmp_path / f"aggregate-{mode}"
        _write_json(
            evaluation / "run_manifest.json",
            {
                "status": "complete",
                "exit_code": 0,
                "artifacts_exist": True,
                "job_type": "fliptrack_v02_image_evaluation",
                "global_step": step,
                "image_mode": mode,
                "max_new_tokens": 32,
                "seed": 0,
                "decoding": {"temperature": 0.0, "top_p": 1.0, "n": 1},
                "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
                "data_manifest_hash": finalizer.R19_MANIFEST_SHA256,
                "evaluation_scope": "registered M5 long-horizon FlipTrack checkpoint endpoint",
                "performance_values_opened": False,
                "source_training_run": str(source_run),
                "source_training_manifest_snapshot": str(source_snapshot),
                "source_training_manifest_sha256": _sha256(source_snapshot),
                "model_revision": str(checkpoint),
                "checkpoint_index_sha256": _sha256(index),
            },
        )
        _write_json(
            aggregate / "run_manifest.json",
            {
                "status": "complete",
                "exit_code": 0,
                "artifacts_exist": True,
                "source_run": str(evaluation),
            },
        )
        _write_json(aggregate / "metrics.json", {"n_pairs": 1200})
        return evaluation, aggregate

    return source_run, checkpoint, geo_run, r19


def test_m5_step150_marker_requires_exact_geo_and_r19_coverage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, checkpoint, geo, r19_factory = _fixture_tree(tmp_path, monkeypatch)
    r19, aggregate = r19_factory("real")

    marker = finalizer.build_marker(
        geo3k_run=geo,
        r19_evaluation_run=r19,
        r19_aggregate_run=aggregate,
        source_run=source,
        checkpoint_path=checkpoint,
        global_step=150,
    )

    assert marker["status"] == "complete"
    assert marker["geo3k"]["row_count"] == 601
    assert marker["r19_real"]["pair_count"] == 1200
    assert marker["performance_values_opened"] is False


def test_m5_marker_rejects_checkpoint_substitution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, checkpoint, geo, r19_factory = _fixture_tree(tmp_path, monkeypatch)
    r19, aggregate = r19_factory("real")
    wrong = tmp_path / "wrong-checkpoint"
    wrong.mkdir()
    (wrong / "model.safetensors.index.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="model_revision|checkpoint_index"):
        finalizer.build_marker(
            geo3k_run=geo,
            r19_evaluation_run=r19,
            r19_aggregate_run=aggregate,
            source_run=source,
            checkpoint_path=wrong,
            global_step=150,
        )


def test_m5_step400_fails_closed_without_blind_floor_cells(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, checkpoint, geo, r19_factory = _fixture_tree(tmp_path, monkeypatch, step=400)
    r19, aggregate = r19_factory("real")

    with pytest.raises(ValueError, match="gray and noise"):
        finalizer.build_marker(
            geo3k_run=geo,
            r19_evaluation_run=r19,
            r19_aggregate_run=aggregate,
            source_run=source,
            checkpoint_path=checkpoint,
            global_step=400,
        )


def test_m5_step400_accepts_exact_gray_and_noise_cells(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, checkpoint, geo, r19_factory = _fixture_tree(tmp_path, monkeypatch, step=400)
    real, real_aggregate = r19_factory("real")
    gray, gray_aggregate = r19_factory("gray")
    noise, noise_aggregate = r19_factory("noise")

    marker = finalizer.build_marker(
        geo3k_run=geo,
        r19_evaluation_run=real,
        r19_aggregate_run=real_aggregate,
        source_run=source,
        checkpoint_path=checkpoint,
        global_step=400,
        gray_evaluation_run=gray,
        gray_aggregate_run=gray_aggregate,
        noise_evaluation_run=noise,
        noise_aggregate_run=noise_aggregate,
    )

    assert marker["checks"]["step400_blind_cells_complete"] is True
    assert set(marker["r19_blind"]) == {"gray", "noise"}


def test_m5_evaluation_shell_launchers_parse_and_bind_registered_contract() -> None:
    for name in (
        "launch_m5_geo3k_checkpoint_eval.sh",
        "launch_m5_fliptrack_checkpoint_eval.sh",
        "launch_m5_step_evaluation_watch.sh",
    ):
        subprocess.run(["bash", "-n", str(ROOT / "scripts" / name)], check=True)
    fliptrack = (ROOT / "scripts/launch_fliptrack_eval_shards.sh").read_text(encoding="utf-8")
    geo = (ROOT / "scripts/launch_m5_geo3k_checkpoint_eval.sh").read_text(encoding="utf-8")
    watcher = (ROOT / "scripts/launch_m5_step_evaluation_watch.sh").read_text(encoding="utf-8")
    assert "BLIND_GAINS_M5_SOURCE_RUN" in fliptrack
    assert "M5 step 400 permits real, gray, or noise" in fliptrack
    assert "M5 descriptive checkpoints require real-image" in fliptrack
    assert "--global-step ${GLOBAL_STEP}" in geo
    assert "expected_row_count:601" in geo
    assert "performance_values_opened:false" in geo
    assert "finalize_m5_step_evaluation.py" in (
        ROOT / "scripts/watch_m5_step_evaluation.py"
    ).read_text(encoding="utf-8")
    assert "performance_values_opened:false" in watcher
