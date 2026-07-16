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
