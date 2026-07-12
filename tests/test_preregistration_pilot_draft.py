from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pytest
import yaml

from scripts.build_preregistration_pilot_draft import (
    CHART_CONSTRUCT,
    EXECUTION_ACCESS_DISCLOSURE,
    FALSIFICATION,
    ONE_SEED_SCOPE,
    PRIOR_OBSERVATION_DISCLOSURE,
    R20_CAVEAT,
    build_draft,
)


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    config = {
        "data": {
            "image_condition": "real",
            "train_files": "data/geo3k_pilot_filtered.jsonl",
            "val_files": "hiyouga/geometry3k@test",
        },
        "worker": {
            "actor": {"model": {"freeze_vision_tower": True}},
            "rollout": {"tensor_parallel_size": 1},
            "reward": {"reward_function": "pilot_reward.py:compute_score"},
        },
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

    hashes = {}
    runs = {}
    for condition in ("real", "gray", "noise", "none", "caption"):
        run = tmp_path / "experiments" / "runs" / f"l7_{condition}"
        run.mkdir(parents=True)
        per_item = run / "per_item.jsonl"
        q_floor = 0.13865898995462222
        q_above = 0.369888261634798
        rows = [
            {
                "condition": condition,
                "split": "train",
                "row_index": index,
                "sample_count": 16,
                "sample_correct_count": count,
                "q_i": q_floor if count in {0, 16} else q_above,
            }
            for index, count in enumerate((0, 0, 1, 16))
        ]
        per_item.write_text(
            "".join(f"{json.dumps(row)}\n" for row in rows), encoding="utf-8"
        )
        hashes[condition] = hashlib.sha256(per_item.read_bytes()).hexdigest()
        runs[condition] = str(run.relative_to(tmp_path))
    audit = {
        "status": "pass",
        "per_item_output_sha256": hashes,
        "runs": runs,
    }
    aggregates = {}
    for index, condition in enumerate(("real", "gray", "none", "caption"), start=1):
        aggregates[condition] = {
            "train": {
                "metrics": {
                    "q_i": {
                        "mean": index / 10,
                        "ci_low": index / 10 - 0.01,
                        "ci_high": index / 10 + 0.01,
                    }
                },
                "n": 4,
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

    reports = tmp_path / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "grpo_anchor_step100_prepost_v1.json").write_text(
        json.dumps(
            {
                "status": "pass",
                "splits": {
                    "test": {
                        "metrics": {
                            "pilot_accuracy": {
                                "before": 0.14975,
                                "after": 0.43594,
                                "delta": 0.28619,
                                "delta_ci_low": 0.24459,
                                "delta_ci_high": 0.32779,
                            }
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    (reports / "anchor_step100_fliptrack_r19_v2.json").write_text(
        json.dumps(
            {
                "status": "pass",
                "comparison": {
                    "all": {
                        "base_pair_accuracy": 0.56167,
                        "step100_pair_accuracy": 0.56333,
                        "pair_delta": 0.00167,
                        "pair_delta_ci95": [-0.01833, 0.02085],
                    },
                    "geometry_coordinate_register_twenty_point_x_v02": {
                        "base_pair_accuracy": 0.47167,
                        "step100_pair_accuracy": 0.48,
                        "pair_delta": 0.00833,
                        "pair_delta_ci95": [-0.01833, 0.03667],
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    (reports / "anchor_step100_fliptrack_r19_blind_ablation_v2.json").write_text(
        json.dumps(
            {
                "status": "pass",
                "endpoints": {
                    "anchor_gray": {"pair_accuracy": 0.0, "collapse_rate": 1.0},
                    "anchor_noise": {"pair_accuracy": 0.0, "collapse_rate": 1.0},
                },
            }
        ),
        encoding="utf-8",
    )
    false_floor = {
        "3b_real_at_least_0_40": False,
        "3b_real_at_most_0_90": True,
        "3b_caption_at_most_0_15": True,
        "7b_caption_at_most_0_15": True,
        "3b_gray_at_most_0_05": True,
        "3b_noise_at_most_0_05": True,
        "7b_gray_at_most_0_05": True,
        "7b_noise_at_most_0_05": True,
        "3b_degradation_curve_nonincreasing": True,
        "real_accuracy_increases_3b_to_7b": True,
    }
    (reports / "fliptrack_r20_confirmatory.json").write_text(
        json.dumps(
            {
                "status": "pass",
                "template_results": {
                    "coordinate_register_twenty_point_x_v02": {
                        "automated_outcome": "downgrade-to-R19-selected",
                        "checks": false_floor,
                        "pair_accuracy": {"3b_real": 0.39667},
                    },
                    "starred_series_value_nine_v07": {
                        "automated_outcome": "downgrade-to-R19-selected",
                        "checks": false_floor,
                        "pair_accuracy": {"3b_real": 0.39},
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    (reports / "fliptrack_v02r19_human_audit.md").write_text(
        "verdict=accepted\nauditor=Richard\n60/60 pairs passed\n", encoding="utf-8"
    )
    anchor_config = (
        tmp_path
        / "checkpoints/anchor_a0_recipe_3b_geo3k"
        / "anchor_a0_recipe_3b_geo3k_20260709T224852Z"
        / "experiment_config.json"
    )
    anchor_config.parent.mkdir(parents=True)
    anchor_config.write_text(
        json.dumps(
            {
                "data": {
                    "train_files": "hiyouga/geometry3k@train",
                    "val_files": "hiyouga/geometry3k@test",
                },
                "worker": {
                    "actor": {"model": {"freeze_vision_tower": False}},
                    "rollout": {"tensor_parallel_size": 2},
                    "reward": {"reward_function_kwargs": {}},
                },
            }
        ),
        encoding="utf-8",
    )
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
    assert PRIOR_OBSERVATION_DISCLOSURE in text
    assert R20_CAVEAT in text
    assert CHART_CONSTRUCT in text
    assert EXECUTION_ACCESS_DISCLOSURE in text
    assert "PRIMARY mechanism analysis" in text
    assert "hurdle contrast" in text
    assert "Secondary: tie-corrected Spearman" in text
    assert "restricted to `c_i > 0`" in text
    assert "directly observed latent" in text
    assert "| gray | 4 | 2 | 0.5000 | 2 | 0.5000 | 0.200000 |" in text
    assert "q_i-quartile" not in text
    assert "cued chart point-value reading" in text
    assert "partially informed" in text
    assert "present unchanged at Git `HEAD`" in text
    assert "no pilot optimizer step has run" in text
    assert "PENDING_RICHARD_MERGE" in text
    assert "PI 1 approval" not in text
    assert "Final M0 path `reports/preregistration_pilot_v1.md`: intentionally absent" in text
    assert "| caption q≈real AND zero-bit q substantial" in text
    assert "0.9156 canonical-v2/native agreement rate is context" in text
    assert "No post-hoc R19-minus-chart composite" in text


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


def test_draft_rejects_unrecorded_human_audit(tmp_path: Path) -> None:
    summary, audit, ids = _fixture(tmp_path)
    (tmp_path / "reports/fliptrack_v02r19_human_audit.md").write_text(
        "verdict=pending\n", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="human audit acceptance"):
        build_draft(
            root=tmp_path,
            l7_summary_path=summary,
            l7_audit_path=audit,
            filtered_ids_path=ids,
        )
