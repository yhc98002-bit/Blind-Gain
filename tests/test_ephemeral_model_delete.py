from pathlib import Path

import pytest

from scripts.delete_ephemeral_model import validate_deletion_contract


def _manifests(model_path: Path) -> tuple[dict, dict, dict]:
    download = {
        "run_id": "download-run",
        "status": "complete",
        "node": "an29",
        "local_path": str(model_path),
    }
    checkout = {"status": "pass", "local_path": str(model_path)}
    caption = {
        "status": "complete",
        "node": "an29",
        "model_path": str(model_path),
        "model_download_run": "download-run",
    }
    return download, checkout, caption


def test_deletion_contract_requires_completed_matching_caption_run(tmp_path: Path) -> None:
    download, checkout, caption = _manifests(tmp_path / "model")

    assert validate_deletion_contract(
        download,
        checkout,
        caption,
        expected_node="an29",
        require_memory_path=False,
    ) == tmp_path / "model"

    caption["status"] = "running"
    with pytest.raises(ValueError, match="caption_complete"):
        validate_deletion_contract(
            download,
            checkout,
            caption,
            expected_node="an29",
            require_memory_path=False,
        )


def test_deletion_contract_rejects_shared_or_cross_node_path() -> None:
    model_path = Path("/XYFS02/HDD_POOL/model")
    download, checkout, caption = _manifests(model_path)
    with pytest.raises(ValueError, match="model_path_ephemeral"):
        validate_deletion_contract(
            download,
            checkout,
            caption,
            expected_node="an29",
        )
    download["local_path"] = "/dev/shm/blind-gains/model"
    checkout["local_path"] = download["local_path"]
    caption["model_path"] = download["local_path"]
    caption["node"] = "an12"
    with pytest.raises(ValueError, match="caption_node_exact"):
        validate_deletion_contract(
            download,
            checkout,
            caption,
            expected_node="an29",
        )


def test_deletion_launcher_requires_predelete_and_final_records() -> None:
    launcher = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "launch_ephemeral_model_delete.sh"
    ).read_text(encoding="utf-8")

    assert "predelete_record.json" in launcher
    assert "deletion_record.json" in launcher
    assert 'job_type: "l9_ephemeral_model_deletion"' in launcher
    assert "gpu_ids: []" in launcher
    assert "setsid" in launcher
