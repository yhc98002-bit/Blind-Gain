from __future__ import annotations

import subprocess
from pathlib import Path

from scripts.watch_pilot_resume60_checkpoints import RESUME60_STEPS, relocation_plan


ROOT = Path(__file__).resolve().parents[1]


def test_resume60_watcher_only_handles_future_checkpoints() -> None:
    assert RESUME60_STEPS == (80, 100)
    assert relocation_plan() == {
        80: "relocate_after_merge",
        100: "retain_final_on_shared",
    }


def test_resume60_watcher_launcher_is_fail_closed() -> None:
    path = ROOT / "scripts" / "launch_pilot_resume60_checkpoint_watch.sh"
    subprocess.run(["bash", "-n", str(path)], check=True)
    source = path.read_text(encoding="utf-8")
    assert '"$(jq -r \'.resumed_from_global_step\'' in source
    assert '"a1_real" || "${ARM}" == "a2_gray"' in source
    assert "resume_schedule: [80,100]" in source
    assert "step60-evaluation-marker" not in source
