from __future__ import annotations

import signal
import subprocess
from pathlib import Path

import pytest

from scripts.run_m5_recovery_queue import snapshot_gpu_rows


ROOT = Path(__file__).resolve().parents[1]


def test_m5_recovery_queue_requires_all_eight_gpu_rows() -> None:
    rows = [f"{index}, 0, 0" for index in range(8)]
    parsed = snapshot_gpu_rows(rows)
    assert parsed[7] == {"memory_mib": 0, "utilization_pct": 0}
    with pytest.raises(RuntimeError, match="eight GPU rows"):
        snapshot_gpu_rows(rows[:-1])


def test_m5_recovery_queue_is_fail_closed_before_launch() -> None:
    source = (ROOT / "scripts/run_m5_recovery_queue.py").read_text(encoding="utf-8")
    assert '"restore_complete"' in source
    assert '"a1_complete"' in source
    assert "stable_polls < 2" in source
    assert "mem_available_kib >= 681574400" in source
    assert "selected_gpus_free" in source
    assert "project_trainer_absent" in source
    assert source.index("stable_polls < 2") < source.index(
        '"scripts/launch_m5_anchor_recovery150.sh"'
    )
    assert '"--ray-preflight-run"' in source
    assert "str(args.ray_preflight_run)" in source


def test_m5_recovery_queue_only_resumes_the_cpu_seed_queue() -> None:
    source = (ROOT / "scripts/run_m5_recovery_queue.py").read_text(encoding="utf-8")
    assert "signal.SIGCONT" in source
    assert "signal.SIGTERM" not in source
    assert "signal.SIGKILL" not in source
    assert "scripts/run_pilot_followup_queue.py --seed 2" in source
    assert signal.SIGCONT is not None


def test_m5_recovery_queue_launchers_parse() -> None:
    for name in ("launch_m5_recovery_queue.sh", "launch_m5_anchor_recovery150.sh"):
        subprocess.run(["bash", "-n", str(ROOT / "scripts" / name)], check=True)
    launcher = (ROOT / "scripts/launch_m5_recovery_queue.sh").read_text(encoding="utf-8")
    assert "--ray-preflight-run '${RAY_PREFLIGHT_RUN}'" in launcher
