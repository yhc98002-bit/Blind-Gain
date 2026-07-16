from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_smoke_launcher_is_registered_guarded_single_node_and_fail_closed() -> None:
    source = (ROOT / "scripts/launch_mini_a5_plumbing_smoke.sh").read_text(
        encoding="utf-8"
    )
    assert "mini_a5_smoke_registration_marker_v1.json" in source
    assert "git merge-base --is-ancestor" in source
    assert '(.main_optimizer_steps_authorized == 0)' in source
    assert "requires eight comma-separated GPU indices" in source
    assert "tensor_parallel_width: 1" in source
    assert "replica_count: 8" in source
    assert "BLIND_GAINS_CP_RUNTIME_AUDIT=1" in source
    assert "--tier S" in source
    assert "--required-bytes 55000000000" in source
    assert "refusing Mini-A5 smoke" in source
    assert 'job_type: "m6_mini_a5_registered_plumbing_smoke"' in source
    assert "main_m6_optimizer_steps_authorized: 0" in source


def test_adversarial_dirty_or_unregistered_launch_cannot_bypass_checks() -> None:
    source = (ROOT / "scripts/launch_mini_a5_plumbing_smoke.sh").read_text(
        encoding="utf-8"
    )
    assert "git diff --quiet" in source
    assert '(.status == "registered")' in source
    assert '(.smoke_optimizer_steps_authorized_per_mode == 1)' in source
    assert "(.launcher_sha256 == $launcher_sha)" in source
    assert "isolated EasyR1 worktree patch inventory drift" in source
