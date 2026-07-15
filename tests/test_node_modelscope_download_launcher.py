from __future__ import annotations

from pathlib import Path

import subprocess


def test_modelscope_download_is_node_local_guarded_and_proxy_free() -> None:
    root = Path(__file__).resolve().parents[1]
    launcher = (root / "scripts/launch_node_modelscope_download.sh").read_text(
        encoding="utf-8"
    )

    assert "modelscope download --model" in launcher
    assert "/dev/shm/blind-gains/models/" in launcher
    assert "/tmp/blind-gains/models/" in launcher
    assert "login|an12|an29" in launcher
    assert "env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY" in launcher
    assert "40 * 1024 * 1024 * 1024" in launcher
    assert "refusing to overwrite node-local model" in launcher
    assert "artifact_manifest.tsv" in launcher
    assert '"m11_modelscope_node_local_download"' in launcher
    assert "nohup setsid" in launcher
    assert "logs/wrapper.log" in launcher


def test_ephemeral_stage_is_guarded_manifest_verified_and_fail_closed() -> None:
    root = Path(__file__).resolve().parents[1]
    launcher = (root / "scripts/launch_ephemeral_model_stage.sh").read_text(
        encoding="utf-8"
    )

    assert "m11_ephemeral_model_stage" in launcher
    assert "/tmp/blind-gains/models/" in launcher
    assert "/dev/shm/blind-gains/models/" in launcher
    assert "40 * 1024 * 1024 * 1024" in launcher
    assert "refusing to overwrite node-local model or partial" in launcher
    assert "source download run is not complete" in launcher
    assert "sha256sum -c -" in launcher
    assert "rsync -a --partial" in launcher
    assert "nohup setsid" in launcher
    assert 'tensor_parallel_width: null' in launcher


def test_shared_model_stage_rejects_released_node_before_source_or_remote_work() -> None:
    root = Path(__file__).resolve().parents[1]
    launcher = root / "scripts/launch_shared_model_stage.sh"
    result = subprocess.run(
        ["bash", str(launcher), "missing", "revision", "an21", "model"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "permanent node" in result.stderr


def test_shared_model_stage_is_atomic_guarded_and_hash_verified() -> None:
    root = Path(__file__).resolve().parents[1]
    launcher = root / "scripts/launch_shared_model_stage.sh"
    subprocess.run(["bash", "-n", str(launcher)], check=True)
    source = launcher.read_text(encoding="utf-8")

    assert "artifacts/models" in source
    assert "40 * 1024 * 1024 * 1024" in source
    assert "refusing to overwrite node-local model or partial" in source
    assert "sha256sum -c -" in source
    assert "rsync -a --partial" in source
    assert "mv '${PARTIAL}' '${DESTINATION}'" in source
    assert 'tensor_parallel_width: null' in source
    assert "nohup setsid" in source
