from __future__ import annotations

from pathlib import Path

from scripts.probe_ray_tempdir import TEMP_ENV_KEYS, validate_observation


def _observation(root: Path) -> dict:
    runtime = root / "tmp"
    environment = {key: str(runtime if key != "RAY_TMPDIR" else root) for key in TEMP_ENV_KEYS}
    return {
        "driver": {"tempfile": str(runtime), "multiprocessing": str(runtime / "pymp-a"), "env": environment},
        "worker": {"tempfile": str(runtime), "multiprocessing": str(runtime / "pymp-b"), "env": environment},
        "ray": {"session_dir": str(root / "ray" / "session")},
    }


def test_temp_probe_accepts_only_job_local_paths(tmp_path: Path) -> None:
    assert validate_observation(_observation(tmp_path), tmp_path) == []


def test_temp_probe_rejects_worker_multiprocessing_fallback_to_tmp(tmp_path: Path) -> None:
    observation = _observation(tmp_path)
    observation["worker"]["multiprocessing"] = "/tmp/pymp-old-failure"

    errors = validate_observation(observation, tmp_path)

    assert errors == ["worker.multiprocessing:outside_expected_root:/tmp/pymp-old-failure"]
