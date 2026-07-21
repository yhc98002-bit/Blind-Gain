#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

from scripts.finalize_pilot_step_evaluation import (
    MARKER_SCHEMA_VERSION,
    R19_MANIFEST_SHA256,
)
from scripts.run_pilot_step100_eval_queue import query_gpu_processes


ROOT = Path(__file__).resolve().parents[1]
ARM_CONDITIONS = {
    "a1_real": "real",
    "a2_gray": "gray",
    "a2b_noimage": "none",
    "a3_caption": "caption",
}
TERMINAL_FAILURES = {"fail", "failed", "error", "cancelled", "canceled"}
SEED1_CONFIG_SCHEMA = "blind-gains.pilot-geo3k-step100-queue.v1"
FOLLOWUP_CONFIG_SCHEMA = "blind-gains.pilot-followup-geo3k-queue.v1"


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve(root: Path, value: str) -> Path:
    candidate = Path(value)
    resolved = (candidate if candidate.is_absolute() else root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as error:
        raise ValueError(f"path escapes repository root: {value}") from error
    return resolved


def _write_state(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.partial")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _is_followup(config: dict[str, Any]) -> bool:
    return config.get("schema_version") == FOLLOWUP_CONFIG_SCHEMA


def validate_config(config: dict[str, Any], root: Path = ROOT) -> None:
    if config.get("schema_version") not in {
        SEED1_CONFIG_SCHEMA,
        FOLLOWUP_CONFIG_SCHEMA,
    }:
        raise ValueError("unsupported Geometry3K queue config schema")
    arm = config.get("arm")
    if arm not in ARM_CONDITIONS:
        raise ValueError("unsupported pilot arm")
    if config.get("condition") != ARM_CONDITIONS[arm]:
        raise ValueError("arm and condition disagree")
    if config.get("node") not in {"an12", "an29"}:
        raise ValueError("queue may target only permanent nodes an12 or an29")
    gpu = config.get("gpu_id")
    if not isinstance(gpu, int) or not 0 <= gpu <= 7:
        raise ValueError("gpu_id must be an integer in [0, 7]")
    global_step = config.get("global_step")
    if _is_followup(config):
        if config.get("seed") not in {2, 3}:
            raise ValueError("follow-up Geometry3K queue seed must be 2 or 3")
        if global_step not in {60, 100}:
            raise ValueError("follow-up Geometry3K endpoint must be step 60 or 100")
    elif global_step != 100:
        raise ValueError("seed-1 Geometry3K queue is pinned to step 100")
    if config.get("expected_row_count") != 601:
        raise ValueError("Geometry3K queue requires the 601-row test split")
    if config.get("caption_run") != "-" and arm != "a3_caption":
        raise ValueError("only A3 may provide a caption store")
    if arm == "a3_caption" and config.get("caption_run") == "-":
        raise ValueError("A3 requires the frozen caption store")
    for field in (
        "training_run",
        "r19_queue_run",
        "r19_marker",
        "checkpoint_path",
        "caption_run",
        "state_path",
    ):
        if not isinstance(config.get(field), str):
            raise ValueError(f"missing path field: {field}")
        if field != "caption_run" or config[field] != "-":
            _resolve(root, config[field])
    training_run = _resolve(root, config["training_run"])
    marker = _resolve(root, config["r19_marker"])
    if marker != training_run / f"step{global_step}_fliptrack_complete.json":
        raise ValueError("R19 marker is not bound to the exact training run")
    training_manifest_path = training_run / "run_manifest.json"
    if not training_manifest_path.is_file():
        raise ValueError("training manifest is absent")
    training = _read_json(training_manifest_path)
    identity = {
        "job_type": (
            "m3_mechanical_pilot_arm"
            if _is_followup(config)
            else "l13_mechanical_pilot_arm"
        ),
        "arm": arm,
        "image_condition": config["condition"],
    }
    if _is_followup(config):
        identity["seed"] = config["seed"]
    else:
        identity["node"] = config["node"]
    mismatches = {
        key: {"expected": value, "observed": training.get(key)}
        for key, value in identity.items()
        if training.get(key) != value
    }
    expected_checkpoint = Path(str(training.get("checkpoint_path", ""))) / (
        f"global_step_{global_step}/actor/huggingface"
    )
    checkpoint = _resolve(root, config["checkpoint_path"])
    if expected_checkpoint.resolve() != checkpoint:
        mismatches["checkpoint_path"] = {
            "expected": str(expected_checkpoint.resolve()),
            "observed": str(checkpoint),
        }
    if mismatches:
        raise ValueError(f"training identity mismatch: {mismatches}")
    if not isinstance(config.get("poll_seconds"), int) or config["poll_seconds"] < 10:
        raise ValueError("poll_seconds must be >= 10")
    if (
        not isinstance(config.get("stable_free_polls"), int)
        or config["stable_free_polls"] < 2
    ):
        raise ValueError("stable_free_polls must be >= 2")


def validate_r19_marker(config: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    marker_path = _resolve(root, config["r19_marker"])
    marker = _read_json(marker_path)
    checkpoint = _resolve(root, config["checkpoint_path"])
    expected = {
        "schema_version": MARKER_SCHEMA_VERSION,
        "status": "complete",
        "global_step": config["global_step"],
        "r19_manifest_sha256": R19_MANIFEST_SHA256,
        "checkpoint_path": str(checkpoint),
    }
    errors = {
        key: {"expected": value, "observed": marker.get(key)}
        for key, value in expected.items()
        if marker.get(key) != value
    }
    checks = marker.get("checks")
    if not isinstance(checks, dict) or not checks or not all(checks.values()):
        errors["checks"] = {"expected": "all true", "observed": checks}
    training = _read_json(_resolve(root, config["training_run"]) / "run_manifest.json")
    completion = {
        "status": "complete",
        "exit_code": 0,
        "artifacts_exist": True,
    }
    for key, value in completion.items():
        if training.get(key) != value:
            errors[f"training_{key}"] = {"expected": value, "observed": training.get(key)}
    if not (checkpoint / "model.safetensors.index.json").is_file():
        errors["checkpoint_index"] = "absent"
    if errors:
        raise ValueError(f"R19 marker validation failed: {errors}")
    return marker


def _parse_run_path(output: str, root: Path) -> Path:
    candidates = [
        line.strip()
        for line in output.splitlines()
        if line.strip().startswith("experiments/runs/")
    ]
    if len(candidates) != 1:
        raise RuntimeError(f"ambiguous child launcher output: {output!r}")
    return _resolve(root, candidates[0])


def launch_evaluation(config: dict[str, Any], root: Path = ROOT) -> Path:
    environment = os.environ.copy()
    if _is_followup(config):
        environment["BLIND_GAINS_PILOT_FOLLOWUP_SEED"] = str(config["seed"])
        environment["BLIND_GAINS_PILOT_GLOBAL_STEP"] = str(config["global_step"])
    result = subprocess.run(
        [
            "bash",
            "scripts/launch_pilot_geo3k_step100_eval.sh",
            config["arm"],
            config["node"],
            str(config["gpu_id"]),
            config["training_run"],
            config["r19_marker"],
            config["checkpoint_path"],
            config["caption_run"],
        ],
        cwd=root,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Geometry3K evaluation launch failed ({result.returncode}): "
            f"{result.stderr.strip()}"
        )
    return _parse_run_path(result.stdout, root)


def launch_audit(evaluation_run: Path, root: Path = ROOT) -> Path:
    result = subprocess.run(
        [
            "bash",
            "scripts/launch_pilot_geo3k_step100_audit.sh",
            str(evaluation_run.relative_to(root)),
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Geometry3K audit launch failed ({result.returncode}): "
            f"{result.stderr.strip()}"
        )
    return _parse_run_path(result.stdout, root)


def _validate_evaluation(config: dict[str, Any], run: Path) -> dict[str, Any]:
    manifest = _read_json(run / "run_manifest.json")
    expected = {
        "job_type": (
            "m3_pilot_geo3k_checkpoint_eval"
            if _is_followup(config)
            else "m2_pilot_geo3k_step100_eval"
        ),
        "arm": config["arm"],
        "condition": config["condition"],
        "node": config["node"],
        "gpu_ids": [config["gpu_id"]],
        "global_step": config["global_step"],
        "expected_row_count": 601,
    }
    errors = {
        key: {"expected": value, "observed": manifest.get(key)}
        for key, value in expected.items()
        if manifest.get(key) != value
    }
    if errors:
        raise ValueError(f"evaluation identity mismatch: {errors}")
    return manifest


def _validate_audit(
    config: dict[str, Any],
    run: Path,
    evaluation_run: Path,
    *,
    root: Path = ROOT,
) -> dict[str, Any]:
    manifest = _read_json(run / "run_manifest.json")
    expected_job_type = (
        "m3_pilot_geo3k_checkpoint_audit"
        if _is_followup(config)
        else "m2_pilot_geo3k_step100_audit"
    )
    if manifest.get("job_type") != expected_job_type:
        raise ValueError("unexpected audit job type")
    evaluation_manifest_path = evaluation_run / "run_manifest.json"
    evaluation_manifest = _read_json(evaluation_manifest_path)
    expected_source_run = str(evaluation_run.relative_to(root))
    if (
        manifest.get("source_evaluation_run") != expected_source_run
        or manifest.get("source_evaluation_manifest_sha256")
        != _sha256(evaluation_manifest_path)
    ):
        raise ValueError("audit is not bound to the queued evaluation run")
    audit_path = run / "audit.json"
    audit = _read_json(audit_path)
    checks = audit.get("checks")
    if (
        manifest.get("status") != "complete"
        or manifest.get("exit_code") != 0
        or manifest.get("artifacts_exist") is not True
        or audit.get("status") != "pass"
        or audit.get("row_count") != 601
        or not isinstance(checks, dict)
        or not checks
        or not all(checks.values())
        or audit.get("static_mismatch_count") != 0
        or audit.get("score_recomputation_mismatch_count") != 0
        or audit.get("strict_identity_mismatch_count") != 0
        or audit.get("run_id") != evaluation_manifest.get("run_id")
        or Path(str(audit.get("run_manifest", ""))).resolve()
        != evaluation_manifest_path.resolve()
        or audit.get("run_manifest_sha256") != _sha256(evaluation_manifest_path)
        or audit.get("performance_values_reported") is not False
    ):
        raise ValueError("Geometry3K audit did not satisfy every structural check")
    return audit


def run_queue(
    config_path: Path,
    *,
    root: Path = ROOT,
    once: bool = False,
    capacity_query: Callable[[str, list[int]], dict[int, list[int]]] = query_gpu_processes,
    evaluation_launcher: Callable[[dict[str, Any], Path], Path] = launch_evaluation,
    audit_launcher: Callable[[Path, Path], Path] = launch_audit,
) -> int:
    config = _read_json(config_path)
    validate_config(config, root)
    state_path = _resolve(root, config["state_path"])
    state = _read_json(state_path) if state_path.is_file() else {
        "schema_version": (
            "blind-gains.pilot-followup-geo3k-queue-state.v1"
            if _is_followup(config)
            else "blind-gains.pilot-geo3k-step100-queue-state.v1"
        ),
        "created_utc": _now(),
        "status": "initialized",
        "poll_count": 0,
        "stable_free_poll_count": 0,
        "scientific_gate_decision": None,
        "performance_values_inspected": False,
    }
    try:
        while True:
            state["poll_count"] = int(state.get("poll_count", 0)) + 1
            state["updated_utc"] = _now()
            audit_value = state.get("audit_run")
            evaluation_value = state.get("evaluation_run")

            if isinstance(audit_value, str):
                audit_run = _resolve(root, audit_value)
                manifest = _read_json(audit_run / "run_manifest.json")
                status = manifest.get("status")
                if status in TERMINAL_FAILURES:
                    raise RuntimeError(f"audit reached terminal failure: {status}")
                if status == "complete":
                    if not isinstance(evaluation_value, str):
                        raise RuntimeError("audit state is missing its evaluation binding")
                    evaluation_run = _resolve(root, evaluation_value)
                    audit = _validate_audit(
                        config, audit_run, evaluation_run, root=root
                    )
                    state.update(
                        {
                            "status": "complete",
                            "audit_sha256": _sha256(audit_run / "audit.json"),
                            "output_sha256": audit["output_sha256"],
                        }
                    )
                    _write_state(state_path, state)
                    return 0
                state["status"] = "audit_running"
            elif isinstance(evaluation_value, str):
                evaluation_run = _resolve(root, evaluation_value)
                manifest = _validate_evaluation(config, evaluation_run)
                status = manifest.get("status")
                if status in TERMINAL_FAILURES:
                    raise RuntimeError(f"evaluation reached terminal failure: {status}")
                if status == "complete":
                    if manifest.get("exit_code") != 0 or manifest.get("artifacts_exist") is not True:
                        raise RuntimeError("evaluation completion is unverified")
                    audit_run = audit_launcher(evaluation_run, root)
                    state["audit_run"] = str(audit_run.relative_to(root))
                    state["status"] = "audit_running"
                else:
                    state["status"] = "evaluation_running"
            else:
                marker_path = _resolve(root, config["r19_marker"])
                if not marker_path.is_file():
                    upstream = _read_json(
                        _resolve(root, config["r19_queue_run"]) / "run_manifest.json"
                    )
                    upstream_status = upstream.get("status")
                    if upstream_status in TERMINAL_FAILURES:
                        raise RuntimeError(f"upstream R19 queue failed: {upstream_status}")
                    if upstream_status == "complete":
                        raise RuntimeError("upstream R19 queue completed without marker")
                    state["stable_free_poll_count"] = 0
                    state["status"] = "waiting_r19_marker"
                else:
                    marker = validate_r19_marker(config, root)
                    state["r19_marker_sha256"] = _sha256(marker_path)
                    state["r19_evaluation_run"] = marker.get("evaluation_run")
                    occupied = capacity_query(config["node"], [config["gpu_id"]])
                    state["observed_gpu_processes"] = {
                        str(gpu): pids for gpu, pids in occupied.items()
                    }
                    if any(occupied.values()):
                        state["stable_free_poll_count"] = 0
                        state["status"] = "waiting_capacity"
                    else:
                        state["stable_free_poll_count"] = int(
                            state.get("stable_free_poll_count", 0)
                        ) + 1
                        state["status"] = "confirming_free_capacity"
                        if state["stable_free_poll_count"] >= config["stable_free_polls"]:
                            evaluation_run = evaluation_launcher(config, root)
                            state["evaluation_run"] = str(
                                evaluation_run.relative_to(root)
                            )
                            state["status"] = "evaluation_running"

            _write_state(state_path, state)
            print(
                json.dumps(
                    {
                        "time_utc": state["updated_utc"],
                        "status": state["status"],
                        "stable_free_polls": state["stable_free_poll_count"],
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            if once:
                return 3
            time.sleep(config["poll_seconds"])
    except Exception as error:
        state.update(
            {
                "status": "failed",
                "updated_utc": _now(),
                "error": f"{type(error).__name__}: {error}",
            }
        )
        _write_state(state_path, state)
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    raise SystemExit(run_queue(args.config, once=args.once))


if __name__ == "__main__":
    main()
