from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_caption_launcher_rejects_token_budget_in_gpu_position(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            "bash",
            "scripts/launch_fliptrack_caption_shards.sh",
            "an29",
            "0",
            "2",
            "model",
            "manifest",
            str(tmp_path / "run"),
            "384",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert "GPU_LIST" in result.stderr


def test_caption_qa_launcher_rejects_invalid_gpu_list(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            "bash",
            "scripts/launch_caption_qa_shards.sh",
            "an29",
            "0",
            "2",
            "model",
            "caption-run",
            str(tmp_path / "qa-run"),
            "8",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert "GPU_LIST" in result.stderr
