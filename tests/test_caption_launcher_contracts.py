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


def test_image_eval_launcher_rejects_mapping_that_launches_zero_workers(tmp_path: Path) -> None:
    manifest = tmp_path / "input.jsonl"
    manifest.write_text('{"pair_id":"p"}\n', encoding="utf-8")
    result = subprocess.run(
        [
            "bash",
            "scripts/launch_fliptrack_eval_shards.sh",
            "an29",
            "0",
            "1",
            "model",
            str(manifest),
            str(tmp_path / "run"),
            "64",
            "1",
            "real",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert "No evaluation workers launched" in result.stderr
