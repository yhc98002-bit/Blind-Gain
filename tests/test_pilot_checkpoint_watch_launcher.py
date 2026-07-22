from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts" / "launch_pilot_checkpoint_watch.sh"


def test_pilot_checkpoint_watch_launcher_is_valid_shell() -> None:
    subprocess.run(["bash", "-n", str(LAUNCHER)], check=True)


def test_pilot_checkpoint_watch_launcher_pins_retention_and_step60_barrier() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")

    assert 'intermediate_steps: [20, 40, 60, 80]' in source
    assert "final_shared_step: 100" in source
    assert "step60_fliptrack_complete.json" in source
    assert "step60_geo3k_complete.json" in source
    assert "--step60-evaluation-marker" in source
    assert "--step60-geo3k-marker" in source
    assert "pilot_code_bundle_hash" in source
    assert 'ARCHIVE_ROOT="/tmp/blindgain_checkpoint_archive/${PARENT_RUN_ID}"' in source


def test_pilot_checkpoint_watch_refuses_nonpilot_parent_before_tmux() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    parent_guard = source.index('!= "l13_mechanical_pilot_arm"')
    tmux_launch = source.index("tmux new-session")

    assert parent_guard < tmux_launch
