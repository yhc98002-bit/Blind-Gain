from __future__ import annotations

import subprocess
from pathlib import Path

from scripts.execute_m5_step200_handoff import recent_memory_slope


ROOT = Path(__file__).resolve().parents[1]


def test_m5_step200_handoff_memory_slope() -> None:
    rows = [(step, 50.0 + 7.5 * step) for step in range(10)]
    assert recent_memory_slope(rows) == 7.5


def test_m5_step200_handoff_signals_only_after_evidence_and_recheck() -> None:
    source = (ROOT / "scripts/execute_m5_step200_handoff.py").read_text(
        encoding="utf-8"
    )
    boundary = source.index("boundary = validate_step200(")
    intent = source.index('"handoff_intent.json"')
    repeated = source.index("repeated = process_identity(")
    signal = source.index("_ssh(args.node, f\"kill -INT")
    assert boundary < intent < repeated < signal
    assert "SIGKILL" not in source
    assert 'target_counts != [8, 14]' in source


def test_m5_step200_handoff_launcher_parses_and_pins_source() -> None:
    launcher = ROOT / "scripts/launch_m5_step200_handoff.sh"
    subprocess.run(["bash", "-n", str(launcher)], check=True)
    source = launcher.read_text(encoding="utf-8")
    assert "m5_anchor_longhorizon_400_resume150_an12_20260721T160431Z" in source
    assert "git diff --quiet HEAD" in source
    assert "--slope-threshold 2.0" in source
    assert "--available-threshold-gib 350" in source
