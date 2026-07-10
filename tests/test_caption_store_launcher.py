from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _invoke(run_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "bash",
            "scripts/launch_caption_store_shards.sh",
            "node-not-contacted",
            "0",
            "1",
            "model",
            str(run_dir / "missing_images"),
            str(run_dir),
            "0",
            "384",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_caption_store_launcher_rejects_concurrent_run_owner_before_preflight(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "run"
    (run_dir / ".launch_lock").mkdir(parents=True)

    result = _invoke(run_dir)

    assert result.returncode == 2
    assert "Another launcher owns" in result.stderr
    assert "contains no readable image files" not in result.stderr
    assert "Could not resolve hostname" not in result.stderr


def test_caption_store_launcher_refuses_initialized_run_directory(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "run_manifest.json").write_text("{}\n", encoding="ascii")

    result = _invoke(run_dir)

    assert result.returncode == 2
    assert "already initialized" in result.stderr
    assert not (run_dir / ".launch_lock").exists()
    assert "Could not resolve hostname" not in result.stderr


def test_caption_store_lock_precedes_expensive_input_hash() -> None:
    source = (ROOT / "scripts/launch_caption_store_shards.sh").read_text(encoding="utf-8")
    assert source.index('mkdir "${LAUNCH_LOCK}"') < source.index("IMAGE_HASH=")
