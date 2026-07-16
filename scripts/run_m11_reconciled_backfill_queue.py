#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from scripts.run_m11_generalization_queue import (
    ROOT,
    _atomic_json,
    _load,
    _now_utc,
    _record,
    expand_cells,
    free_gpus,
    launch_cell,
    record_capacity_poll,
    update_free_gpu_streaks,
)


SCHEMA_VERSION = "blind-gains.m11-reconciled-backfill-config.v1"
STATE_SCHEMA_VERSION = "blind-gains.m11-reconciled-backfill-state.v1"


def _registered_run_dir(value: str, root: Path = ROOT) -> Path:
    path = (root / value).resolve()
    runs = (root / "experiments/runs").resolve()
    if path.parent != runs:
        raise ValueError(f"reconciled run must be an immutable run directory: {value}")
    return path


def _expected_identity(cell: dict[str, Any]) -> tuple[str, str, str | None, str]:
    job_type = (
        "m11_nonqwen_fliptrack_evaluation"
        if cell["kind"] == "fliptrack"
        else "m11_nonqwen_blind_sample_evaluation"
    )
    return (
        str(cell["backend"]),
        str(cell["condition"]),
        str(cell.get("dataset")) if cell.get("dataset") is not None else None,
        job_type,
    )


def _metrics_path(
    run_dir: Path, manifest: dict[str, Any], root: Path = ROOT
) -> Path:
    path = run_dir / "metrics.json"
    registered = {
        (root / str(value)).resolve() for value in manifest.get("expected_artifacts", [])
    }
    if path.resolve() not in registered:
        raise ValueError(f"metrics are not registered by {run_dir}")
    return path


def validate_reconciled_run(
    cell: dict[str, Any], run_dir_value: str, root: Path = ROOT
) -> dict[str, Any]:
    run_dir = _registered_run_dir(run_dir_value, root)
    manifest_path = run_dir / "run_manifest.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise ValueError(f"reconciled run manifest is absent or symbolic: {run_dir_value}")
    manifest = _load(manifest_path)
    observed = (
        manifest.get("model_backend"),
        manifest.get("condition"),
        manifest.get("dataset_id"),
        manifest.get("job_type"),
    )
    if observed != _expected_identity(cell):
        raise ValueError(
            f"reconciled run identity mismatch for {cell['id']}: "
            f"expected={_expected_identity(cell)}, observed={observed}"
        )
    status = str(manifest.get("status"))
    if status not in {"running", "complete"}:
        raise ValueError(f"reconciled run is not viable for {cell['id']}: {status}")
    gpu_ids = manifest.get("gpu_ids")
    if not isinstance(gpu_ids, list) or len(gpu_ids) != 1:
        raise ValueError(f"reconciled run must record one GPU for {cell['id']}")
    record = {
        **cell,
        "status": status,
        "node": str(manifest.get("node")),
        "gpu": int(gpu_ids[0]),
        "run_dir": str(run_dir.relative_to(root)),
    }
    if status == "complete":
        if manifest.get("exit_code") != 0:
            raise ValueError(f"completed reconciled run has nonzero exit for {cell['id']}")
        metrics = _metrics_path(run_dir, manifest, root)
        if not metrics.is_file() or metrics.stat().st_size == 0:
            raise ValueError(f"completed reconciled run lacks metrics for {cell['id']}")
        record["metrics"] = str(metrics.relative_to(root))
    return record


def initial_state(config: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    expected = {cell["id"]: cell for cell in expand_cells(config, "full")}
    existing = config.get("reconciled_runs")
    if not isinstance(existing, dict) or not existing:
        raise ValueError("reconciled_runs must be a nonempty object")
    unknown = sorted(set(existing) - set(expected))
    if unknown:
        raise ValueError(f"unknown reconciled cells: {unknown}")

    cells: dict[str, dict[str, Any]] = {}
    for cell_id, cell in expected.items():
        if cell_id in existing:
            cells[cell_id] = validate_reconciled_run(cell, str(existing[cell_id]), root)
        else:
            cells[cell_id] = {
                **cell,
                "status": "pending",
                "node": None,
                "gpu": None,
                "run_dir": None,
            }
    non_gemma_pending = sorted(
        cell_id
        for cell_id, cell in cells.items()
        if cell["status"] == "pending" and cell["backend"] != "gemma3"
    )
    if non_gemma_pending:
        raise ValueError(f"backfill config omits non-Gemma cells: {non_gemma_pending}")
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "status": "waiting_capacity",
        "created_utc": _now_utc(),
        "updated_utc": None,
        "capacity_poll_count": 0,
        "last_capacity_poll_utc": None,
        "last_observed_free_gpus": [],
        "last_stable_free_gpus": [],
        "gpu_free_streaks": {str(index): 0 for index in range(8)},
        "performance_values_opened": False,
        "cells": cells,
        "events": [],
    }


def refresh_cells(state: dict[str, Any], root: Path = ROOT) -> None:
    for cell in state["cells"].values():
        if cell["status"] != "running":
            continue
        run_dir = root / str(cell["run_dir"])
        manifest = _load(run_dir / "run_manifest.json")
        status = str(manifest.get("status"))
        if status == "running":
            continue
        if status != "complete" or manifest.get("exit_code") != 0:
            cell["status"] = "fail"
            _record(state, "cell_failed", cell=cell["id"], run_dir=cell["run_dir"])
            continue
        metrics = _metrics_path(run_dir, manifest)
        if not metrics.is_file() or metrics.stat().st_size == 0:
            cell["status"] = "fail"
            _record(state, "cell_missing_metrics", cell=cell["id"])
            continue
        cell["status"] = "complete"
        cell["metrics"] = str(metrics.relative_to(root))
        _record(state, "cell_completed", cell=cell["id"], run_dir=cell["run_dir"])


def target_running_gpus(state: dict[str, Any], node: str) -> set[int]:
    return {
        int(cell["gpu"])
        for cell in state["cells"].values()
        if cell["status"] == "running"
        and cell.get("node") == node
        and cell.get("gpu") is not None
    }


def run_queue(config: dict[str, Any], state: dict[str, Any], state_path: Path) -> None:
    node = str(config["node"])
    allowed = {int(value) for value in config["allowed_gpu_ids"]}
    while True:
        refresh_cells(state)
        cells = list(state["cells"].values())
        if any(cell["status"] == "fail" for cell in cells):
            state["status"] = "fail"
            _atomic_json(state_path, state)
            raise RuntimeError("M11 reconciled backfill has a failed cell")
        if all(cell["status"] == "complete" for cell in cells):
            state["status"] = "cells_complete_pending_report"
            _record(state, "all_cells_complete")
            _atomic_json(state_path, state)
            return

        state["status"] = "running"
        reserved = target_running_gpus(state, node)
        observed = [gpu for gpu in free_gpus(config, reserved) if gpu in allowed]
        stable = update_free_gpu_streaks(config, state, observed)
        record_capacity_poll(state, observed, stable)
        _atomic_json(state_path, state)
        running_target = sum(
            cell["status"] == "running" and cell.get("node") == node
            for cell in cells
        )
        slots = max(0, int(config["max_concurrent_jobs_on_node"]) - running_target)
        pending = [cell for cell in cells if cell["status"] == "pending"]
        for cell, gpu in zip(pending[:slots], stable):
            run_dir = launch_cell(config, cell, gpu)
            cell.update(
                status="running",
                node=node,
                gpu=gpu,
                run_dir=str(run_dir),
            )
            state["gpu_free_streaks"][str(gpu)] = 0
            _record(state, "cell_launched", cell=cell["id"], gpu=gpu, run_dir=str(run_dir))
            _atomic_json(state_path, state)
        time.sleep(int(config["poll_seconds"]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    config = _load(args.config)
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported M11 reconciled backfill config")
    state = initial_state(config)
    if args.preflight_only:
        print(
            json.dumps(
                {
                    "status": "pass",
                    "reconciled": sum(
                        cell["status"] != "pending" for cell in state["cells"].values()
                    ),
                    "pending": sum(
                        cell["status"] == "pending" for cell in state["cells"].values()
                    ),
                    "performance_values_opened": False,
                },
                sort_keys=True,
            )
        )
        return
    if args.run_dir is None:
        raise ValueError("--run-dir is required outside preflight mode")
    state_path = args.run_dir / "queue_state.json"
    if state_path.exists():
        state = _load(state_path)
        if state.get("schema_version") != STATE_SCHEMA_VERSION:
            raise ValueError("unsupported M11 reconciled backfill state")
    else:
        _record(state, "reconciled_queue_initialized")
        _atomic_json(state_path, state)
    run_queue(config, state, state_path)


if __name__ == "__main__":
    main()
