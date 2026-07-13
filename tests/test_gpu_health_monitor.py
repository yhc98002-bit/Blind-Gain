from __future__ import annotations

import subprocess
from pathlib import Path

from scripts.monitor_gpu_health import cadence_sleep_seconds, classify_run_sample


ROOT = Path(__file__).resolve().parents[1]


def _run(**overrides):
    value = {
        "manifest_status": "running", "wrapper_alive": True, "fatal_patterns": [],
        "max_logged_step": 20, "stdout_log_mtime_ns": 1,
    }
    value.update(overrides)
    return value


def test_idle_gpu_is_not_alone_an_unhealthy_classification() -> None:
    previous = _run(stdout_log_mtime_ns=1)
    current = _run(stdout_log_mtime_ns=2)
    result = classify_run_sample(current, previous, assigned_gpu_util=0.0)
    assert result["health"] == "healthy"
    assert "assigned_gpu_util_below_5pct" in result["reasons"]


def test_old_failure_signature_is_unhealthy_even_when_pid_lives() -> None:
    result = classify_run_sample(
        _run(fatal_patterns=["no space left on device"]),
        _run(),
        assigned_gpu_util=0.0,
    )
    assert result["health"] == "unhealthy"
    assert result["reasons"] == ["fatal_log_pattern:no space left on device"]


def test_running_manifest_with_missing_wrapper_is_unhealthy() -> None:
    result = classify_run_sample(_run(wrapper_alive=False), _run(), assigned_gpu_util=90.0)
    assert result == {"health": "unhealthy", "reasons": ["running_manifest_wrapper_missing"]}


def test_cadence_does_not_add_collection_time_to_interval() -> None:
    assert cadence_sleep_seconds(
        sample_started=100.0,
        collection_finished=124.0,
        interval_seconds=30.0,
        deadline=1000.0,
    ) == 6.0
    assert cadence_sleep_seconds(
        sample_started=100.0,
        collection_finished=135.0,
        interval_seconds=30.0,
        deadline=1000.0,
    ) == 0.0


def test_monitor_launcher_is_valid_and_read_only_by_contract() -> None:
    launcher = ROOT / "scripts/launch_gpu_health_monitor.sh"
    subprocess.run(["bash", "-n", str(launcher)], check=True)
    source = (ROOT / "scripts/monitor_gpu_health.py").read_text(encoding="utf-8")
    assert "nvidia-smi --query-gpu" in source
    assert "nvidia-smi --query-compute-apps" in source
    assert "os.kill" not in source
    assert ".terminate(" not in source
    assert ".send_signal(" not in source
