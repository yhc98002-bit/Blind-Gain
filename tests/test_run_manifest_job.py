from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import scripts.run_manifest_job as runner
from scripts.run_manifest_job import run_manifest_job


def test_manifest_runner_executes_logs_and_finalizes(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.txt"
    manifest = tmp_path / "run_manifest.json"
    log = tmp_path / "run.log"
    manifest.write_text(
        json.dumps(
            {
                "command": f"printf artifact > '{artifact}'; printf logged-output",
                "expected_artifacts": [str(artifact)],
                "status": "running",
                "end_time_utc": None,
            }
        ),
        encoding="utf-8",
    )
    assert run_manifest_job(manifest, log) == 0
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["status"] == "complete"
    assert payload["artifacts_exist"] is True
    assert log.read_text(encoding="utf-8") == "logged-output"


def test_manifest_runner_finalizes_when_command_spawn_raises_oom(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = tmp_path / "run_manifest.json"
    log = tmp_path / "run.log"
    manifest.write_text(
        json.dumps(
            {
                "command": "never-started",
                "expected_artifacts": [],
                "status": "running",
                "end_time_utc": None,
            }
        ),
        encoding="utf-8",
    )

    def fail_spawn(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise OSError(12, "Cannot allocate memory")

    monkeypatch.setattr(runner.subprocess, "run", fail_spawn)
    assert run_manifest_job(manifest, log) == 126
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["status"] == "fail"
    assert payload["exit_code"] == 126
    assert payload["runner_error"] == {
        "phase": "spawn_registered_command",
        "error_type": "OSError",
        "message": "[Errno 12] Cannot allocate memory",
    }
    assert "could not spawn" in log.read_text(encoding="utf-8")
