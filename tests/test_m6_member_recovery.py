from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from scripts import run_m6_member_recovery as recovery


ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    return path


def _inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path]:
    monkeypatch.setattr(recovery, "ROOT", tmp_path)
    cp = _write(
        tmp_path / "cp/run_manifest.json",
        {
            "status": "complete",
            "exit_code": 0,
            "artifacts_exist": True,
            "smoke_mode": "cp",
            "job_type": "m6_mini_a5_registered_plumbing_smoke",
            "node": "an29",
            "gpu_ids": list(range(8)),
        },
    )
    failed_log = tmp_path / "failed/member.log"
    failed_log.parent.mkdir(parents=True, exist_ok=True)
    failed_log.write_text("Gloo connectFullMesh failed before optimizer\n", encoding="utf-8")
    failed = _write(
        tmp_path / "failed/run_manifest.json",
        {
            "status": "fail",
            "exit_code": 1,
            "smoke_mode": "member",
            "job_type": "m6_mini_a5_registered_plumbing_smoke",
            "node": "an29",
            "gpu_ids": list(range(8)),
            "stdout_stderr_log": str(failed_log.relative_to(tmp_path)),
            "checkpoint_path": str(tmp_path / "absent-checkpoint"),
        },
    )
    output = _write(
        tmp_path / "preflight/preflight.json",
        {
            "status": "pass",
            "checks": {"both_rounds_pass": True},
            "rounds": [{"round_name": "default"}, {"round_name": "ib0"}],
        },
    )
    preflight = _write(
        tmp_path / "preflight/run_manifest.json",
        {
            "status": "complete",
            "exit_code": 0,
            "artifacts_exist": True,
            "job_type": "m6_single_node_collective_preflight",
            "node": "an29",
            "gpu_ids": list(range(8)),
            "expected_artifacts": [str(output.relative_to(tmp_path))],
            "end_time_utc": dt.datetime.now(dt.timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
        },
    )
    return cp, failed, preflight


def test_recovery_inputs_require_exact_failure_and_full_preflight(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cp, failed, preflight = _inputs(tmp_path, monkeypatch)
    assert recovery.validate_inputs(cp, failed, preflight)["status"] == "pass"


def test_adversarial_unrelated_member_failure_cannot_be_retried(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cp, failed, preflight = _inputs(tmp_path, monkeypatch)
    payload = json.loads(failed.read_text(encoding="utf-8"))
    (tmp_path / payload["stdout_stderr_log"]).write_text(
        "CUDA out of memory\n", encoding="utf-8"
    )
    result = recovery.validate_inputs(cp, failed, preflight)
    assert result["status"] == "fail"
    assert result["checks"]["failed_member_has_exact_gloo_signature"] is False


def test_adversarial_preflight_without_default_round_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cp, failed, preflight = _inputs(tmp_path, monkeypatch)
    payload = json.loads(preflight.read_text(encoding="utf-8"))
    output = tmp_path / payload["expected_artifacts"][0]
    output_payload = json.loads(output.read_text(encoding="utf-8"))
    output_payload["rounds"] = [{"round_name": "ib0"}]
    output.write_text(json.dumps(output_payload), encoding="utf-8")
    result = recovery.validate_inputs(cp, failed, preflight)
    assert result["status"] == "fail"
    assert result["checks"]["collective_preflight_includes_default_and_ib0"] is False


def test_adversarial_stale_preflight_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cp, failed, preflight = _inputs(tmp_path, monkeypatch)
    payload = json.loads(preflight.read_text(encoding="utf-8"))
    payload["end_time_utc"] = "2026-01-01T00:00:00Z"
    preflight.write_text(json.dumps(payload), encoding="utf-8")
    result = recovery.validate_inputs(cp, failed, preflight)
    assert result["status"] == "fail"
    assert result["checks"]["collective_preflight_fresh"] is False


def test_node_checks_ignore_foreign_ray_and_avoid_nested_grep_pipeline() -> None:
    launcher = (ROOT / "scripts/launch_m6_collective_preflight.sh").read_text(
        encoding="utf-8"
    )
    recovery_source = (ROOT / "scripts/run_m6_member_recovery.py").read_text(
        encoding="utf-8"
    )
    for source in (launcher, recovery_source):
        assert "[r]aylet" not in source
        assert "[g]cs_server" not in source
        assert "grep -F" not in source
        assert "[p]ython.*verl[.]trainer[.]main" in source
