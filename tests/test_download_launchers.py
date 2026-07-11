from pathlib import Path


def test_hf_dataset_launcher_disables_xet_and_limits_workers() -> None:
    root = Path(__file__).resolve().parents[1]
    launcher = (root / "scripts/launch_hf_dataset_download.sh").read_text(encoding="utf-8")
    assert "HF_HUB_DISABLE_XET=1" in launcher
    assert "--max-workers 2" in launcher
    assert "BLIND_GAINS_DOWNLOAD_EXPECTED_BYTES:?" in launcher
    assert "scripts/storage_guard.py" in launcher
    assert "--operation hf_dataset_download" in launcher


def test_model_download_requires_budget_and_guards_before_snapshot_download() -> None:
    root = Path(__file__).resolve().parents[1]
    launcher = (root / "scripts" / "launch_modelscope_model_download.sh").read_text(encoding="utf-8")
    downloader = (root / "scripts" / "download_modelscope_model.py").read_text(encoding="utf-8")
    assert "BLIND_GAINS_DOWNLOAD_EXPECTED_BYTES:?" in launcher
    assert "--storage-tier" in launcher
    assert "--expected-bytes" in launcher
    assert downloader.index("check_storage(") < downloader.index("snapshot_download(")


def test_modelscope_lfs_pull_requires_budget_and_storage_guard() -> None:
    root = Path(__file__).resolve().parents[1]
    launcher = (root / "scripts" / "launch_modelscope_lfs_pull.sh").read_text(encoding="utf-8")
    assert "BLIND_GAINS_DOWNLOAD_EXPECTED_BYTES:?" in launcher
    assert "--operation modelscope_lfs_pull" in launcher
