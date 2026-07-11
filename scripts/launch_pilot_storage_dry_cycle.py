#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_manifest_job import run_manifest_job  # noqa: E402


def _stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_json(path: Path, payload: dict[str, object]) -> None:
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def main() -> None:
    stamp = _stamp()
    run_id = f"pilot_storage_dry_cycle_login_{stamp}"
    run_dir = ROOT / "experiments" / "runs" / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "logs").mkdir()
    manifest = run_dir / "run_manifest.json"
    result = run_dir / "dry_cycle_result.json"
    shared = ROOT / "checkpoints" / "pilot" / run_id
    archive = Path("/tmp/blindgain_checkpoint_archive/pilot") / run_id
    snapshot = ROOT / "reports" / "storage_usage_snapshot.json"
    command = shlex.join(
        [
            str(ROOT / ".venv" / "bin" / "python"),
            str(ROOT / "scripts" / "pilot_storage_dry_cycle.py"),
            "--shared-checkpoint-root",
            str(shared),
            "--archive-root",
            str(archive),
            "--run-manifest",
            str(manifest),
            "--result",
            str(result),
            "--usage-snapshot",
            str(snapshot),
        ]
    )
    git_hash = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    payload: dict[str, object] = {
        "run_id": run_id,
        "job_type": "pilot_storage_dry_save_sweep_readback",
        "node": "login",
        "gpu_allocation": [],
        "git_hash": git_hash,
        "config_hash": hashlib.sha256(command.encode("utf-8")).hexdigest(),
        "data_manifest": str(snapshot),
        "data_manifest_hash": _sha256(snapshot),
        "seed": 0,
        "command": command,
        "start_time_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end_time_utc": None,
        "status": "running",
        "expected_artifacts": [str(result), str(archive)],
        "artifact_path": str(result),
        "deviations": [
            "Synthetic EasyR1-compatible bytes exercise storage plumbing without taking a pilot optimizer step."
        ],
    }
    _atomic_json(manifest, payload)
    exit_code = run_manifest_job(manifest, run_dir / "logs" / "login.log")
    print(run_dir)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
