from __future__ import annotations

import json
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


def test_caption_store_launcher_rejects_live_resume_run_before_ssh(tmp_path: Path) -> None:
    images = tmp_path / "images"
    images.mkdir()
    (images / "image.bin").write_bytes(b"image")
    resume = tmp_path / "resume"
    (resume / "shards").mkdir(parents=True)
    (resume / "run_manifest.json").write_text(
        json.dumps(
            {
                "status": "running",
                "job_type": "caption_image_store_generation",
                "model_path": "model",
                "data_manifest": str(images),
                "expected_shards": 1,
                "max_new_tokens": 384,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    target = tmp_path / "target"

    result = subprocess.run(
        [
            "bash",
            "scripts/launch_caption_store_shards.sh",
            "node-not-contacted",
            "0",
            "1",
            "model",
            str(images),
            str(target),
            "0",
            "384",
            str(resume),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "does not match or is not failed" in result.stderr
    assert "Could not resolve hostname" not in result.stderr


def test_caption_store_launcher_records_failed_run_resume_provenance(tmp_path: Path) -> None:
    images = tmp_path / "images"
    images.mkdir()
    (images / "image.bin").write_bytes(b"image")
    resume = tmp_path / "resume"
    shards = resume / "shards"
    shards.mkdir(parents=True)
    (shards / "store_shard_0.jsonl.partial").write_text("partial\n", encoding="utf-8")
    (resume / "run_manifest.json").write_text(
        json.dumps(
            {
                "status": "fail",
                "job_type": "caption_image_store_generation",
                "model_path": "model",
                "data_manifest": str(images),
                "expected_shards": 1,
                "max_new_tokens": 384,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    target = tmp_path / "target"

    result = subprocess.run(
        [
            "bash",
            "scripts/launch_caption_store_shards.sh",
            "node-not-contacted",
            "0",
            "1",
            "model",
            str(images),
            str(target),
            "0",
            "384",
            str(resume),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    manifest = json.loads((target / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["resume_from_run"] == str(resume)
    assert manifest["resume_source_hash"]
    assert str(resume) in manifest["command"]
