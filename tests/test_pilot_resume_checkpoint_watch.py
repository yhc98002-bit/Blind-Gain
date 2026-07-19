from __future__ import annotations

import subprocess
from pathlib import Path

from scripts.watch_pilot_resume_checkpoints import RESUME_STEPS, relocation_plan


ROOT = Path(__file__).resolve().parents[1]


def test_resume_watcher_starts_at_next_registered_checkpoint() -> None:
    assert RESUME_STEPS == (40, 60, 80, 100)
    assert relocation_plan() == {
        40: "relocate_after_merge",
        60: "relocate_after_registered_evaluation",
        80: "relocate_after_merge",
        100: "retain_final_on_shared",
    }


def test_resume_watcher_launcher_is_valid_and_fail_closed() -> None:
    path = ROOT / "scripts/launch_pilot_resume_checkpoint_watch.sh"
    subprocess.run(["bash", "-n", str(path)], check=True)
    source = path.read_text(encoding="utf-8")
    assert '"$(jq -r \'.resumed_from_global_step\'' in source
    assert '[[ "${RUN_LABEL}" == "${SOURCE_RUN_NAME}_resume20" ]]' in source
    assert '"${ARM}" == "a2_gray"' in source
    assert '"${ARM}" == "a2b_noimage"' in source
    assert "resume_schedule: [40,60,80,100]" in source
