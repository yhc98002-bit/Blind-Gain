"""Contract tests for the M7 arm launcher's manifest lifecycle.

M7 manifests never closed because scripts/launch_m7_virl_arm.sh exec'd
verl.trainer.main directly, so nothing outlived the trainer to stamp
end_time_utc/exit_code/status. Every other training launcher in this repo routes
through scripts/run_manifest_job.py, which reads payload["command"] and calls
finalize_manifest on exit. These tests pin that routing so the regression cannot
come back silently.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts/launch_m7_virl_arm.sh"
REFERENCE_LAUNCHERS = (
    ROOT / "scripts/launch_mech_pilot_arm.sh",
    ROOT / "scripts/launch_mini_a5_main.sh",
)


def _text() -> str:
    return LAUNCHER.read_text(encoding="utf-8")


def _launch_line() -> str:
    for line in _text().splitlines():
        if line.startswith('ssh "${NODE}"') and "nohup" in line:
            return line
    raise AssertionError("no remote launch line found in the M7 launcher")


def test_launcher_is_syntactically_valid() -> None:
    subprocess.run(["bash", "-n", str(LAUNCHER)], check=True)


def test_remote_launch_goes_through_run_manifest_job() -> None:
    line = _launch_line()
    assert "scripts/run_manifest_job.py" in line
    assert "${MANIFEST}" in line and "${LOG}" in line
    # the trainer must no longer be exec'd by the launcher itself; the runner
    # execs it from the manifest's own "command" field
    assert "verl.trainer.main" not in line


def test_reference_launchers_route_the_same_way() -> None:
    for launcher in REFERENCE_LAUNCHERS:
        body = launcher.read_text(encoding="utf-8")
        assert "scripts/run_manifest_job.py" in body, launcher


def test_runner_and_finalizer_are_byte_clean_contract_files() -> None:
    critical = re.search(r"^CRITICAL=\((.*?)\)$", _text(), re.MULTILINE | re.DOTALL)
    assert critical is not None
    body = critical.group(1)
    assert "scripts/run_manifest_job.py" in body
    assert "scripts/finalize_run_manifest.py" in body


def test_manifest_declares_expected_artifacts_so_the_close_is_not_vacuous() -> None:
    # finalize_manifest computes artifacts_exist = all(expected_artifacts exist);
    # with no expected_artifacts that is vacuously True and status is decided by
    # the exit code alone.
    assert "expected_artifacts:" in _text()


def test_emitted_manifest_is_valid_json_with_the_lifecycle_fields(tmp_path: Path) -> None:
    jq = shutil.which("jq") or shutil.which("jq", path=os.path.expanduser("~/.local/bin"))
    if jq is None:
        pytest.skip("jq is not on PATH (it lives in ~/.local/bin on this cluster)")

    body = _text()
    program = re.search(r"'(\{schema_version:.*?\})' > \"\$\{MANIFEST\}\"", body, re.DOTALL)
    assert program is not None, "could not extract the jq manifest program"

    args = [
        jq, "-n",
        "--arg", "run_id", "rid",
        "--arg", "git", "deadbeef",
        "--arg", "arm", "a1_real",
        "--argjson", "seed", "1",
        "--arg", "node", "an12",
        "--arg", "config", "configs/train/x.yaml",
        "--arg", "config_sha", "cfg",
        "--arg", "train", "data/train.jsonl",
        "--arg", "train_sha", "t",
        "--arg", "val", "data/val.jsonl",
        "--arg", "val_sha", "v",
        "--arg", "ckpt", "/ckpt/root",
        "--arg", "command", "env X=1 python -m verl.trainer.main config=/x.yaml",
        "--arg", "start", "2026-07-30T00:00:00Z",
        "--arg", "log", "experiments/runs/rid/logs/an12.log",
        "--arg", "shadow", "/run/reward_shadow.jsonl",
        "--argjson", "gpus", "[0,1,2,3]",
        "--argjson", "deviations", "[]",
        program.group(1),
    ]
    emitted = json.loads(subprocess.run(args, capture_output=True, text=True, check=True).stdout)

    assert emitted["status"] == "running"
    assert emitted["end_time_utc"] is None
    assert emitted["command"].startswith("env ")
    assert emitted["expected_artifacts"] == [
        "/run/reward_shadow.jsonl",
        "/ckpt/root/experiment_log.jsonl",
        "/ckpt/root/checkpoint_tracker.json",
    ]
