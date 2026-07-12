from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.relocate_legacy_smoke_metadata import relocate_metadata


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    run_id = "pilot_reward_smoke_an29_fixture"
    run_dir = tmp_path / "experiments" / "runs" / run_id
    run_dir.mkdir(parents=True)
    manifest = run_dir / "run_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "job_type": "l3_pilot_reward_plumbing_smoke",
                "status": "complete",
                "exit_code": 0,
            }
        ),
        encoding="utf-8",
    )
    source = tmp_path / "checkpoints" / "pilot" / "mech_a1_real"
    source.mkdir(parents=True)
    (source / "checkpoint_tracker.json").write_text("{}\n", encoding="utf-8")
    (source / "experiment_config.json").write_text(
        json.dumps(
            {
                "trainer": {"experiment_name": run_id, "max_steps": 5},
                "worker": {"rollout": {"tensor_parallel_size": 2}},
            }
        ),
        encoding="utf-8",
    )
    (source / "experiment_log.jsonl").write_text('{"step": 5}\n', encoding="utf-8")
    (source / "generations.log").write_text("generation\n", encoding="utf-8")
    return source, run_dir / "legacy_checkpoint_metadata", manifest


def test_relocation_verifies_and_clears_future_pilot_namespace(tmp_path: Path) -> None:
    source, destination, manifest = _fixture(tmp_path)

    result = relocate_metadata(source, destination, manifest)

    assert result["status"] == "relocated"
    assert result["classification"] == "superseded"
    assert result["file_count"] == 4
    assert not source.exists()
    assert (destination / "source.sha256").is_file()
    assert json.loads((destination / "relocation.json").read_text())["status"] == "relocated"
    run = json.loads(manifest.read_text(encoding="utf-8"))
    assert run["storage_retention_events"][0]["status"] == "superseded-metadata-relocated"


def test_relocation_rejects_unrelated_experiment_without_removal(tmp_path: Path) -> None:
    source, destination, manifest = _fixture(tmp_path)
    config_path = source / "experiment_config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["trainer"]["experiment_name"] = "different-run"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    with pytest.raises(ValueError, match="experiment name"):
        relocate_metadata(source, destination, manifest)

    assert source.is_dir()
    assert not destination.exists()
