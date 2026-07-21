#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARMS = {"a1_real", "a2_gray", "a2b_noimage", "a3_caption"}
STEPS = {60, 100}
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
    resolved.relative_to(root.resolve())
    return resolved


def validate_children(payload: dict[str, Any], root: Path = ROOT) -> None:
    if payload.get("schema_version") != "blind-gains.pilot-followup-eval-children.v1":
        raise ValueError("unsupported lifecycle children schema")
    if payload.get("seed") not in {2, 3}:
        raise ValueError("lifecycle seed must be 2 or 3")
    endpoints = payload.get("endpoints")
    if not isinstance(endpoints, list) or len(endpoints) != 8:
        raise ValueError("lifecycle requires exactly eight arm/checkpoint endpoints")
    observed: set[tuple[str, int]] = set()
    for endpoint in endpoints:
        if not isinstance(endpoint, dict):
            raise ValueError("endpoint must be a JSON object")
        identity = (endpoint.get("arm"), endpoint.get("global_step"))
        if identity[0] not in ARMS or identity[1] not in STEPS:
            raise ValueError(f"invalid endpoint identity: {identity}")
        if identity in observed:
            raise ValueError(f"duplicate endpoint identity: {identity}")
        observed.add(identity)
        for field in ("r19_queue_run", "geo3k_queue_run"):
            if not isinstance(endpoint.get(field), str):
                raise ValueError(f"endpoint lacks {field}")
            run = _resolve(root, endpoint[field])
            if not (run / "run_manifest.json").is_file():
                raise ValueError(f"endpoint queue manifest absent: {run}")
    if observed != {(arm, step) for arm in ARMS for step in STEPS}:
        raise ValueError("lifecycle endpoint matrix is incomplete")


def _validate_queue_manifest(
    manifest: dict[str, Any],
    *,
    expected_job_type: str,
    arm: str,
    seed: int,
    global_step: int,
) -> None:
    expected = {
        "job_type": expected_job_type,
        "arm": arm,
        "pilot_seed": seed,
        "global_step": global_step,
        "performance_values_opened": False,
    }
    errors = {
        key: {"expected": value, "observed": manifest.get(key)}
        for key, value in expected.items()
        if manifest.get(key) != value
    }
    if errors:
        raise ValueError(f"queue identity mismatch: {errors}")


def _validate_complete_endpoint(
    endpoint: dict[str, Any],
    *,
    seed: int,
    root: Path,
) -> dict[str, Any] | None:
    arm = str(endpoint["arm"])
    global_step = int(endpoint["global_step"])
    r19_run = _resolve(root, endpoint["r19_queue_run"])
    geo_run = _resolve(root, endpoint["geo3k_queue_run"])
    r19_manifest_path = r19_run / "run_manifest.json"
    geo_manifest_path = geo_run / "run_manifest.json"
    r19_manifest = _read_json(r19_manifest_path)
    geo_manifest = _read_json(geo_manifest_path)
    _validate_queue_manifest(
        r19_manifest,
        expected_job_type="pilot_followup_r19_evaluation_queue",
        arm=arm,
        seed=seed,
        global_step=global_step,
    )
    _validate_queue_manifest(
        geo_manifest,
        expected_job_type="pilot_followup_geo3k_evaluation_queue",
        arm=arm,
        seed=seed,
        global_step=global_step,
    )
    statuses = {"r19": r19_manifest.get("status"), "geo3k": geo_manifest.get("status")}
    failures = {key: value for key, value in statuses.items() if value in TERMINAL_FAILURES}
    if failures:
        raise RuntimeError(f"endpoint queue failed for {arm}/step{global_step}: {failures}")
    if set(statuses.values()) != {"complete"}:
        return None

    r19_state_path = _resolve(root, str(r19_manifest["expected_artifacts"][0]))
    geo_state_path = _resolve(root, str(geo_manifest["expected_artifacts"][0]))
    r19_state = _read_json(r19_state_path)
    geo_state = _read_json(geo_state_path)
    if r19_state.get("status") != "complete" or geo_state.get("status") != "complete":
        raise ValueError("complete queue manifest has incomplete lifecycle state")
    marker_path = _resolve(root, str(r19_manifest["expected_artifacts"][1]))
    marker = _read_json(marker_path)
    marker_checks = marker.get("checks")
    if (
        marker.get("status") != "complete"
        or marker.get("global_step") != global_step
        or not isinstance(marker_checks, dict)
        or not marker_checks
        or not all(marker_checks.values())
    ):
        raise ValueError("R19 marker did not pass every structural check")

    audit_run = _resolve(root, str(geo_state.get("audit_run", "")))
    audit_path = audit_run / "audit.json"
    audit = _read_json(audit_path)
    audit_checks = audit.get("checks")
    if (
        audit.get("status") != "pass"
        or audit.get("row_count") != 601
        or audit.get("performance_values_reported") is not False
        or not isinstance(audit_checks, dict)
        or not audit_checks
        or not all(audit_checks.values())
    ):
        raise ValueError("Geometry3K 601-row audit did not pass every structural check")
    return {
        "arm": arm,
        "global_step": global_step,
        "r19_queue_manifest_sha256": _sha256(r19_manifest_path),
        "r19_state_sha256": _sha256(r19_state_path),
        "r19_marker_sha256": _sha256(marker_path),
        "geo3k_queue_manifest_sha256": _sha256(geo_manifest_path),
        "geo3k_state_sha256": _sha256(geo_state_path),
        "geo3k_audit_sha256": _sha256(audit_path),
        "geo3k_row_count": 601,
    }


def _atomic_output(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite lifecycle output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.partial")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--children", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--poll-seconds", type=int, default=60)
    args = parser.parse_args()
    if args.poll_seconds < 10:
        raise ValueError("poll interval must be at least 10 seconds")
    payload = _read_json(args.children)
    validate_children(payload)
    while True:
        completed: list[dict[str, Any]] = []
        for endpoint in payload["endpoints"]:
            result = _validate_complete_endpoint(
                endpoint,
                seed=int(payload["seed"]),
                root=ROOT,
            )
            if result is not None:
                completed.append(result)
        print(
            json.dumps(
                {
                    "time_utc": _now(),
                    "completed_endpoints": len(completed),
                    "expected_endpoints": 8,
                },
                sort_keys=True,
            ),
            flush=True,
        )
        if len(completed) == 8:
            _atomic_output(
                args.output,
                {
                    "schema_version": "blind-gains.pilot-followup-eval-lifecycle.v1",
                    "status": "complete",
                    "seed": payload["seed"],
                    "completed_at_utc": _now(),
                    "children_manifest": str(args.children),
                    "children_manifest_sha256": _sha256(args.children),
                    "endpoints": sorted(
                        completed, key=lambda item: (item["arm"], item["global_step"])
                    ),
                    "checks": {
                        "all_four_arms": {item["arm"] for item in completed} == ARMS,
                        "both_registered_checkpoints": {
                            item["global_step"] for item in completed
                        }
                        == STEPS,
                        "eight_endpoint_matrix": len(completed) == 8,
                        "all_geo3k_audits_601_rows": all(
                            item["geo3k_row_count"] == 601 for item in completed
                        ),
                    },
                    "performance_values_opened": False,
                    "scientific_gate_decision": None,
                },
            )
            return
        time.sleep(args.poll_seconds)


if __name__ == "__main__":
    main()
