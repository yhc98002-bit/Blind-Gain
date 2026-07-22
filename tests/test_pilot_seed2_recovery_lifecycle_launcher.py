from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts/launch_pilot_seed2_recovery_lifecycle.sh"


def test_seed2_recovery_lifecycle_launcher_is_valid_shell() -> None:
    subprocess.run(["bash", "-n", str(LAUNCHER)], check=True)


def test_seed2_recovery_lifecycle_replaces_only_step60_geo3k() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")

    assert "source_failed_lifecycle" in source
    assert "select(.global_step == 60" in source
    assert "geo3k_queue_run" in source
    assert "r19_queue_run" not in source.split("jq \\", 1)[-1].split(
        '"${ORIGINAL_CHILDREN}"', 1
    )[0]
    assert "performance_values_opened: false" in source


def test_seed2_recovery_lifecycle_serializes_launcher_admission() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")

    lock = source.index("blindgain_pilot_seed2_recovery_lifecycle.lock")
    admission_scan = source.index("pilot_followup_evaluation_recovery_lifecycle")
    run_id = source.index('RUN_ID="pilot_seed2_recovery_eval_lifecycle')
    assert "flock -n 9" in source
    assert lock < admission_scan < run_id
