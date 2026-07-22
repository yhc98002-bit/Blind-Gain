from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts" / "launch_pilot_seed2_readout_queue.sh"


def test_launcher_serializes_before_scanning_or_creating_run_directory() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")

    lock = source.index("flock -n 9")
    active_scan = source.index("find experiments/runs")
    run_id = source.index('RUN_ID="pilot_4arm_seed2_readout_queue')
    assert lock < active_scan < run_id


def test_launcher_keeps_unified_outputs_immutable() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")

    assert '[[ ! -e "${JSON_OUTPUT}" && ! -e "${MARKDOWN_OUTPUT}" ]]' in source
    assert "performance_values_opened: false" in source
    assert "performance_values_opened_only_after_complete_lifecycle" in (
        ROOT / "scripts" / "run_pilot_fourarm_readout_queue.py"
    ).read_text(encoding="utf-8")
