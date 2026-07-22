from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_queue_launcher_is_gpu_inert_registered_and_no_peek() -> None:
    source = (ROOT / "scripts/launch_mini_a5_smoke_queue.sh").read_text(
        encoding="utf-8"
    )
    assert 'job_type: "m6_registered_smoke_priority_queue"' in source
    assert "pilot_seed2_queue_login_20260716T164718Z" in source
    assert "m11_reconciled_backfill_login_20260716T172041Z" in source
    assert "m5_anchor_longhorizon_400_an12_20260716T173030Z" in source
    assert 'performance_values_opened: false' in source
    assert "main_optimizer_steps_authorized: 0" in source
    assert "refusing duplicate Mini-A5 smoke queue" in source


def test_smoke_queue_v2_binds_current_structural_dependencies() -> None:
    source = (ROOT / "scripts/launch_mini_a5_smoke_queue_v2.sh").read_text(
        encoding="utf-8"
    )

    assert "sealed-seed2-lifecycle-manifest" in source
    assert "pilot_followup_evaluation_recovery_lifecycle" in source
    assert "m11_reconciled_final_report_login_20260718T153539Z" in source
    assert "m5_anchor_longhorizon_400_resume150_an12_20260721T160431Z" in source
    assert 'preferred_child_node: "an29"' in source
    assert "child_gpu_count: 8" in source
    assert "main_optimizer_steps_authorized: 0" in source
    assert "smoke_optimizer_steps_authorized_per_arm: 1" in source
    assert 'job_type: "m6_registered_smoke_priority_queue_v3"' in source
