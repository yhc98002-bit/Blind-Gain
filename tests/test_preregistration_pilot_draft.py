from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from scripts.build_preregistration_pilot_draft import (
    FALSIFICATION,
    ONE_SEED_SCOPE,
    build_draft,
)


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    config = {
        "data": {"image_condition": "real"},
        "worker": {"rollout": {"tensor_parallel_size": 1}},
        "trainer": {
            "experiment_name": "a1",
            "save_checkpoint_path": "/checkpoints/a1",
            "n_gpus_per_node": 4,
            "max_steps": 100,
            "save_freq": 20,
            "val_freq": 10,
        },
    }
    configs = {
        "mech_a1_real_3b_geo3k.yaml": ("real", "a1"),
        "mech_a2_gray_3b_geo3k.yaml": ("gray", "a2"),
        "mech_a2b_noimage_3b_geo3k.yaml": ("none", "a2b"),
        "mech_a3_caption_3b_geo3k.yaml": ("caption", "a3"),
    }
    config_dir = tmp_path / "configs/train"
    config_dir.mkdir(parents=True)
    for name, (condition, identity) in configs.items():
        payload = json.loads(json.dumps(config))
        payload["data"]["image_condition"] = condition
        payload["trainer"]["experiment_name"] = identity
        payload["trainer"]["save_checkpoint_path"] = f"/checkpoints/{identity}"
        (config_dir / name).write_text(yaml.safe_dump(payload), encoding="utf-8")

    hashes = {
        condition: str(index) * 64
        for index, condition in enumerate(
            ("real", "gray", "noise", "none", "caption"), start=1
        )
    }
    audit = {"status": "pass", "per_item_output_sha256": hashes}
    aggregates = {}
    for index, condition in enumerate(("gray", "none", "caption"), start=1):
        aggregates[condition] = {
            "train": {
                "metrics": {
                    "q_i": {
                        "mean": index / 10,
                        "ci_low": index / 10 - 0.01,
                        "ci_high": index / 10 + 0.01,
                    }
                },
                "q_i_distribution": {
                    "q25": 0.1,
                    "median": 0.2,
                    "q75": 0.3,
                },
            }
        }
    summary = {
        "status": "complete",
        "audit": audit,
        "evaluation_contract": {
            "symbolic_grader_guard_version": "posix-itimer-v1",
            "symbolic_grader_timeout_seconds": 5.0,
            "max_tokens": 2048,
            "sample_count": 16,
            "group_size": 5,
        },
        "aggregates": aggregates,
    }
    summary_path = tmp_path / "summary.json"
    audit_path = tmp_path / "audit.json"
    ids_path = tmp_path / "ids.json"
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    audit_path.write_text(json.dumps(audit), encoding="utf-8")
    ids_path.write_text("[1, 2]\n", encoding="utf-8")
    return summary_path, audit_path, ids_path


def test_draft_renders_fixed_language_and_computed_q_anchors(tmp_path: Path) -> None:
    summary, audit, ids = _fixture(tmp_path)

    text = build_draft(
        root=tmp_path,
        l7_summary_path=summary,
        l7_audit_path=audit,
        filtered_ids_path=ids,
    )

    assert ONE_SEED_SCOPE in text
    assert FALSIFICATION in text
    assert "| gray | 0.100000 | 0.090000 | 0.110000" in text
    assert "Final L12 path `reports/preregistration_pilot_v1.md`: intentionally absent" in text


def test_draft_rejects_nonpass_l7_audit(tmp_path: Path) -> None:
    summary, audit, ids = _fixture(tmp_path)
    payload = json.loads(audit.read_text(encoding="utf-8"))
    payload["status"] = "fail"
    audit.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="complete L7 summary and pass audit"):
        build_draft(
            root=tmp_path,
            l7_summary_path=summary,
            l7_audit_path=audit,
            filtered_ids_path=ids,
        )


def test_draft_rejects_behavior_drift_between_arm_configs(tmp_path: Path) -> None:
    summary, audit, ids = _fixture(tmp_path)
    path = tmp_path / "configs/train/mech_a3_caption_3b_geo3k.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["trainer"]["max_steps"] = 99
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="outside registered arm identity"):
        build_draft(
            root=tmp_path,
            l7_summary_path=summary,
            l7_audit_path=audit,
            filtered_ids_path=ids,
        )
