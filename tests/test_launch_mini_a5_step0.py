from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_step0_launcher_is_single_gpu_inference_only_and_manifested() -> None:
    source = (ROOT / "scripts" / "launch_mini_a5_step0.sh").read_text(
        encoding="utf-8"
    )
    assert 'NODE="${NODE:-an12}"' in source
    assert 'GPU="${GPU:-7}"' in source
    assert 'job_type: "m6_mini_a5_step0_base_reward_diagnostic"' in source
    assert "tensor_parallel_width: 1" in source
    assert "replica_count: 1" in source
    assert "optimizer_steps: 0" in source
    assert "scripts/run_mini_a5_step0.py" in source
    assert "verl.trainer.main" not in source
    assert "scripts/storage_guard.py" in source
    assert "--required-bytes 2147483648" in source
    assert "--max-tokens 2048" not in source  # The runner pins this internally.
    assert "--seed 20260716" in source
