#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT


MARKER_SCHEMA_VERSION = "blind-gains.pilot-step-eval-marker.v1"
R19_MANIFEST_SHA256 = "e1dde98451e1c7473906637c029713ab4f95ab4f7c915bd035f697953bf2ffb2"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _complete_manifest(manifest: dict[str, Any]) -> bool:
    return bool(
        manifest.get("status") == "complete"
        and manifest.get("exit_code", 0) == 0
        and manifest.get("artifacts_exist", True)
    )


def build_marker(
    *,
    evaluation_run: Path,
    aggregate_run: Path,
    checkpoint_path: Path,
    global_step: int,
) -> dict[str, Any]:
    evaluation_manifest_path = evaluation_run / "run_manifest.json"
    aggregate_manifest_path = aggregate_run / "run_manifest.json"
    aggregate_metrics_path = aggregate_run / "metrics.json"
    checkpoint_index = checkpoint_path / "model.safetensors.index.json"
    evaluation_manifest = _read_json(evaluation_manifest_path)
    aggregate_manifest = _read_json(aggregate_manifest_path)
    aggregate_metrics = _read_json(aggregate_metrics_path)
    evaluation_model = Path(
        str(evaluation_manifest.get("model_revision") or evaluation_manifest.get("model_path", ""))
    )
    checks = {
        "global_step_is_registered_endpoint": global_step in {60, 100},
        "evaluation_manifest_complete": _complete_manifest(evaluation_manifest),
        "evaluation_job_type_exact": evaluation_manifest.get("job_type")
        in {"fliptrack_v02_image_evaluation", "pilot_fliptrack_checkpoint_eval"},
        "evaluation_checkpoint_exact": evaluation_model.resolve() == checkpoint_path.resolve(),
        "evaluation_global_step_exact": evaluation_manifest.get("global_step") == global_step,
        "evaluation_is_real_image": evaluation_manifest.get("image_mode") == "real",
        "evaluation_decoding_locked": evaluation_manifest.get("decoding")
        == {"temperature": 0.0, "top_p": 1.0, "n": 1},
        "evaluation_max_tokens_locked": evaluation_manifest.get("max_new_tokens") == 32,
        "evaluation_prompt_contract_locked": evaluation_manifest.get("prompt_contract_sha256")
        == DEFAULT_PROMPT_CONTRACT.sha256,
        "evaluation_r19_manifest_locked": evaluation_manifest.get("data_manifest_hash")
        == R19_MANIFEST_SHA256,
        "aggregate_manifest_complete": _complete_manifest(aggregate_manifest),
        "aggregate_source_run_exact": Path(str(aggregate_manifest.get("source_run", ""))).resolve()
        == evaluation_run.resolve(),
        "checkpoint_index_present": checkpoint_index.is_file(),
        "aggregate_metrics_present": aggregate_metrics_path.is_file(),
        "aggregate_covers_1200_pairs": aggregate_metrics.get("n_pairs") == 1200,
    }
    return {
        "schema_version": MARKER_SCHEMA_VERSION,
        "status": "complete" if all(checks.values()) else "fail",
        "checks": checks,
        "global_step": global_step,
        "checkpoint_path": str(checkpoint_path.resolve()),
        "checkpoint_index_sha256": _sha256(checkpoint_index)
        if checkpoint_index.is_file()
        else None,
        "evaluation_run": str(evaluation_run),
        "evaluation_manifest_sha256": _sha256(evaluation_manifest_path),
        "evaluation_output_sha256": _sha256(aggregate_metrics_path)
        if aggregate_metrics_path.is_file()
        else None,
        "aggregate_run": str(aggregate_run),
        "aggregate_manifest_sha256": _sha256(aggregate_manifest_path),
        "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
        "decoding": {"temperature": 0.0, "top_p": 1.0, "n": 1, "max_new_tokens": 32},
        "r19_manifest_sha256": R19_MANIFEST_SHA256,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluation-run", type=Path, required=True)
    parser.add_argument("--aggregate-run", type=Path, required=True)
    parser.add_argument("--checkpoint-path", type=Path, required=True)
    parser.add_argument("--global-step", type=int, choices=(60, 100), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite pilot evaluation marker: {args.output}")
    payload = build_marker(
        evaluation_run=args.evaluation_run,
        aggregate_run=args.aggregate_run,
        checkpoint_path=args.checkpoint_path,
        global_step=args.global_step,
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
