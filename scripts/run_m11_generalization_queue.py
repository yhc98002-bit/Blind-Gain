#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BACKENDS = ("internvl3", "gemma3")
DATASETS = ("r19", "r20")
CONDITIONS = ("real", "none", "caption")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def expand_cells(config: dict[str, Any], phase: str) -> list[dict[str, Any]]:
    models = config["models"]
    conditions = tuple(config["conditions"])
    if set(models) != set(BACKENDS) or conditions != CONDITIONS:
        raise ValueError("M11 queue model/condition registry drift")
    cells = []
    if phase == "smoke":
        for backend in BACKENDS:
            for condition in CONDITIONS:
                cells.append(
                    {
                        "id": f"smoke_{backend}_r19_{condition}",
                        "kind": "fliptrack",
                        "backend": backend,
                        "dataset": "r19",
                        "condition": condition,
                        "limit": int(config["smoke_limit"]),
                    }
                )
        return cells
    if phase != "full":
        raise ValueError(f"unknown M11 queue phase: {phase}")
    for backend in BACKENDS:
        for dataset in DATASETS:
            for condition in CONDITIONS:
                cells.append(
                    {
                        "id": f"flip_{backend}_{dataset}_{condition}",
                        "kind": "fliptrack",
                        "backend": backend,
                        "dataset": dataset,
                        "condition": condition,
                        "limit": None,
                    }
                )
        for condition in CONDITIONS:
            cells.append(
                {
                    "id": f"blind_{backend}_virl4096_{condition}",
                    "kind": "blind",
                    "backend": backend,
                    "condition": condition,
                    "limit": None,
                }
            )
    return cells


def initial_state(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "blind-gains.m11-queue-state.v1",
        "status": "waiting_capacity",
        "created_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_utc": None,
        "gpu_free_streaks": {str(index): 0 for index in range(8)},
        "cells": {
            cell["id"]: {**cell, "status": "pending", "gpu": None, "run_dir": None}
            for phase in ("smoke", "full")
            for cell in expand_cells(config, phase)
        },
        "events": [],
    }


def _record(state: dict[str, Any], event: str, **fields: Any) -> None:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    state["updated_utc"] = now
    state["events"].append({"time_utc": now, "event": event, **fields})


def free_gpus(config: dict[str, Any], reserved: set[int]) -> list[int]:
    command = [
        "ssh",
        str(config["node"]),
        "nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader,nounits",
    ]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        return []
    free = []
    for line in result.stdout.splitlines():
        try:
            index, memory, utilization = [int(value.strip()) for value in line.split(",")]
        except ValueError:
            continue
        if (
            index not in reserved
            and memory <= int(config["gpu_free_memory_mib_ceiling"])
            and utilization <= int(config["gpu_free_utilization_ceiling"])
        ):
            free.append(index)
    return free


def update_free_gpu_streaks(
    config: dict[str, Any], state: dict[str, Any], observed_free: list[int]
) -> list[int]:
    required_polls = int(config["gpu_free_stability_polls"])
    if required_polls < 1:
        raise ValueError("gpu_free_stability_polls must be positive")
    observed = set(observed_free)
    streaks = state.setdefault(
        "gpu_free_streaks", {str(index): 0 for index in range(8)}
    )
    stable = []
    for index in range(8):
        key = str(index)
        streaks[key] = int(streaks.get(key, 0)) + 1 if index in observed else 0
        if index in observed and streaks[key] >= required_polls:
            stable.append(index)
    return stable


def launch_cell(config: dict[str, Any], cell: dict[str, Any], gpu: int) -> Path:
    backend = cell["backend"]
    model = config["models"][backend]["path"]
    node = config["node"]
    limit = str(cell["limit"]) if cell["limit"] is not None else "-"
    if cell["kind"] == "fliptrack":
        dataset = cell["dataset"]
        manifest = config["fliptrack"][dataset]
        caption = manifest if cell["condition"] == "caption" else "-"
        command = [
            "scripts/launch_nonqwen_fliptrack_eval.sh",
            node,
            str(gpu),
            backend,
            model,
            dataset,
            manifest,
            cell["condition"],
            caption,
            cell["id"],
            "384",
            limit,
        ]
    else:
        command = [
            "scripts/launch_nonqwen_blind_sample.sh",
            node,
            str(gpu),
            backend,
            model,
            cell["condition"],
            cell["id"],
            "1",
            "0",
            limit,
        ]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"M11 launch failed for {cell['id']}: stdout={result.stdout!r}, stderr={result.stderr!r}"
        )
    run_dir = Path(result.stdout.strip().splitlines()[-1])
    if not (ROOT / run_dir / "run_manifest.json").is_file():
        raise RuntimeError(f"M11 launcher returned no run manifest: {run_dir}")
    return run_dir


def refresh_cells(state: dict[str, Any]) -> None:
    for cell in state["cells"].values():
        if cell["status"] != "running":
            continue
        manifest_path = ROOT / cell["run_dir"] / "run_manifest.json"
        manifest = _load(manifest_path)
        status = str(manifest.get("status"))
        if status == "running":
            continue
        if status != "complete":
            cell["status"] = "fail"
            _record(state, "cell_failed", cell=cell["id"], run_dir=cell["run_dir"])
            continue
        metrics_path = ROOT / cell["run_dir"] / "metrics.json"
        if not metrics_path.is_file() or metrics_path.stat().st_size == 0:
            cell["status"] = "fail"
            _record(state, "cell_missing_metrics", cell=cell["id"], run_dir=cell["run_dir"])
            continue
        metrics = _load(metrics_path)
        if cell["id"].startswith("smoke_") and metrics.get("row_count") != 1:
            cell["status"] = "fail"
            _record(state, "smoke_row_count_failed", cell=cell["id"])
            continue
        cell["status"] = "complete"
        cell["metrics"] = str(metrics_path.relative_to(ROOT))
        _record(state, "cell_completed", cell=cell["id"], run_dir=cell["run_dir"])


def run_phase(config: dict[str, Any], state: dict[str, Any], state_path: Path, phase: str) -> None:
    prefix = "smoke_" if phase == "smoke" else ("flip_", "blind_")
    while True:
        refresh_cells(state)
        selected = [
            cell
            for key, cell in state["cells"].items()
            if (key.startswith(prefix) if isinstance(prefix, str) else key.startswith(prefix))
        ]
        if any(cell["status"] == "fail" for cell in selected):
            _atomic_json(state_path, state)
            raise RuntimeError(f"M11 {phase} phase failed; full launch remains closed")
        if all(cell["status"] == "complete" for cell in selected):
            _record(state, f"{phase}_phase_complete")
            _atomic_json(state_path, state)
            return
        reserved = {
            int(cell["gpu"])
            for cell in state["cells"].values()
            if cell["status"] == "running" and cell["gpu"] is not None
        }
        observed_free = free_gpus(config, reserved)
        available = update_free_gpu_streaks(config, state, observed_free)
        pending = [cell for cell in selected if cell["status"] == "pending"]
        for cell, gpu in zip(pending, available):
            run_dir = launch_cell(config, cell, gpu)
            cell["status"] = "running"
            cell["gpu"] = gpu
            cell["run_dir"] = str(run_dir)
            state["gpu_free_streaks"][str(gpu)] = 0
            _record(state, "cell_launched", cell=cell["id"], gpu=gpu, run_dir=str(run_dir))
            _atomic_json(state_path, state)
        time.sleep(int(config["poll_seconds"]))


def build_report(config: dict[str, Any], state: dict[str, Any]) -> None:
    full = [
        cell
        for key, cell in state["cells"].items()
        if key.startswith(("flip_", "blind_"))
    ]
    flip_metrics = [cell["metrics"] for cell in full if cell["kind"] == "fliptrack"]
    blind_metrics = [cell["metrics"] for cell in full if cell["kind"] == "blind"]
    stage_manifests = [config["models"][backend]["stage_manifest"] for backend in BACKENDS]
    command = [
        str(ROOT / ".venv/bin/python"),
        "scripts/build_generalization_audits.py",
        "--fliptrack-metrics",
        *flip_metrics,
        "--blind-metrics",
        *blind_metrics,
        "--model-stage-manifests",
        *stage_manifests,
        "--machine-output",
        config["outputs"]["machine"],
        "--markdown-output",
        config["outputs"]["markdown"],
    ]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"M11 report builder failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    config = _load(args.config)
    if config.get("schema_version") != "blind-gains.m11-queue-config.v1":
        raise ValueError("unsupported M11 queue config")
    state_path = args.run_dir / "queue_state.json"
    state = _load(state_path) if state_path.exists() else initial_state(config)
    if not state_path.exists():
        _record(state, "queue_initialized")
        _atomic_json(state_path, state)

    state["status"] = "smoke"
    _record(
        state,
        "smoke_phase_opened",
        free_gpu_stability_polls=int(config["gpu_free_stability_polls"]),
    )
    _atomic_json(state_path, state)
    run_phase(config, state, state_path, "smoke")
    state["status"] = "full"
    _record(state, "full_phase_opened")
    _atomic_json(state_path, state)
    run_phase(config, state, state_path, "full")
    build_report(config, state)
    state["status"] = "complete"
    _record(state, "report_complete", outputs=config["outputs"])
    _atomic_json(state_path, state)


if __name__ == "__main__":
    main()
