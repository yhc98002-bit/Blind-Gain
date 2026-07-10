from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


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


def test_image_eval_launcher_rejects_negative_shard_mapping_before_ssh(tmp_path: Path) -> None:
    manifest = tmp_path / "input.jsonl"
    manifest.write_text('{"pair_id":"p"}\n', encoding="utf-8")
    result = subprocess.run(
        [
            "bash",
            "scripts/launch_fliptrack_eval_shards.sh",
            "host-that-must-not-be-contacted",
            "-2",
            "1",
            "model",
            str(manifest),
            str(tmp_path / "negative-run"),
            "64",
            "0",
            "real",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert "No evaluation workers launched" in result.stderr
    assert "Could not resolve hostname" not in result.stderr


@pytest.mark.parametrize(
    "launcher",
    [
        "launch_fliptrack_eval_shards.sh",
        "launch_fliptrack_caption_shards.sh",
        "launch_caption_qa_shards.sh",
        "launch_caption_store_shards.sh",
    ],
)
def test_sharded_launchers_reject_negative_indices_and_use_remote_finalizer(launcher: str) -> None:
    source = (ROOT / "scripts" / launcher).read_text(encoding="utf-8")
    assert '"${SHARD_INDEX}" -lt 0' in source
    assert 'scripts/launch_remote_sharded_finalizer.sh "${NODE}"' in source


def test_remote_finalizer_is_started_on_compute_node() -> None:
    source = (ROOT / "scripts/launch_remote_sharded_finalizer.sh").read_text(encoding="utf-8")
    assert 'ssh "${NODE}"' in source
    assert "scripts/finalize_sharded_run.py" in source


def test_caption_store_launcher_hashes_symlink_targets() -> None:
    source = (ROOT / "scripts/launch_caption_store_shards.sh").read_text(encoding="utf-8")
    assert 'find -L "${IMAGE_DIR}" -type f' in source
