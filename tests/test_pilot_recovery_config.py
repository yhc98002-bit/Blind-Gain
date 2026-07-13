from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.prepare_pilot_recovery_config import prepare_recovery_config


def test_recovery_config_changes_only_operational_output_identity(tmp_path: Path) -> None:
    source = tmp_path / "source.yaml"
    source_payload = {
        "data": {"image_condition": "none", "seed": 1},
        "worker": {"rollout": {"n": 5}},
        "trainer": {
            "experiment_name": "mech_a2b_noimage",
            "save_checkpoint_path": "/shared/original",
            "load_checkpoint_path": "/unexpected/resume",
            "find_last_checkpoint": True,
            "max_steps": 100,
        },
    }
    source.write_text(yaml.safe_dump(source_payload), encoding="utf-8")
    output = tmp_path / "effective.yaml"

    prepare_recovery_config(
        source,
        output,
        experiment_name="mech_a2b_noimage_retry1",
        checkpoint_path=tmp_path / "retry1",
    )

    recovered = yaml.safe_load(output.read_text())
    assert recovered["data"] == source_payload["data"]
    assert recovered["worker"] == source_payload["worker"]
    assert recovered["trainer"]["max_steps"] == 100
    assert recovered["trainer"]["experiment_name"] == "mech_a2b_noimage_retry1"
    assert recovered["trainer"]["save_checkpoint_path"] == str(
        (tmp_path / "retry1").resolve()
    )
    assert recovered["trainer"]["load_checkpoint_path"] is None
    assert recovered["trainer"]["find_last_checkpoint"] is False

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        prepare_recovery_config(
            source,
            output,
            experiment_name="mech_a2b_noimage_retry1",
            checkpoint_path=tmp_path / "retry1",
        )
