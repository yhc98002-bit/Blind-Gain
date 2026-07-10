from pathlib import Path


def test_hf_dataset_launcher_disables_xet_and_limits_workers() -> None:
    root = Path(__file__).resolve().parents[1]
    launcher = (root / "scripts/launch_hf_dataset_download.sh").read_text(encoding="utf-8")
    assert "HF_HUB_DISABLE_XET=1" in launcher
    assert "--max-workers 2" in launcher
