from __future__ import annotations

import json
from pathlib import Path

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
