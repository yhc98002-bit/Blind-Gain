#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

from src.eval.blind_solvability import CONDITIONS


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_NODE = "an29"
EXPECTED_GPU = {"real": 0, "gray": 1, "none": 2, "caption": 3, "noise": 4}
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


def _line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def validate_config(config: dict[str, Any], root: Path = ROOT) -> None:
    if config.get("schema_version") != "blind-gains.m8-summary-queue.v1":
        raise ValueError("unsupported M8 summary queue schema")
    if config.get("expected_job_type") != "m8_virl39k_7b_blind_solvability_v1":
        raise ValueError("M8 queue has an unexpected source job type")
    model_revision = config.get("expected_model_revision")
    if not isinstance(model_revision, str) or re.fullmatch(
        r"Qwen/Qwen2\.5-VL-7B-Instruct@[0-9a-f]{40}", model_revision
    ) is None:
        raise ValueError("M8 queue must pin an exact Qwen2.5-VL-7B revision")
    if config.get("expected_row_count") != 4096:
        raise ValueError("M8 queue is pinned to 4,096 rows per condition")
    runs = config.get("runs")
    if not isinstance(runs, dict) or set(runs) != set(CONDITIONS):
        raise ValueError("M8 queue requires exactly the five registered conditions")
    resolved_runs = []
    for condition in CONDITIONS:
        value = runs.get(condition)
        if not isinstance(value, str):
            raise ValueError(f"missing run path for {condition}")
        run = _resolve(root, value)
        if not (run / "run_manifest.json").is_file():
            raise ValueError(f"source run manifest is absent: {condition}")
        resolved_runs.append(run)
    if len(set(resolved_runs)) != len(CONDITIONS):
        raise ValueError("condition run paths must be unique")
    outputs = config.get("outputs")
    expected_outputs = {
        "summary_json",
        "summary_markdown",
        "audit_json",
        "audit_markdown",
    }
    if not isinstance(outputs, dict) or set(outputs) != expected_outputs:
        raise ValueError("M8 queue output registry is incomplete")
    for value in outputs.values():
        if not isinstance(value, str):
            raise ValueError("M8 output paths must be strings")
        path = _resolve(root, value)
        if path.suffix not in {".json", ".md"} or path.parent != root / "reports":
            raise ValueError("M8 outputs must be JSON/Markdown under reports")
    state_path = config.get("state_path")
    if not isinstance(state_path, str):
        raise ValueError("M8 queue state_path is missing")
    _resolve(root, state_path)
    if not isinstance(config.get("poll_seconds"), int) or config["poll_seconds"] < 30:
        raise ValueError("M8 queue poll_seconds must be >= 30")


def inspect_source_runs(
    config: dict[str, Any], root: Path = ROOT
) -> tuple[str, dict[str, Any]]:
    statuses: dict[str, Any] = {}
    complete = 0
    for condition in CONDITIONS:
        run = _resolve(root, config["runs"][condition])
        manifest_path = run / "run_manifest.json"
        manifest = _read_json(manifest_path)
        expected = {
            "job_type": config["expected_job_type"],
            "condition": condition,
            "node": EXPECTED_NODE,
            "gpu_ids": [EXPECTED_GPU[condition]],
            "tensor_parallel_width": 1,
            "replica_count": 1,
            "model_revision": config["expected_model_revision"],
            "sample_size": config["expected_row_count"],
            "sample_count": 16,
            "max_tokens": 2048,
            "seed": 20260710,
        }
        mismatches = {
            key: {"expected": value, "observed": manifest.get(key)}
            for key, value in expected.items()
            if manifest.get(key) != value
        }
        artifacts = manifest.get("expected_artifacts")
        expected_output = run / "per_item.jsonl"
        if artifacts != [str(expected_output.relative_to(root))]:
            mismatches["expected_artifacts"] = {
                "expected": [str(expected_output.relative_to(root))],
                "observed": artifacts,
            }
        if mismatches:
            raise ValueError(f"M8 {condition} identity mismatch: {mismatches}")
        status = manifest.get("status")
        if status in TERMINAL_FAILURES:
            raise RuntimeError(f"M8 {condition} reached terminal failure: {status}")
        record: dict[str, Any] = {
            "status": status,
            "manifest_sha256": _sha256(manifest_path),
        }
        if status == "complete":
            if manifest.get("exit_code") != 0 or manifest.get("artifacts_exist") is not True:
                raise RuntimeError(f"M8 {condition} completion is unverified")
            if not expected_output.is_file():
                raise RuntimeError(f"M8 {condition} output is absent")
            rows = _line_count(expected_output)
            if rows != config["expected_row_count"]:
                raise RuntimeError(f"M8 {condition} has {rows} rows, expected 4096")
            record.update(rows=rows, output_sha256=_sha256(expected_output))
            complete += 1
        statuses[condition] = record
    return ("complete" if complete == len(CONDITIONS) else "running"), statuses


def _parse_run_path(output: str, root: Path) -> Path:
    candidates = [
        line.strip()
        for line in output.splitlines()
        if line.strip().startswith("experiments/runs/")
    ]
    if len(candidates) != 1:
        raise RuntimeError(f"ambiguous M8 summary launcher output: {output!r}")
    return _resolve(root, candidates[0])


def launch_summary(config_path: Path, root: Path = ROOT) -> Path:
    result = subprocess.run(
        ["bash", "scripts/launch_virl39k_7b_blind_v1_summary.sh", str(config_path)],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"M8 summary launch failed ({result.returncode}): {result.stderr.strip()}"
        )
    return _parse_run_path(result.stdout, root)


def validate_summary_run(
    run: Path,
    config: dict[str, Any],
    config_path: Path,
    root: Path = ROOT,
) -> dict[str, Any]:
    manifest = _read_json(run / "run_manifest.json")
    expected_artifacts = [config["outputs"][name] for name in (
        "summary_json",
        "summary_markdown",
        "audit_json",
        "audit_markdown",
    )]
    if (
        manifest.get("job_type") != "m8_virl39k_7b_summary_audit"
        or manifest.get("node") != "login"
        or manifest.get("gpu_ids") != []
        or manifest.get("expected_artifacts") != expected_artifacts
        or manifest.get("queue_config") != str(config_path.relative_to(root))
        or manifest.get("queue_config_sha256") != _sha256(config_path)
    ):
        raise ValueError("M8 summary run identity mismatch")
    status = manifest.get("status")
    if status in TERMINAL_FAILURES:
        raise RuntimeError(f"M8 summary reached terminal failure: {status}")
    if status != "complete":
        return manifest
    if manifest.get("exit_code") != 0 or manifest.get("artifacts_exist") is not True:
        raise RuntimeError("M8 summary completion is unverified")
    for value in expected_artifacts:
        if not _resolve(root, value).is_file():
            raise RuntimeError(f"M8 summary artifact is absent: {value}")
    audit = _read_json(_resolve(root, config["outputs"]["audit_json"]))
    summary = _read_json(_resolve(root, config["outputs"]["summary_json"]))
    checks = audit.get("checks")
    if (
        audit.get("status") != "pass"
        or audit.get("expected_job_type") != config["expected_job_type"]
        or audit.get("expected_model_revision") != config["expected_model_revision"]
        or audit.get("row_counts") != {condition: 4096 for condition in CONDITIONS}
        or audit.get("recomputed_score_mismatch_count") != 0
        or audit.get("runs") != config["runs"]
        or not isinstance(checks, dict)
        or not checks
        or not all(checks.values())
        or summary.get("status") != "pass"
        or summary.get("n_items") != 4096
        or (summary.get("evaluation_contract") or {}).get("model_revision")
        != config["expected_model_revision"]
    ):
        raise ValueError("M8 summary audit did not satisfy every structural check")
    return manifest


def run_queue(
    config_path: Path,
    *,
    root: Path = ROOT,
    once: bool = False,
    summary_launcher: Callable[[Path, Path], Path] = launch_summary,
) -> int:
    config_path = _resolve(root, str(config_path))
    config = _read_json(config_path)
    validate_config(config, root)
    state_path = _resolve(root, config["state_path"])
    state = _read_json(state_path) if state_path.is_file() else {
        "schema_version": "blind-gains.m8-summary-queue-state.v1",
        "created_utc": _now(),
        "status": "initialized",
        "poll_count": 0,
        "performance_values_inspected": False,
        "scientific_gate_decision": None,
    }
    try:
        while True:
            state["poll_count"] = int(state.get("poll_count", 0)) + 1
            state["updated_utc"] = _now()
            summary_value = state.get("summary_run")
            if isinstance(summary_value, str):
                summary_run = _resolve(root, summary_value)
                manifest = validate_summary_run(
                    summary_run,
                    config,
                    config_path,
                    root,
                )
                if manifest.get("status") == "complete":
                    state.update(
                        status="complete",
                        audit_sha256=_sha256(
                            _resolve(root, config["outputs"]["audit_json"])
                        ),
                        summary_sha256=_sha256(
                            _resolve(root, config["outputs"]["summary_json"])
                        ),
                    )
                    _write_state(state_path, state)
                    return 0
                state["status"] = "summary_running"
            else:
                source_status, source_runs = inspect_source_runs(config, root)
                state["source_runs"] = source_runs
                if source_status == "complete":
                    summary_run = summary_launcher(config_path, root)
                    state["summary_run"] = str(summary_run.relative_to(root))
                    state["status"] = "summary_running"
                else:
                    state["status"] = "waiting_source_runs"
            _write_state(state_path, state)
            print(
                json.dumps(
                    {
                        "time_utc": state["updated_utc"],
                        "status": state["status"],
                        "poll_count": state["poll_count"],
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
            status="failed",
            updated_utc=_now(),
            error=f"{type(error).__name__}: {error}",
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
