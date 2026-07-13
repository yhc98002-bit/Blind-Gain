#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import multiprocessing.util
import os
import socket
import tempfile
from pathlib import Path
from typing import Any


TEMP_ENV_KEYS = ("TMPDIR", "TMP", "TEMP", "RAY_TMPDIR")


def validate_observation(observation: dict[str, Any], expected_root: Path) -> list[str]:
    root = expected_root.resolve()
    errors: list[str] = []
    paths = {
        "driver.tempfile": observation.get("driver", {}).get("tempfile"),
        "driver.multiprocessing": observation.get("driver", {}).get("multiprocessing"),
        "worker.tempfile": observation.get("worker", {}).get("tempfile"),
        "worker.multiprocessing": observation.get("worker", {}).get("multiprocessing"),
        "ray.session_dir": observation.get("ray", {}).get("session_dir"),
    }
    for scope in ("driver", "worker"):
        for key in TEMP_ENV_KEYS:
            paths[f"{scope}.env.{key}"] = observation.get(scope, {}).get("env", {}).get(key)
    for label, value in paths.items():
        if not isinstance(value, str):
            errors.append(f"{label}:missing")
            continue
        try:
            Path(value).resolve().relative_to(root)
        except ValueError:
            errors.append(f"{label}:outside_expected_root:{value}")
    return errors


def _local_observation() -> dict[str, Any]:
    return {
        "hostname": socket.gethostname(),
        "pid": os.getpid(),
        "tempfile": tempfile.gettempdir(),
        "multiprocessing": multiprocessing.util.get_temp_dir(),
        "env": {key: os.environ.get(key) for key in TEMP_ENV_KEYS},
    }


def run_probe(expected_root: Path) -> dict[str, Any]:
    expected_root = expected_root.resolve()
    runtime_tmp = expected_root / "tmp"
    ray_tmp = expected_root / "ray"
    runtime_tmp.mkdir(parents=True, exist_ok=False)
    ray_tmp.mkdir(parents=True, exist_ok=False)
    for key in ("TMPDIR", "TMP", "TEMP"):
        os.environ[key] = str(runtime_tmp)
    os.environ["RAY_TMPDIR"] = str(expected_root)
    tempfile.tempdir = None

    import ray

    ray.init(
        address="local",
        num_cpus=1,
        include_dashboard=False,
        _temp_dir=str(ray_tmp),
        object_store_memory=128 * 1024 * 1024,
        logging_level="ERROR",
    )

    @ray.remote
    def worker_observation() -> dict[str, Any]:
        return _local_observation()

    try:
        worker = ray.get(worker_observation.remote(), timeout=60)
        session_dir = str(ray._private.worker._global_node.get_session_dir_path())
    finally:
        ray.shutdown()
    observation = {
        "schema_version": "blind-gains.ray-tempdir-probe.v1",
        "observed_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expected_root": str(expected_root),
        "driver": _local_observation(),
        "worker": worker,
        "ray": {"session_dir": session_dir},
    }
    errors = validate_observation(observation, expected_root)
    observation["checks"] = {
        "all_driver_worker_and_ray_paths_under_expected_root": not errors,
        "cuda_hidden_for_probe": os.environ.get("CUDA_VISIBLE_DEVICES") == "",
    }
    observation["errors"] = errors
    observation["status"] = "pass" if all(observation["checks"].values()) else "fail"
    return observation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.expected_root.exists():
        raise FileExistsError("temp probe output and expected root must be new")
    payload = run_probe(args.expected_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(payload, sort_keys=True))
    raise SystemExit(0 if payload["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
