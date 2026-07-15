from __future__ import annotations

import subprocess
from pathlib import Path

from scripts.watch_pilot_retention_recovery import RECOVERY_STEPS, relocation_plan


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts/launch_pilot_retention_recovery.sh"


def test_retention_recovery_handles_only_unfinished_future_steps() -> None:
    assert RECOVERY_STEPS == (80, 100)
    assert relocation_plan() == {
        80: "relocate_after_merge",
        100: "retain_final_on_shared",
    }


def test_retention_recovery_launcher_is_fail_closed_and_serialized() -> None:
    subprocess.run(["bash", "-n", str(LAUNCHER)], check=True)
    source = LAUNCHER.read_text(encoding="utf-8")

    assert "retention recovery requires a completed pilot parent" in source
    assert "recovery target watcher is not failed" in source
    assert "recovery watcher parent mismatch" in source
    assert "failed watcher archive lineage mismatch" in source
    assert "another pilot retention recovery is active" in source
    assert "recovery_of_manifest_sha256" in source
    assert "recovery_schedule: [80, 100]" in source


def test_retention_recovery_does_not_mutate_active_watcher_bundle() -> None:
    source = (ROOT / "scripts/watch_pilot_retention_recovery.py").read_text(
        encoding="utf-8"
    )

    assert "RECOVERY_CODE_BUNDLE_PATHS" in source
    assert 'ROOT / "scripts/watch_pilot_retention_recovery.py"' in source
    assert "watch_pilot_checkpoints.py" not in source
    assert "watch_pilot_resume_checkpoints.py" not in source
