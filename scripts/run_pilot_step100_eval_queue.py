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


ROOT = Path(__file__).resolve().parents[1]
TERMINAL_FAILURES = {"fail", "failed", "error", "cancelled", "canceled"}


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
    path = Path(value)
    resolved = (path if path.is_absolute() else root / path).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as error:
        raise ValueError(f"path escapes repository root: {value}") from error
    return resolved


def _write_state(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.partial")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def validate_config(config: dict[str, Any], root: Path = ROOT) -> None:
    if config.get("schema_version") != "blind-gains.pilot-step100-eval-queue.v1":
        raise ValueError("unsupported queue config schema")
    if config.get("arm") not in {"a1_real", "a2_gray", "a2b_noimage", "a3_caption"}:
        raise ValueError("unsupported pilot arm")
    if config.get("node") not in {"an12", "an29"}:
        raise ValueError("queue may target only permanent nodes an12 or an29")
    gpu_ids = config.get("gpu_ids")
    if (
        not isinstance(gpu_ids, list)
        or len(gpu_ids) != 4
        or len(set(gpu_ids)) != 4
        or any(not isinstance(gpu, int) or not 0 <= gpu <= 7 for gpu in gpu_ids)
    ):
        raise ValueError("queue requires four unique GPU ids in [0, 7]")
    if config.get("global_step") != 100:
        raise ValueError("this queue is pinned to global step 100")
    if config.get("image_mode") != "real" or config.get("max_new_tokens") != 32:
        raise ValueError("pilot FlipTrack queue requires real images and 32 tokens")
    if config.get("num_shards") != 4:
        raise ValueError("pilot queue requires four TP1 shards")
    if config.get("r19_manifest_sha256") != R19_MANIFEST_SHA256:
        raise ValueError("queue config does not pin the registered R19 manifest")
    for field in (
        "training_run",
        "retention_run",
        "checkpoint_path",
        "r19_manifest",
        "marker",
        "evaluation_run",
        "state_path",
    ):
        if not isinstance(config.get(field), str):
            raise ValueError(f"missing path field: {field}")
        _resolve(root, config[field])
    training_run = _resolve(root, config["training_run"])
    marker = _resolve(root, config["marker"])
    expected_marker = training_run / "step100_fliptrack_complete.json"
    if marker != expected_marker:
        raise ValueError("marker is not bound to the pinned training run and step")
    manifest = _resolve(root, config["r19_manifest"])
    if not manifest.is_file() or _sha256(manifest) != R19_MANIFEST_SHA256:
        raise ValueError("registered R19 manifest is absent or hash-mismatched")
    if not isinstance(config.get("aggregate_tag"), str) or not config["aggregate_tag"]:
        raise ValueError("aggregate_tag is required")
    if not str(config["aggregate_tag"]).replace("_", "").replace("-", "").isalnum():
        raise ValueError("aggregate_tag contains unsupported characters")
    if not isinstance(config.get("poll_seconds"), int) or config["poll_seconds"] < 10:
        raise ValueError("poll_seconds must be >= 10")
    if not isinstance(config.get("stable_free_polls"), int) or config["stable_free_polls"] < 2:
        raise ValueError("stable_free_polls must be >= 2")


def inspect_dependencies(config: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    training_run = _resolve(root, config["training_run"])
    retention_run = _resolve(root, config["retention_run"])
    checkpoint = _resolve(root, config["checkpoint_path"])
    training_path = training_run / "run_manifest.json"
    retention_path = retention_run / "run_manifest.json"
    if not training_path.is_file() or not retention_path.is_file():
        return {"status": "failed", "reason": "source_manifest_absent"}
    training = _read_json(training_path)
    retention = _read_json(retention_path)
    training_errors = {
        key: {"expected": value, "observed": training.get(key)}
        for key, value in {
            "job_type": "l13_mechanical_pilot_arm",
            "arm": config["arm"],
            "node": config["node"],
        }.items()
        if training.get(key) != value
    }
    expected_checkpoint = Path(str(training.get("checkpoint_path", ""))) / (
        "global_step_100/actor/huggingface"
    )
    if expected_checkpoint.resolve() != checkpoint.resolve():
        training_errors["checkpoint_path"] = {
            "expected": str(expected_checkpoint.resolve()),
            "observed": str(checkpoint.resolve()),
        }
    if training_errors:
        return {
            "status": "failed",
            "reason": "training_identity_or_completion_mismatch",
            "details": training_errors,
        }
    training_status = training.get("status")
    if training_status in TERMINAL_FAILURES:
        return {"status": "failed", "reason": f"training_terminal_{training_status}"}
    if (
        training_status == "running"
        and training.get("exit_code") is None
        and not training.get("end_time_utc")
    ):
        return {"status": "waiting_training", "reason": "running"}
    if training_status != "complete":
        return {
            "status": "failed",
            "reason": "training_state_inconsistent",
            "details": {
                "status": training_status,
                "exit_code": training.get("exit_code"),
                "end_time_utc": training.get("end_time_utc"),
            },
        }
    if training.get("exit_code") != 0 or training.get("artifacts_exist") is not True:
        return {"status": "failed", "reason": "training_completion_unverified"}

    final_index = checkpoint / "model.safetensors.index.json"
    final_raw = checkpoint.parent / "RAW_STATE_RELOCATED.json"
    common_retention_expected = {
        "parent_training_run": str(training_run.relative_to(root)),
        "compute_node": config["node"],
        "expected_artifacts": [str(final_index), str(final_raw)],
    }
    retention_job_type = retention.get("job_type")
    if retention_job_type == "pilot_checkpoint_retention_recovery":
        retention_expected = {
            "job_type": retention_job_type,
            **common_retention_expected,
        }
        retention_profile = "recovery"
    elif retention_job_type == "pilot_resume60_checkpoint_retention_watch":
        retention_expected = {
            "job_type": retention_job_type,
            **common_retention_expected,
            "run_root": str(Path(str(training["checkpoint_path"])).resolve()),
            "resume_schedule": [80, 100],
        }
        retention_profile = "primary_resume60"
    else:
        return {
            "status": "failed",
            "reason": "unsupported_retention_job_type",
            "details": {"observed": retention_job_type},
        }
    retention_errors = {
        key: {"expected": value, "observed": retention.get(key)}
        for key, value in retention_expected.items()
        if retention.get(key) != value
    }
    if retention_errors:
        return {
            "status": "failed",
            "reason": "retention_identity_mismatch",
            "details": retention_errors,
        }
    retention_status = retention.get("status")
    if retention_status in TERMINAL_FAILURES:
        return {
            "status": "failed",
            "reason": f"retention_terminal_{retention_status}",
        }
    if retention_status != "complete":
        return {"status": "waiting_retention", "reason": retention_status}
    if retention.get("exit_code") != 0 or retention.get("artifacts_exist") is not True:
        return {"status": "failed", "reason": "retention_completion_unverified"}
    if not final_index.is_file() or not final_raw.is_file():
        return {"status": "failed", "reason": "retention_artifact_absent"}
    return {
        "status": "ready",
        "retention_profile": retention_profile,
        "checkpoint_index_sha256": _sha256(final_index),
        "retention_manifest_sha256": _sha256(retention_path),
        "training_manifest_sha256": _sha256(training_path),
    }


def query_gpu_processes(node: str, gpu_ids: list[int]) -> dict[int, list[int]]:
    observed: dict[int, list[int]] = {}
    for gpu in gpu_ids:
        result = subprocess.run(
            [
                "ssh",
                node,
                f"nvidia-smi -i {gpu} --query-compute-apps=pid --format=csv,noheader,nounits",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"GPU capacity query failed for {node}:{gpu}: {result.stderr.strip()}"
            )
        pids = [int(line.strip()) for line in result.stdout.splitlines() if line.strip()]
        observed[gpu] = pids
    return observed


def validate_marker(config: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    marker_path = _resolve(root, config["marker"])
    marker = _read_json(marker_path)
    checkpoint = _resolve(root, config["checkpoint_path"])
    expected = {
        "schema_version": MARKER_SCHEMA_VERSION,
        "status": "complete",
        "global_step": 100,
        "r19_manifest_sha256": R19_MANIFEST_SHA256,
    }
    errors = {
        key: {"expected": value, "observed": marker.get(key)}
        for key, value in expected.items()
        if marker.get(key) != value
    }
    if Path(str(marker.get("checkpoint_path", ""))).resolve() != checkpoint.resolve():
        errors["checkpoint_path"] = {
            "expected": str(checkpoint.resolve()),
            "observed": marker.get("checkpoint_path"),
        }
    checks = marker.get("checks")
    if not isinstance(checks, dict) or not checks or not all(checks.values()):
        errors["checks"] = {"expected": "all true", "observed": checks}
    if errors:
        raise ValueError(f"step-100 marker validation failed: {errors}")
    return marker


def _launch_evaluation(config: dict[str, Any], root: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["BLIND_GAINS_PILOT_SOURCE_RUN"] = config["training_run"]
    environment["BLIND_GAINS_PILOT_GLOBAL_STEP"] = "100"
    gpu_list = " ".join(str(gpu) for gpu in config["gpu_ids"])
    return subprocess.run(
        [
            "bash",
            "scripts/launch_fliptrack_eval_shards.sh",
            config["node"],
            "0",
            "4",
            config["checkpoint_path"],
            config["r19_manifest"],
            config["evaluation_run"],
            "32",
            gpu_list,
            "real",
        ],
        cwd=root,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def _find_finalize_watcher(config: dict[str, Any], root: Path) -> Path | None:
    marker = _resolve(root, config["marker"])
    matches: list[Path] = []
    for manifest_path in (root / "experiments/runs").glob(
        "pilot_step_eval_finalize_watch_*/run_manifest.json"
    ):
        manifest = _read_json(manifest_path)
        artifacts = manifest.get("expected_artifacts")
        if not isinstance(artifacts, list) or len(artifacts) < 2:
            continue
        observed = _resolve(root, str(artifacts[1]))
        if observed == marker:
            matches.append(manifest_path.parent)
    if len(matches) > 1:
        raise ValueError(f"multiple finalization watchers own marker: {matches}")
    return matches[0] if matches else None


def _launch_finalize_watcher(config: dict[str, Any], root: Path) -> Path:
    existing = _find_finalize_watcher(config, root)
    if existing is not None:
        return existing
    result = subprocess.run(
        [
            "bash",
            "scripts/launch_pilot_step_evaluation_watch.sh",
            config["evaluation_run"],
            config["training_run"],
            "100",
            config["marker"],
            config["aggregate_tag"],
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"step evaluation finalizer launch failed ({result.returncode}): "
            f"{result.stderr.strip()}"
        )
    candidates = [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip().startswith("experiments/runs/")
    ]
    if len(candidates) != 1:
        raise RuntimeError(f"ambiguous finalizer launcher output: {result.stdout!r}")
    return root / candidates[0]


def run_queue(
    config_path: Path,
    *,
    root: Path = ROOT,
    once: bool = False,
    capacity_query: Callable[[str, list[int]], dict[int, list[int]]] = query_gpu_processes,
) -> int:
    config = _read_json(config_path)
    validate_config(config, root)
    state_path = _resolve(root, config["state_path"])
    state = _read_json(state_path) if state_path.is_file() else {
        "schema_version": "blind-gains.pilot-step100-eval-queue-state.v1",
        "created_utc": _now(),
        "status": "initialized",
        "poll_count": 0,
        "stable_free_poll_count": 0,
        "events": [],
        "scientific_gate_decision": None,
    }
    try:
        while True:
            state["poll_count"] = int(state.get("poll_count", 0)) + 1
            state["updated_utc"] = _now()
            marker_path = _resolve(root, config["marker"])
            if marker_path.is_file():
                marker = validate_marker(config, root)
                state.update(
                    {
                        "status": "complete",
                        "marker_sha256": _sha256(marker_path),
                        "evaluation_run": marker.get("evaluation_run"),
                    }
                )
                _write_state(state_path, state)
                return 0

            dependency = inspect_dependencies(config, root)
            state["dependency"] = dependency
            if dependency["status"] == "failed":
                raise RuntimeError(f"dependency check failed: {dependency}")

            evaluation_run = _resolve(root, config["evaluation_run"])
            if evaluation_run.is_dir():
                evaluation_manifest = _read_json(evaluation_run / "run_manifest.json")
                if evaluation_manifest.get("status") in TERMINAL_FAILURES:
                    raise RuntimeError("evaluation reached terminal failure")
                watcher = _launch_finalize_watcher(config, root)
                state.update(
                    {
                        "status": "evaluation_running",
                        "evaluation_run": str(evaluation_run.relative_to(root)),
                        "finalization_watcher": str(watcher.relative_to(root)),
                    }
                )
            elif dependency["status"] == "ready":
                occupied = capacity_query(config["node"], list(config["gpu_ids"]))
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
                        result = _launch_evaluation(config, root)
                        if result.returncode == 75:
                            state["stable_free_poll_count"] = 0
                            state["status"] = "capacity_race_retry"
                            state["last_launch_stderr"] = result.stderr.strip()
                        elif result.returncode != 0:
                            raise RuntimeError(
                                f"evaluation launch failed ({result.returncode}): "
                                f"{result.stderr.strip()}"
                            )
                        else:
                            watcher = _launch_finalize_watcher(config, root)
                            state["status"] = "evaluation_running"
                            state["evaluation_run"] = config["evaluation_run"]
                            state["finalization_watcher"] = str(
                                watcher.relative_to(root)
                            )
            else:
                state["stable_free_poll_count"] = 0
                state["status"] = dependency["status"]

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
