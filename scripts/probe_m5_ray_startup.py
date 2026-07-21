#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import time
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "blind-gains.m5-ray-startup-preflight.v1"


def validate_result(payload: dict[str, Any], *, rounds: int = 2, gpu_count: int = 4) -> list[str]:
    errors: list[str] = []
    observed = payload.get("rounds")
    if not isinstance(observed, list) or len(observed) != rounds:
        return ["round_count"]
    for index, item in enumerate(observed):
        prefix = f"round_{index + 1}"
        if not isinstance(item, dict) or item.get("status") != "pass":
            errors.append(f"{prefix}.status")
            continue
        workers = item.get("gpu_workers")
        if not isinstance(workers, list) or len(workers) != gpu_count:
            errors.append(f"{prefix}.gpu_worker_count")
            continue
        visible = [worker.get("cuda_visible_devices") for worker in workers]
        if any(not isinstance(value, str) or not value for value in visible):
            errors.append(f"{prefix}.cuda_visible_devices_missing")
        elif len(set(visible)) != gpu_count:
            errors.append(f"{prefix}.cuda_visible_devices_not_unique")
        if any(worker.get("cuda_available") is not True for worker in workers):
            errors.append(f"{prefix}.cuda_unavailable")
        if any(worker.get("runtime_env_marker") != "m5-ray-preflight" for worker in workers):
            errors.append(f"{prefix}.runtime_env_missing")
        if item.get("runtime_env_task") != "m5-ray-preflight":
            errors.append(f"{prefix}.runtime_env_task")
    return errors


def _run_round(root: Path, timeout: int) -> dict[str, Any]:
    runtime_tmp = root / "tmp"
    ray_tmp = root / "ray"
    runtime_tmp.mkdir(parents=True, exist_ok=False)
    ray_tmp.mkdir(parents=True, exist_ok=False)
    for key in ("TMPDIR", "TMP", "TEMP"):
        os.environ[key] = str(runtime_tmp)
    os.environ["RAY_TMPDIR"] = str(root)

    import ray

    started = time.monotonic()
    try:
        ray.init(
            address="local",
            num_cpus=8,
            num_gpus=4,
            include_dashboard=False,
            _temp_dir=str(ray_tmp),
            object_store_memory=256 * 1024 * 1024,
            logging_level="ERROR",
        )
    except Exception as error:  # pragma: no cover - live startup failure path
        return {
            "status": "fail",
            "error_type": type(error).__name__,
            "error": str(error),
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }

    @ray.remote(runtime_env={"env_vars": {"BLIND_GAINS_RAY_PREFLIGHT": "m5-ray-preflight"}})
    def runtime_env_task() -> str | None:
        return os.environ.get("BLIND_GAINS_RAY_PREFLIGHT")

    @ray.remote(num_gpus=1, runtime_env={"env_vars": {"BLIND_GAINS_RAY_PREFLIGHT": "m5-ray-preflight"}})
    class GpuProbe:
        def observe(self) -> dict[str, Any]:
            import torch

            available = torch.cuda.is_available()
            allocation_ok = False
            device_name: str | None = None
            if available:
                tensor = torch.ones(256, device="cuda")
                allocation_ok = bool(float(tensor.sum().item()) == 256.0)
                device_name = torch.cuda.get_device_name(0)
            return {
                "pid": os.getpid(),
                "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
                "cuda_available": available and allocation_ok,
                "device_name": device_name,
                "runtime_env_marker": os.environ.get("BLIND_GAINS_RAY_PREFLIGHT"),
            }

    actors: list[Any] = []
    try:
        task_ref = runtime_env_task.remote()
        actors = [GpuProbe.remote() for _ in range(4)]
        worker_refs = [actor.observe.remote() for actor in actors]
        task_value = ray.get(task_ref, timeout=timeout)
        workers = ray.get(worker_refs, timeout=timeout)
        session_dir = str(ray._private.worker._global_node.get_session_dir_path())
        result: dict[str, Any] = {
            "status": "pass",
            "runtime_env_task": task_value,
            "gpu_workers": workers,
            "session_dir": session_dir,
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }
    except Exception as error:  # pragma: no cover - exercised by the live fail-closed probe
        result = {
            "status": "fail",
            "error_type": type(error).__name__,
            "error": str(error),
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }
    finally:
        for actor in actors:
            try:
                ray.kill(actor, no_restart=True)
            except Exception:
                pass
        ray.shutdown()
    return result


def run_probe(root: Path, *, rounds: int, timeout: int) -> dict[str, Any]:
    if root.exists():
        raise FileExistsError(root)
    root.mkdir(parents=True)
    results: list[dict[str, Any]] = []
    for index in range(rounds):
        round_root = root / f"round_{index + 1}"
        results.append(_run_round(round_root, timeout))
        if results[-1]["status"] != "pass":
            break
        time.sleep(2)
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "created_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expected_rounds": rounds,
        "expected_gpu_count": 4,
        "rounds": results,
    }
    errors = validate_result(payload, rounds=rounds, gpu_count=4)
    payload["checks"] = {
        "two_fresh_ray_sessions": len(results) == rounds,
        "runtime_env_agent_responded": not any("runtime_env" in error for error in errors),
        "four_unique_gpu_actors_per_round": not any("gpu_" in error or "cuda_" in error for error in errors),
    }
    payload["errors"] = errors
    payload["status"] = "pass" if not errors and all(payload["checks"].values()) else "fail"
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rounds", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if args.rounds != 2 or args.timeout < 30:
        raise ValueError("M5 preflight requires exactly two rounds and timeout >= 30 seconds")
    payload = run_probe(args.runtime_root, rounds=args.rounds, timeout=args.timeout)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    raise SystemExit(0 if payload["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
