from __future__ import annotations

import subprocess
from pathlib import Path

from scripts.probe_m5_ray_startup import SCHEMA_VERSION, validate_result


ROOT = Path(__file__).resolve().parents[1]


def _payload() -> dict:
    rounds = []
    for _ in range(2):
        rounds.append(
            {
                "status": "pass",
                "runtime_env_task": "m5-ray-preflight",
                "gpu_workers": [
                    {
                        "cuda_visible_devices": str(index),
                        "cuda_available": True,
                        "runtime_env_marker": "m5-ray-preflight",
                    }
                    for index in range(4)
                ],
            }
        )
    return {"schema_version": SCHEMA_VERSION, "rounds": rounds}


def test_preflight_accepts_two_fresh_four_gpu_rounds() -> None:
    assert validate_result(_payload()) == []


def test_preflight_rejects_reused_gpu_identity() -> None:
    payload = _payload()
    payload["rounds"][1]["gpu_workers"][3]["cuda_visible_devices"] = "2"
    assert validate_result(payload) == ["round_2.cuda_visible_devices_not_unique"]


def test_preflight_rejects_missing_runtime_env_agent_result() -> None:
    payload = _payload()
    payload["rounds"][0]["runtime_env_task"] = None
    assert validate_result(payload) == ["round_1.runtime_env_task"]


def test_preflight_launcher_parses_and_is_fail_closed() -> None:
    launcher = ROOT / "scripts/launch_m5_ray_startup_preflight.sh"
    subprocess.run(["bash", "-n", str(launcher)], check=True)
    source = launcher.read_text(encoding="utf-8")
    assert "--rounds 2 --timeout 120" in source
    assert "another project EasyR1 trainer is active" in source
    assert "M5 preflight needs 650 GiB host memory" in source
    assert "runtime_cleanup.json" in source
