from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _short_ray_tmp_dir(run_id: str) -> str:
    command = (
        f"source {ROOT / 'scripts/lib/run_paths.sh'}; "
        f"short_ray_tmp_dir {run_id!r}"
    )
    result = subprocess.run(
        ["bash", "-c", command],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def test_ray_tmp_dir_leaves_room_for_ray_unix_socket() -> None:
    run_id = "user:node:anchor_a0_recipe_3b_geo3k_20260709T215715Z"
    tmp_dir = _short_ray_tmp_dir(run_id)
    socket = (
        Path(tmp_dir)
        / "ray"
        / "session_2026-07-10_05-57-29_140463_2763370"
        / "sockets"
        / "plasma_store"
    )

    assert tmp_dir.startswith("/tmp/bg-ray-")
    assert len(str(socket).encode()) <= 107


def test_ray_tmp_dir_is_deterministic_and_run_specific() -> None:
    assert _short_ray_tmp_dir("run-a") == _short_ray_tmp_dir("run-a")
    assert _short_ray_tmp_dir("run-a") != _short_ray_tmp_dir("run-b")
