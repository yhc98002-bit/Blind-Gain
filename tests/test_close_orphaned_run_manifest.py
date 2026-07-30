from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/close_orphaned_run_manifest.py"


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True
    )


def _manifest(tmp_path: Path, **extra) -> Path:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    manifest = run_dir / "run_manifest.json"
    payload = {"run_id": "r", "status": "running", "end_time_utc": None, "deviations": []}
    payload.update(extra)
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    return manifest


def test_closes_a_dead_run_and_records_the_timestamp_discrepancy(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    artifact = manifest.parent / "artifact.jsonl"
    artifact.write_text("done", encoding="utf-8")
    os.utime(artifact, (1_784_000_000, 1_784_000_000))

    result = _run(
        [
            str(manifest),
            "--exit-code", "0",
            "--exit-code-provenance", "inferred from artifacts",
            "--completion-evidence", str(artifact),
            "--expected-artifact", str(artifact),
            "--reason", "launcher execed the trainer directly",
        ]
    )
    assert result.returncode == 0, result.stderr

    closed = json.loads(manifest.read_text(encoding="utf-8"))
    assert closed["status"] == "complete"
    assert closed["exit_code"] == 0
    # expected_artifacts declared post-hoc, so artifacts_exist is not vacuous
    assert closed["artifacts_exist"] is True
    assert closed["expected_artifacts_declared_post_hoc"] is True
    # the close-time stamp and the true completion time are both present and differ
    assert closed["end_time_utc"] is not None
    assert closed["observed_completion_utc"] == "2026-07-14T03:33:20Z"
    assert closed["observed_completion_utc"] != closed["end_time_utc"]
    assert "NOT the true completion time" in closed["end_time_utc_source"]
    assert closed["exit_code_provenance"] == "inferred from artifacts"
    entry = closed["deviations"][-1]
    assert entry["code"] == "post_hoc_manifest_close"
    assert entry["observed_completion_utc"] == "2026-07-14T03:33:20Z"


def test_refuses_a_manifest_that_is_already_closed(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path, status="complete")
    result = _run(
        [
            str(manifest),
            "--exit-code", "0",
            "--exit-code-provenance", "x",
            "--reason", "y",
        ]
    )
    assert result.returncode == 3
    assert "already closed" in result.stderr
    assert json.loads(manifest.read_text(encoding="utf-8"))["status"] == "complete"


def test_refuses_while_the_recorded_pid_is_still_alive(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path, node=socket.gethostname())
    pid_dir = manifest.parent / "pids"
    pid_dir.mkdir()
    (pid_dir / "local.pid").write_text(str(os.getpid()), encoding="utf-8")

    result = _run(
        [
            str(manifest),
            "--exit-code", "0",
            "--exit-code-provenance", "x",
            "--reason", "y",
        ]
    )
    assert result.returncode == 3
    assert "in flight is never closed" in result.stderr
    still = json.loads(manifest.read_text(encoding="utf-8"))
    assert still["status"] == "running"
    assert still["end_time_utc"] is None


def test_refuses_when_pid_liveness_is_indeterminate(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path, node=socket.gethostname())
    pid_dir = manifest.parent / "pids"
    pid_dir.mkdir()
    (pid_dir / "junk.pid").write_text("not-a-pid", encoding="utf-8")

    result = _run(
        [
            str(manifest),
            "--exit-code", "0",
            "--exit-code-provenance", "x",
            "--reason", "y",
        ]
    )
    assert result.returncode == 3
    assert json.loads(manifest.read_text(encoding="utf-8"))["status"] == "running"
