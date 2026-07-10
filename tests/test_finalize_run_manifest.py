from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_finalizer_requires_zero_exit_and_all_artifacts(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.txt"
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"expected_artifacts": [str(artifact)]}), encoding="utf-8")

    subprocess.run(["python", str(ROOT / "scripts/finalize_run_manifest.py"), str(manifest), "0"], check=True)
    missing = json.loads(manifest.read_text(encoding="utf-8"))
    assert missing["status"] == "fail"
    assert missing["artifacts_exist"] is False

    artifact.write_text("done", encoding="utf-8")
    subprocess.run(["python", str(ROOT / "scripts/finalize_run_manifest.py"), str(manifest), "0"], check=True)
    complete = json.loads(manifest.read_text(encoding="utf-8"))
    assert complete["status"] == "complete"
    assert complete["artifacts_exist"] is True

    subprocess.run(["python", str(ROOT / "scripts/finalize_run_manifest.py"), str(manifest), "2"], check=True)
    failed = json.loads(manifest.read_text(encoding="utf-8"))
    assert failed["status"] == "fail"
    assert failed["exit_code"] == 2
