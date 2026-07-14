from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.prepare_pilot_resume_config import ALLOWED_CHANGES, prepare_resume_config


def _source(path: Path, condition: str = "caption") -> None:
    path.write_text(
        yaml.safe_dump(
            {
                "data": {"image_condition": condition},
                "worker": {"actor": {"optim": {"lr": 1e-6}}},
                "trainer": {
                    "experiment_name": "mech_a3_caption",
                    "max_steps": 100,
                    "save_freq": 20,
                    "save_checkpoint_path": "/shared/original",
                    "load_checkpoint_path": None,
                    "find_last_checkpoint": False,
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def test_resume_changes_only_operational_checkpoint_fields(tmp_path: Path) -> None:
    source = tmp_path / "source.yaml"
    output = tmp_path / "resume.yaml"
    _source(source)

    audit = prepare_resume_config(
        source,
        output,
        experiment_name="mech_a3_caption_resume20",
        save_checkpoint_path=tmp_path / "new-output",
        load_checkpoint_path=tmp_path / "old" / "global_step_20",
        expected_step=20,
    )
    payload = yaml.safe_load(output.read_text(encoding="utf-8"))

    assert audit["status"] == "pass"
    assert set(audit["changed_fields"]).issubset(ALLOWED_CHANGES)
    assert set(audit["changed_fields"]) >= {
        "trainer.experiment_name",
        "trainer.save_checkpoint_path",
        "trainer.load_checkpoint_path",
    }
    assert audit["scientific_config_changed"] is False
    assert payload["worker"]["actor"]["optim"]["lr"] == 1e-6
    assert payload["trainer"]["load_checkpoint_path"].endswith("global_step_20")


def test_resume_rejects_wrong_checkpoint_step(tmp_path: Path) -> None:
    source = tmp_path / "source.yaml"
    _source(source)

    with pytest.raises(ValueError, match="expected resume step"):
        prepare_resume_config(
            source,
            tmp_path / "resume.yaml",
            experiment_name="resume",
            save_checkpoint_path=tmp_path / "new",
            load_checkpoint_path=tmp_path / "global_step_26",
            expected_step=20,
        )


def test_resume_accepts_registered_real_condition_when_explicit(tmp_path: Path) -> None:
    source = tmp_path / "source.yaml"
    _source(source, condition="real")

    audit = prepare_resume_config(
        source,
        tmp_path / "resume.yaml",
        experiment_name="mech_a1_real_resume60",
        save_checkpoint_path=tmp_path / "new",
        load_checkpoint_path=tmp_path / "global_step_60",
        expected_step=60,
        expected_image_condition="real",
    )

    assert audit["image_condition"] == "real"
    assert audit["resume_global_step"] == 60


def test_resume_rejects_image_condition_mismatch(tmp_path: Path) -> None:
    source = tmp_path / "source.yaml"
    _source(source, condition="real")

    with pytest.raises(ValueError, match="image condition mismatch"):
        prepare_resume_config(
            source,
            tmp_path / "resume.yaml",
            experiment_name="resume",
            save_checkpoint_path=tmp_path / "new",
            load_checkpoint_path=tmp_path / "global_step_20",
            expected_step=20,
        )
