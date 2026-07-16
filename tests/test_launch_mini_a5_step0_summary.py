from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_summary_launcher_is_fail_closed_and_recomputes_rewards() -> None:
    source = (ROOT / "scripts" / "launch_mini_a5_step0_summary.sh").read_text(
        encoding="utf-8"
    )
    assert '.optimizer_steps == 0' in source
    assert '"$(wc -l < "${PREDICTIONS}")" -eq 1920' in source
    assert "scripts/summarize_mini_a5_step0.py" in source
    assert "src/rewards/cp_grpo_reward.py" in source
    assert "scripts/storage_guard.py" in source
    assert "source_performance_values_opened_by_launcher: false" in source
    assert 'job_type: "m6_mini_a5_step0_summary_audit"' in source
