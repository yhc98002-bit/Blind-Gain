from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_m5_integrity_launcher_is_single_node_and_non_preemptive() -> None:
    source = (ROOT / "scripts/launch_m5_anchor_integrity.sh").read_text(
        encoding="utf-8"
    )

    assert "M5 integrity requires four unique GPU ids" in source
    assert "selected GPUs did not remain free" in source
    assert "kill -0" in source
    assert "kill -9" not in source
    assert 'tensor_parallel_width: 2' in source
    assert 'replica_count: 2' in source
    assert "m5_anchor_resume_integrity_step101.yaml" in source


def test_m5_integrity_queue_waits_for_two_stable_polls() -> None:
    source = (ROOT / "scripts/run_m5_integrity_queue.py").read_text(encoding="utf-8")

    assert "streaks[node][gpu] >= 2" in source
    assert '["an12", "an29"]' in source
    assert "scripts/launch_m5_anchor_integrity.sh" in source
    assert "scripts/audit_m5_resume_integrity.py" in source
    assert "os.kill" not in source
