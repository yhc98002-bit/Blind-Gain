#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from scripts.finalize_pilot_step_evaluation import R19_MANIFEST_SHA256
from scripts.run_pilot_geo3k_step100_eval import (
    M5_ROW_SCHEMA_VERSION,
    REGISTERED_DECODING,
    load_validated_resume_prefix,
)
from src.eval.blind_solvability import load_geometry_rows
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT


MARKER_SCHEMA_VERSION = "blind-gains.m5-step-eval-marker.v1"
REGISTERED_STEPS = frozenset({150, 200, 300, 400})
GEO3K_MANIFEST = Path("data/geometry3k_caption_images_manifest.jsonl")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _complete_manifest(payload: dict[str, Any]) -> bool:
    return bool(
        payload.get("status") == "complete"
        and payload.get("exit_code", 0) == 0
        and payload.get("artifacts_exist", True)
    )


def _same_path(observed: Any, expected: Path) -> bool:
    return Path(str(observed or "")).resolve() == expected.resolve()


def validate_geo3k_run(
    run: Path,
    *,
    source_run: Path,
    checkpoint_path: Path,
    global_step: int,
) -> dict[str, Any]:
    manifest_path = run / "run_manifest.json"
    output_path = run / "per_item.jsonl"
    manifest = _read_json(manifest_path)
    expected = {
        "job_type": "m5_geo3k_checkpoint_eval",
        "arm": "anchor_real",
        "condition": "real",
        "global_step": global_step,
        "expected_row_count": 601,
        "row_schema_version": M5_ROW_SCHEMA_VERSION,
        "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
        "decoding": REGISTERED_DECODING,
        "performance_values_opened": False,
    }
    mismatches = {
        key: {"expected": value, "observed": manifest.get(key)}
        for key, value in expected.items()
        if manifest.get(key) != value
    }
    if not _complete_manifest(manifest):
        mismatches["run_complete"] = {"expected": True, "observed": False}
    if not _same_path(manifest.get("source_training_run"), source_run):
        mismatches["source_training_run"] = {
            "expected": str(source_run.resolve()),
            "observed": manifest.get("source_training_run"),
        }
    if not _same_path(manifest.get("model_revision"), checkpoint_path):
        mismatches["model_revision"] = {
            "expected": str(checkpoint_path.resolve()),
            "observed": manifest.get("model_revision"),
        }
    checkpoint_index = checkpoint_path / "model.safetensors.index.json"
    if not checkpoint_index.is_file():
        mismatches["checkpoint_index_present"] = {"expected": True, "observed": False}
    elif manifest.get("checkpoint_index_sha256") != _sha256(checkpoint_index):
        mismatches["checkpoint_index_sha256"] = {
            "expected": _sha256(checkpoint_index),
            "observed": manifest.get("checkpoint_index_sha256"),
        }
    source_snapshot = Path(str(manifest.get("source_training_manifest_snapshot", "")))
    if not source_snapshot.is_file():
        mismatches["source_training_manifest_snapshot"] = {
            "expected": "present",
            "observed": str(source_snapshot),
        }
    elif manifest.get("source_training_manifest_sha256") != _sha256(source_snapshot):
        mismatches["source_training_manifest_sha256"] = {
            "expected": _sha256(source_snapshot),
            "observed": manifest.get("source_training_manifest_sha256"),
        }
    if not output_path.is_file():
        mismatches["per_item_output"] = {"expected": "present", "observed": "absent"}
    if mismatches:
        raise ValueError(f"M5 Geometry3K evaluation contract mismatch: {mismatches}")

    source_manifest = Path(str(manifest["data_manifest"]))
    if source_manifest.resolve() != GEO3K_MANIFEST.resolve():
        raise ValueError("M5 Geometry3K evaluation used an unexpected source manifest")
    if manifest.get("source_manifest_sha256") != _sha256(source_manifest):
        raise ValueError("M5 Geometry3K source-manifest hash mismatch")
    rows = load_geometry_rows(source_manifest, splits=("test",), train_filter_ids=None)
    lines = load_validated_resume_prefix(
        output_path,
        rows,
        arm="anchor_real",
        condition="real",
        model_revision=str(checkpoint_path.resolve()),
        checkpoint_index_sha256=str(manifest["checkpoint_index_sha256"]),
        source_manifest_sha256=str(manifest["source_manifest_sha256"]),
        source_training_manifest_sha256=str(manifest["source_training_manifest_sha256"]),
        global_step=global_step,
        row_schema_version=M5_ROW_SCHEMA_VERSION,
    )
    if len(lines) != 601:
        raise ValueError(f"M5 Geometry3K output must contain exactly 601 rows, found {len(lines)}")
    return {
        "run": str(run),
        "manifest_sha256": _sha256(manifest_path),
        "output_sha256": _sha256(output_path),
        "row_count": len(lines),
        "source_training_manifest_sha256": manifest["source_training_manifest_sha256"],
    }


def validate_r19_run(
    evaluation_run: Path,
    aggregate_run: Path,
    *,
    source_run: Path,
    checkpoint_path: Path,
    global_step: int,
    image_mode: str,
) -> dict[str, Any]:
    evaluation_manifest_path = evaluation_run / "run_manifest.json"
    aggregate_manifest_path = aggregate_run / "run_manifest.json"
    aggregate_metrics_path = aggregate_run / "metrics.json"
    evaluation = _read_json(evaluation_manifest_path)
    aggregate = _read_json(aggregate_manifest_path)
    metrics = _read_json(aggregate_metrics_path)
    expected = {
        "job_type": "fliptrack_v02_image_evaluation",
        "global_step": global_step,
        "image_mode": image_mode,
        "max_new_tokens": 32,
        "seed": 0,
        "decoding": {"temperature": 0.0, "top_p": 1.0, "n": 1},
        "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
        "data_manifest_hash": R19_MANIFEST_SHA256,
        "evaluation_scope": "registered M5 long-horizon FlipTrack checkpoint endpoint",
        "performance_values_opened": False,
    }
    mismatches = {
        key: {"expected": value, "observed": evaluation.get(key)}
        for key, value in expected.items()
        if evaluation.get(key) != value
    }
    if not _complete_manifest(evaluation):
        mismatches["evaluation_complete"] = {"expected": True, "observed": False}
    if not _same_path(evaluation.get("source_training_run"), source_run):
        mismatches["source_training_run"] = {
            "expected": str(source_run.resolve()),
            "observed": evaluation.get("source_training_run"),
        }
    if not _same_path(evaluation.get("model_revision"), checkpoint_path):
        mismatches["model_revision"] = {
            "expected": str(checkpoint_path.resolve()),
            "observed": evaluation.get("model_revision"),
        }
    source_snapshot = Path(str(evaluation.get("source_training_manifest_snapshot", "")))
    if not source_snapshot.is_file():
        mismatches["source_training_manifest_snapshot"] = {
            "expected": "present",
            "observed": str(source_snapshot),
        }
    elif evaluation.get("source_training_manifest_sha256") != _sha256(source_snapshot):
        mismatches["source_training_manifest_sha256"] = {
            "expected": _sha256(source_snapshot),
            "observed": evaluation.get("source_training_manifest_sha256"),
        }
    checkpoint_index = checkpoint_path / "model.safetensors.index.json"
    if not checkpoint_index.is_file():
        mismatches["checkpoint_index_present"] = {"expected": True, "observed": False}
    elif evaluation.get("checkpoint_index_sha256") != _sha256(checkpoint_index):
        mismatches["checkpoint_index_sha256"] = {
            "expected": _sha256(checkpoint_index),
            "observed": evaluation.get("checkpoint_index_sha256"),
        }
    if not _complete_manifest(aggregate):
        mismatches["aggregate_complete"] = {"expected": True, "observed": False}
    if not _same_path(aggregate.get("source_run"), evaluation_run):
        mismatches["aggregate_source_run"] = {
            "expected": str(evaluation_run.resolve()),
            "observed": aggregate.get("source_run"),
        }
    if metrics.get("n_pairs") != 1200:
        mismatches["aggregate_pair_count"] = {"expected": 1200, "observed": metrics.get("n_pairs")}
    if mismatches:
        raise ValueError(f"M5 R19 {image_mode} evaluation contract mismatch: {mismatches}")
    return {
        "evaluation_run": str(evaluation_run),
        "evaluation_manifest_sha256": _sha256(evaluation_manifest_path),
        "aggregate_run": str(aggregate_run),
        "aggregate_manifest_sha256": _sha256(aggregate_manifest_path),
        "aggregate_metrics_sha256": _sha256(aggregate_metrics_path),
        "pair_count": 1200,
        "image_mode": image_mode,
    }


def build_marker(
    *,
    geo3k_run: Path,
    r19_evaluation_run: Path,
    r19_aggregate_run: Path,
    source_run: Path,
    checkpoint_path: Path,
    global_step: int,
    gray_evaluation_run: Path | None = None,
    gray_aggregate_run: Path | None = None,
    noise_evaluation_run: Path | None = None,
    noise_aggregate_run: Path | None = None,
) -> dict[str, Any]:
    if global_step not in REGISTERED_STEPS:
        raise ValueError("M5 global step is not a registered endpoint")
    blind_values = (gray_evaluation_run, gray_aggregate_run, noise_evaluation_run, noise_aggregate_run)
    if global_step == 400 and any(value is None for value in blind_values):
        raise ValueError("M5 step 400 requires both gray and noise R19 evaluation/aggregate runs")
    if global_step != 400 and any(value is not None for value in blind_values):
        raise ValueError("M5 gray/noise R19 cells are registered only at step 400")

    geo3k = validate_geo3k_run(
        geo3k_run,
        source_run=source_run,
        checkpoint_path=checkpoint_path,
        global_step=global_step,
    )
    r19 = validate_r19_run(
        r19_evaluation_run,
        r19_aggregate_run,
        source_run=source_run,
        checkpoint_path=checkpoint_path,
        global_step=global_step,
        image_mode="real",
    )
    blind: dict[str, Any] = {}
    if global_step == 400:
        assert gray_evaluation_run is not None and gray_aggregate_run is not None
        assert noise_evaluation_run is not None and noise_aggregate_run is not None
        blind["gray"] = validate_r19_run(
            gray_evaluation_run,
            gray_aggregate_run,
            source_run=source_run,
            checkpoint_path=checkpoint_path,
            global_step=global_step,
            image_mode="gray",
        )
        blind["noise"] = validate_r19_run(
            noise_evaluation_run,
            noise_aggregate_run,
            source_run=source_run,
            checkpoint_path=checkpoint_path,
            global_step=global_step,
            image_mode="noise",
        )
    checkpoint_index = checkpoint_path / "model.safetensors.index.json"
    checks = {
        "global_step_registered": global_step in REGISTERED_STEPS,
        "geo3k_601_rows_exact": geo3k["row_count"] == 601,
        "r19_real_1200_pairs_exact": r19["pair_count"] == 1200,
        "step400_blind_cells_complete": global_step != 400
        or set(blind) == {"gray", "noise"},
        "checkpoint_index_present": checkpoint_index.is_file(),
    }
    return {
        "schema_version": MARKER_SCHEMA_VERSION,
        "status": "complete" if all(checks.values()) else "fail",
        "checks": checks,
        "global_step": global_step,
        "source_training_run": str(source_run),
        "checkpoint_path": str(checkpoint_path.resolve()),
        "checkpoint_index_sha256": _sha256(checkpoint_index),
        "geo3k_status": "complete",
        "r19_status": "complete",
        "r19_gray_status": "complete" if global_step == 400 else "not_registered_at_step",
        "r19_noise_status": "complete" if global_step == 400 else "not_registered_at_step",
        "geo3k": geo3k,
        "r19_real": r19,
        "r19_blind": blind,
        "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
        "performance_values_opened": False,
        "scientific_gate_decision": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--geo3k-run", type=Path, required=True)
    parser.add_argument("--r19-evaluation-run", type=Path, required=True)
    parser.add_argument("--r19-aggregate-run", type=Path, required=True)
    parser.add_argument("--source-run", type=Path, required=True)
    parser.add_argument("--checkpoint-path", type=Path, required=True)
    parser.add_argument("--global-step", type=int, required=True)
    parser.add_argument("--gray-evaluation-run", type=Path)
    parser.add_argument("--gray-aggregate-run", type=Path)
    parser.add_argument("--noise-evaluation-run", type=Path)
    parser.add_argument("--noise-aggregate-run", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite M5 evaluation marker: {args.output}")
    payload = build_marker(
        geo3k_run=args.geo3k_run,
        r19_evaluation_run=args.r19_evaluation_run,
        r19_aggregate_run=args.r19_aggregate_run,
        source_run=args.source_run,
        checkpoint_path=args.checkpoint_path,
        global_step=args.global_step,
        gray_evaluation_run=args.gray_evaluation_run,
        gray_aggregate_run=args.gray_aggregate_run,
        noise_evaluation_run=args.noise_evaluation_run,
        noise_aggregate_run=args.noise_aggregate_run,
    )
    if payload["status"] != "complete":
        raise RuntimeError(json.dumps(payload["checks"], sort_keys=True))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(f".{args.output.name}.partial.{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, args.output)
    print(args.output)


if __name__ == "__main__":
    main()
