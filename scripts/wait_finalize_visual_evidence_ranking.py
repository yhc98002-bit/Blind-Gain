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
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG = Path("configs/eval/seed1_visual_evidence_ranking_v1.json")
RESULT_JSON = Path("reports/seed1_visual_evidence_ranking_results_v1.json")
RESULT_MD = Path("reports/seed1_visual_evidence_ranking_results_v1.md")
BUILDER_AUDIT = Path("reports/seed1_visual_evidence_ranking_builder_audit_v1.json")
INDEPENDENT_AUDIT = Path("reports/seed1_visual_evidence_ranking_audit_v1.json")


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def _atomic(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.partial")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _finish(manifest_path: Path, status: str, exit_code: int, opened: bool) -> None:
    manifest = _read(manifest_path)
    manifest.update(
        {
            "status": status,
            "exit_code": exit_code,
            "end_time_utc": _now(),
            "performance_values_opened": opened,
        }
    )
    _atomic(manifest_path, manifest)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue-dir", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--poll-seconds", type=int, default=120)
    args = parser.parse_args()
    if args.poll_seconds < 30:
        raise ValueError("poll interval must be at least 30 seconds")
    queue_dir = Path(args.queue_dir)
    run_dir = Path(args.run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = run_dir / "run_manifest.json"
    if manifest_path.exists():
        raise FileExistsError("finalizer watcher manifest already exists")
    outputs = [RESULT_JSON, RESULT_MD, BUILDER_AUDIT, INDEPENDENT_AUDIT]
    if any((ROOT / path).exists() for path in outputs):
        raise FileExistsError("refusing to overwrite a diagnostic result artifact")
    config = _read(ROOT / CONFIG)
    manifest = {
        "schema_version": "blind-gains.visual-evidence-ranking-finalizer-watch.v1",
        "run_id": run_dir.name,
        "job_type": "post_seed1_visual_evidence_ranking_finalizer",
        "status": "waiting",
        "node": "login",
        "gpu_ids": [],
        "tensor_parallel_width": 0,
        "replica_count": 0,
        "placement_justification": "CPU-only lifecycle wait, paired bootstrap finalization, and independent raw-score recomputation audit.",
        "git_hash": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "config_path": str(CONFIG),
        "config_hash": _sha256(ROOT / CONFIG),
        "data_manifest": config["candidate_registry"]["path"],
        "data_manifest_hash": config["candidate_registry"]["sha256"],
        "source_queue": str(queue_dir),
        "command": f"scripts/wait_finalize_visual_evidence_ranking.py --queue-dir {queue_dir} --run-dir {run_dir} --poll-seconds {args.poll_seconds}",
        "start_time_utc": _now(),
        "end_time_utc": None,
        "exit_code": None,
        "performance_values_opened": False,
        "expected_artifacts": [str(path) for path in outputs],
    }
    _atomic(manifest_path, manifest)

    while True:
        queue_manifest_path = queue_dir / "run_manifest.json"
        matrix_path = queue_dir / "matrix_runs.json"
        if not queue_manifest_path.is_file():
            time.sleep(args.poll_seconds)
            continue
        queue_manifest = _read(queue_manifest_path)
        if queue_manifest.get("status") in {"failed", "fail", "error", "cancelled", "canceled"}:
            _finish(manifest_path, "failed", 1, False)
            raise SystemExit(1)
        if queue_manifest.get("status") == "complete" and matrix_path.is_file():
            break
        time.sleep(args.poll_seconds)

    matrix = _read(matrix_path)
    runs = matrix.get("runs")
    if matrix.get("status") != "complete" or not isinstance(runs, list) or len(runs) != 9:
        _finish(manifest_path, "failed", 2, False)
        raise SystemExit(2)
    run_dirs = [str(item["run_dir"]) for item in runs]
    finalizer_command = [
        str(ROOT / ".venv/bin/python"),
        str(ROOT / "scripts/finalize_visual_evidence_ranking.py"),
        "--config",
        str(CONFIG),
        "--json-output",
        str(RESULT_JSON),
        "--markdown-output",
        str(RESULT_MD),
        "--audit-output",
        str(BUILDER_AUDIT),
    ]
    for child in run_dirs:
        finalizer_command.extend(["--run-dir", child])
    result = subprocess.run(finalizer_command, cwd=ROOT, check=False)
    if result.returncode != 0:
        _finish(manifest_path, "failed", result.returncode, True)
        raise SystemExit(result.returncode)

    audit_command = [
        str(ROOT / ".venv/bin/python"),
        str(ROOT / "scripts/audit_visual_evidence_ranking.py"),
        "--config",
        str(CONFIG),
        "--result-json",
        str(RESULT_JSON),
        "--result-markdown",
        str(RESULT_MD),
        "--output",
        str(INDEPENDENT_AUDIT),
    ]
    for child in run_dirs:
        audit_command.extend(["--run-dir", child])
    audit = subprocess.run(audit_command, cwd=ROOT, check=False)
    if audit.returncode != 0:
        _finish(manifest_path, "failed", audit.returncode, True)
        raise SystemExit(audit.returncode)
    _finish(manifest_path, "complete", 0, True)


if __name__ == "__main__":
    main()
