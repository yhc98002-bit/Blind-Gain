from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts/launch_pilot_step60_eval_restore.sh"


def test_step60_restore_launcher_is_valid_shell() -> None:
    subprocess.run(["bash", "-n", str(LAUNCHER)], check=True)


def test_step60_restore_launcher_is_hash_bound_and_non_destructive() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")

    assert "restore_pilot_step60_merged.py" in source
    assert "merged_checkpoint.source.sha256" in source
    assert "MERGED_CHECKPOINT_RELOCATED.json" in source
    assert "step60_fliptrack_complete.json" in source
    assert "archive is preserved" in source
    assert "rm -" not in source
