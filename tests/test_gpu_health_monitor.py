from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.monitor_gpu_health import cadence_sleep_seconds, classify_run_sample, monitor_nodes


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
    assert "MemAvailable" in source
    assert "top_user_processes_by_rss" in source
    assert "os.kill" not in source
    assert ".terminate(" not in source
    assert ".send_signal(" not in source


def test_monitor_launcher_excludes_the_released_node() -> None:
    launcher = (ROOT / "scripts/launch_gpu_health_monitor.sh").read_text(encoding="utf-8")
    assert 'NODES=\'["an12","an29"]\'' in launcher
    assert '["an12","an21","an29"]' not in launcher
    assert 'observed_nodes:$nodes' in launcher
    assert 'RUN_ID="gpu_health_${GPU_COUNT}x60m_login_${STAMP}"' in launcher


def test_monitor_launcher_accepts_current_registered_training_units() -> None:
    launcher = (ROOT / "scripts/launch_gpu_health_monitor.sh").read_text(encoding="utf-8")

    assert "m3_mechanical_pilot_arm" in launcher
    assert "m5_anchor_resume_integrity_step101" in launcher
    assert "m5_anchor_longhorizon_400" in launcher
    assert "not a registered monitored training run" in launcher


def test_monitor_accepts_new_registered_node_without_changing_old_configs() -> None:
    assert monitor_nodes({}) == ("an12", "an29")
    assert monitor_nodes({"nodes": ["an12", "an21", "an29"]}) == (
        "an12",
        "an21",
        "an29",
    )


def test_monitor_rejects_unknown_or_duplicate_nodes() -> None:
    with pytest.raises(ValueError, match="unsupported"):
        monitor_nodes({"nodes": ["an12", "unknown"]})
    with pytest.raises(ValueError, match="duplicates"):
        monitor_nodes({"nodes": ["an21", "an21"]})
