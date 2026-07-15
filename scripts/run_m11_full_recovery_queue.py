#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from scripts.run_m11_generalization_queue import (
    BACKENDS,
    CONDITIONS,
    ROOT,
    _atomic_json,
    _load,
    _now_utc,
    _record,
    build_report,
    expand_cells,
    free_gpus,
    launch_cell,
    record_capacity_poll,
    refresh_cells,
    update_free_gpu_streaks,
)
from src.eval.nonqwen_adapters import nonqwen_runtime_metadata_valid
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT
from src.rewards.answer_reward import PARSER_VERSION


EXPECTED_SMOKE_CELLS = {
    f"smoke_{backend}_r19_{condition}"
    for backend in BACKENDS
    for condition in CONDITIONS
}
EXPECTED_M2_ARMS = {"a1_real", "a2_gray", "a2b_noimage", "a3_caption"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _registered_path(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    if root.resolve() != path and root.resolve() not in path.parents:
        raise ValueError(f"registered path escapes repository: {value}")
    return path


def validate_smoke_evidence(
    config: dict[str, Any], root: Path = ROOT
) -> list[dict[str, Any]]:
    records = config.get("smoke_evidence")
    if not isinstance(records, list) or len(records) != 6:
        raise ValueError("full-only M11 recovery requires exactly six smoke records")
    observed_ids = {str(record.get("cell_id")) for record in records}
    if observed_ids != EXPECTED_SMOKE_CELLS:
        raise ValueError(
            f"smoke matrix mismatch: missing={sorted(EXPECTED_SMOKE_CELLS - observed_ids)}, "
            f"extra={sorted(observed_ids - EXPECTED_SMOKE_CELLS)}"
        )

    audit: list[dict[str, Any]] = []
    for record in records:
        backend = str(record["backend"])
        condition = str(record["condition"])
        expected_id = f"smoke_{backend}_r19_{condition}"
        paths = {
            name: _registered_path(root, str(record[name]))
            for name in ("run_manifest", "metrics", "predictions")
        }
        expected_hashes = {
            name: str(record[f"{name}_sha256"])
            for name in ("run_manifest", "metrics", "predictions")
        }
        if any(not path.is_file() or path.is_symlink() for path in paths.values()):
            raise ValueError(f"smoke evidence file missing or symbolic: {expected_id}")
        observed_hashes = {name: _sha256(path) for name, path in paths.items()}
        if observed_hashes != expected_hashes:
            raise ValueError(
                f"smoke evidence hash mismatch for {expected_id}: "
                f"expected={expected_hashes}, observed={observed_hashes}"
            )
        manifest = _load(paths["run_manifest"])
        metrics = _load(paths["metrics"])
        prediction_rows = [
            json.loads(line)
            for line in paths["predictions"].read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        registered_outputs = {
            _registered_path(root, str(path))
            for path in manifest.get("expected_artifacts", [])
        }
        checks = {
            "cell_id_exact": record["cell_id"] == expected_id,
            "run_directory_coherent": len({path.parent for path in paths.values()}) == 1,
            "manifest_complete": manifest.get("status") == "complete"
            and manifest.get("exit_code") == 0,
            "job_type_exact": manifest.get("job_type")
            == "m11_nonqwen_fliptrack_evaluation",
            "identity_exact": (
                manifest.get("model_backend"),
                manifest.get("dataset_id"),
                manifest.get("condition"),
            )
            == (backend, "r19", condition),
            "one_row_limit": manifest.get("limit") == 1
            and metrics.get("row_count") == 1
            and len(prediction_rows) == 1,
            "locked_decoding": manifest.get("max_new_tokens") == 384
            and manifest.get("decoding")
            == {"temperature": 0.0, "top_p": 1.0, "n": 1},
            "locked_scoring": metrics.get("parser_version") == PARSER_VERSION
            and metrics.get("prompt_contract_sha256")
            == DEFAULT_PROMPT_CONTRACT.sha256,
            "runtime_valid": nonqwen_runtime_metadata_valid(
                metrics.get("runtime"), backend
            ),
            "outputs_registered": paths["metrics"] in registered_outputs
            and paths["predictions"] in registered_outputs,
        }
        if not all(checks.values()):
            raise ValueError(f"invalid smoke evidence {expected_id}: {checks}")
        audit.append(
            {
                "cell_id": expected_id,
                "run_manifest": str(paths["run_manifest"].relative_to(root)),
                "hashes": observed_hashes,
                "checks": checks,
            }
        )
    return sorted(audit, key=lambda item: item["cell_id"])


def m2_priority_gate_status(
    config: dict[str, Any], root: Path = ROOT
) -> tuple[bool, dict[str, Any]]:
    specifications = config.get("m2_priority_gate")
    if not isinstance(specifications, list):
        raise ValueError("m2_priority_gate must be a list")
    observed_arms = {str(item.get("arm")) for item in specifications}
    if observed_arms != EXPECTED_M2_ARMS or len(specifications) != 4:
        raise ValueError("M2 priority gate must name each registered seed-1 arm once")
    evidence: dict[str, Any] = {}
    ready = True
    for item in specifications:
        arm = str(item["arm"])
        path = _registered_path(root, str(item["marker"]))
        if not path.exists():
            evidence[arm] = {"marker": str(path.relative_to(root)), "exists": False}
            ready = False
            continue
        marker = _load(path)
        checks = {
            "schema": marker.get("schema_version")
            == "blind-gains.pilot-step-eval-marker.v1",
            "status": marker.get("status") == "complete",
            "step": marker.get("global_step") == 100,
            "all_marker_checks": isinstance(marker.get("checks"), dict)
            and bool(marker["checks"])
            and all(marker["checks"].values()),
        }
        if not all(checks.values()):
            raise ValueError(f"invalid M2 priority marker for {arm}: {checks}")
        evidence[arm] = {
            "marker": str(path.relative_to(root)),
            "exists": True,
            "sha256": _sha256(path),
            "checks": checks,
        }
    return ready, evidence


def initial_recovery_state(
    config: dict[str, Any], smoke_audit: list[dict[str, Any]]
) -> dict[str, Any]:
    full_cells = expand_cells(config, "full")
    return {
        "schema_version": "blind-gains.m11-full-recovery-state.v2",
        "status": "waiting_m2_priority",
        "created_utc": _now_utc(),
        "updated_utc": None,
        "capacity_poll_count": 0,
        "last_capacity_poll_utc": None,
        "last_observed_free_gpus": [],
        "last_stable_free_gpus": [],
        "gpu_free_streaks": {str(index): 0 for index in range(8)},
        "smoke_evidence": smoke_audit,
        "cells": {
            cell["id"]: {**cell, "status": "pending", "gpu": None, "run_dir": None}
            for cell in full_cells
        },
        "events": [],
    }


def run_full_phase(
    config: dict[str, Any], state: dict[str, Any], state_path: Path
) -> None:
    while True:
        refresh_cells(state)
        cells = list(state["cells"].values())
        if any(cell["status"] == "fail" for cell in cells):
            _atomic_json(state_path, state)
            raise RuntimeError("M11 full recovery has a failed cell")
        if all(cell["status"] == "complete" for cell in cells):
            _record(state, "full_phase_complete")
            _atomic_json(state_path, state)
            return

        m2_ready, m2_evidence = m2_priority_gate_status(config)
        state["m2_priority_ready"] = m2_ready
        state["m2_priority_evidence"] = m2_evidence
        if not m2_ready:
            state["status"] = "waiting_m2_priority"
            state["last_observed_free_gpus"] = []
            state["last_stable_free_gpus"] = []
            state["gpu_free_streaks"] = {str(index): 0 for index in range(8)}
            _atomic_json(state_path, state)
            time.sleep(int(config["poll_seconds"]))
            continue
        if not state.get("m2_priority_gate_opened"):
            state["m2_priority_gate_opened"] = True
            _record(state, "m2_priority_gate_opened", evidence=m2_evidence)

        state["status"] = "full"
        running = [cell for cell in cells if cell["status"] == "running"]
        reserved = {int(cell["gpu"]) for cell in running if cell["gpu"] is not None}
        allowed = {int(index) for index in config["allowed_gpu_ids"]}
        observed = [gpu for gpu in free_gpus(config, reserved) if gpu in allowed]
        stable = update_free_gpu_streaks(config, state, observed)
        record_capacity_poll(state, observed, stable)
        _atomic_json(state_path, state)
        slots = max(0, int(config["max_concurrent_jobs"]) - len(running))
        pending = [cell for cell in cells if cell["status"] == "pending"]
        for cell, gpu in zip(pending[:slots], stable):
            run_dir = launch_cell(config, cell, gpu)
            cell["status"] = "running"
            cell["gpu"] = gpu
            cell["run_dir"] = str(run_dir)
            state["gpu_free_streaks"][str(gpu)] = 0
            _record(
                state,
                "cell_launched",
                cell=cell["id"],
                gpu=gpu,
                run_dir=str(run_dir),
            )
            _atomic_json(state_path, state)
        time.sleep(int(config["poll_seconds"]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    config = _load(args.config)
    if config.get("schema_version") != "blind-gains.m11-full-recovery-config.v2":
        raise ValueError("unsupported M11 full-recovery config")
    smoke_audit = validate_smoke_evidence(config)
    full_cells = expand_cells(config, "full")
    if len(full_cells) != 18:
        raise ValueError("M11 full matrix must contain exactly 18 cells")
    if args.preflight_only:
        print(
            json.dumps(
                {
                    "status": "pass",
                    "smoke_cells": len(smoke_audit),
                    "full_cells": len(full_cells),
                    "model_performance_inspected": False,
                },
                sort_keys=True,
            )
        )
        return
    if args.run_dir is None:
        raise ValueError("--run-dir is required outside preflight mode")
    state_path = args.run_dir / "queue_state.json"
    state = _load(state_path) if state_path.exists() else initial_recovery_state(config, smoke_audit)
    if state.get("schema_version") != "blind-gains.m11-full-recovery-state.v2":
        raise ValueError("unsupported M11 recovery state")
    if not state_path.exists():
        _record(state, "full_recovery_initialized")
        _atomic_json(state_path, state)
    run_full_phase(config, state, state_path)
    build_report(config, state)
    state["status"] = "complete"
    _record(state, "report_complete", outputs=config["outputs"])
    _atomic_json(state_path, state)


if __name__ == "__main__":
    main()
