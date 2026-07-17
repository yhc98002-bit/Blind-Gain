from __future__ import annotations

import subprocess
import stat
from pathlib import Path

from scripts.run_support_sharpening_queue import ARMS, free_allowed_gpus


ROOT = Path(__file__).resolve().parents[1]


def test_queue_capacity_filter_does_not_treat_loaded_idle_gpu_as_free() -> None:
    snapshot = {
        index: {"memory_mib": 0, "utilization_pct": 0} for index in range(8)
    }
    snapshot[5] = {"memory_mib": 19000, "utilization_pct": 0}
    snapshot[6] = {"memory_mib": 0, "utilization_pct": 11}

    assert free_allowed_gpus(snapshot, (5, 6)) == []


def test_queue_is_pinned_away_from_seed2_node_and_covers_four_arms() -> None:
    launcher = ROOT / "scripts/launch_support_sharpening_queue.sh"
    source = launcher.read_text(encoding="utf-8")
    result = subprocess.run(
        ["bash", "-n", str(launcher)], capture_output=True, text=True, check=False
    )

    assert result.returncode == 0, result.stderr
    assert launcher.stat().st_mode & stat.S_IXUSR
    assert "--node an12 --allowed-gpus 5,6" in source
    assert "an29" not in source
    assert set(ARMS) == {"a1_real", "a2_gray", "a2b_noimage", "a3_caption"}
