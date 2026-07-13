from __future__ import annotations

from pathlib import Path


def test_modelscope_download_is_node_local_guarded_and_proxy_free() -> None:
    root = Path(__file__).resolve().parents[1]
    launcher = (root / "scripts/launch_node_modelscope_download.sh").read_text(
        encoding="utf-8"
    )

    assert "modelscope download --model" in launcher
    assert "/dev/shm/blind-gains/models/" in launcher
    assert "env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY" in launcher
    assert "40 * 1024 * 1024 * 1024" in launcher
    assert "refusing to overwrite node-local model" in launcher
    assert "artifact_manifest.tsv" in launcher
    assert '"m11_modelscope_node_local_download"' in launcher
