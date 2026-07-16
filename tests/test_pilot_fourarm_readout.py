from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts import build_pilot_4arm_seed1_readout as builder
from src.analysis.pilot_fourarm import (
    floor_and_tail_deciles,
    hurdle_summary,
    paired_difference,
    tied_spearman,
)


def test_missing_arm_fails_before_any_scientific_row_is_opened(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = {
        "schema_version": builder.CONFIG_SCHEMA_VERSION,
        "seed": 1,
        "bootstrap_draws": 5000,
        "training_runs": {arm: "missing" for arm in builder.ARMS[:-1]},
        "geo_baselines": {arm: "missing" for arm in builder.ARMS},
        "geo_audits": {arm: "missing" for arm in builder.ARMS},
        "r19_markers": {
            arm: {"60": "missing", "100": "missing"} for arm in builder.ARMS
        },
        "r19_base_run": "missing",
    }
    monkeypatch.setattr(
        builder,
        "_read_jsonl",
        lambda _path: pytest.fail("scientific row opened before four-arm preflight"),
    )

    with pytest.raises(ValueError, match="exactly all four registered arms"):
        builder.build_readout(
            config,
            root=tmp_path,
            artifact_dir=tmp_path / "artifacts",
        )


def test_paired_difference_uses_item_level_changes() -> None:
    summary = paired_difference(
        [False, False, True, True],
        [True, False, True, False],
        draws=500,
        seed=7,
    )

    assert summary["estimate"] == 0.0
    assert summary["n"] == 4
    assert summary["ci95"][0] <= 0 <= summary["ci95"][1]


def test_tied_spearman_uses_midranks_and_reports_degenerate_gain() -> None:
    assert tied_spearman([0.1, 0.1, 0.4, 0.9], [-1, -1, 0, 1]) == pytest.approx(1.0)
    assert tied_spearman([0.1, 0.2, 0.3], [0, 0, 0]) is None


def test_hurdle_and_tail_table_preserve_registered_floor() -> None:
    rows = [
        {"sample_correct_count": 0, "q_i": 0.138659, "gain": 0.0, "row_index": 0},
        {"sample_correct_count": 0, "q_i": 0.138659, "gain": -1.0, "row_index": 1},
    ]
    rows.extend(
        {
            "sample_correct_count": index + 1,
            "q_i": 0.2 + index / 100,
            "gain": 1.0,
            "row_index": index + 2,
        }
        for index in range(20)
    )

    hurdle = hurdle_summary(
        [row["sample_correct_count"] for row in rows],
        [row["gain"] for row in rows],
        draws=500,
        seed=11,
    )
    table = floor_and_tail_deciles(rows)

    assert hurdle["floor_n"] == 2
    assert hurdle["above_floor_n"] == 20
    assert hurdle["estimate"] == pytest.approx(1.5)
    assert table[0]["group"] == "floor_c0"
    assert table[0]["n"] == 2
    assert [row["n"] for row in table[1:]] == [2] * 10


def _resource_fixture(
    root: Path, *, gap_arm: str | None = None, mismatch_arm: str | None = None
) -> dict[str, dict]:
    resolved: dict[str, dict] = {}
    for arm in builder.ARMS:
        config = {
            "data": {
                "train_files": "data/frozen.jsonl",
                "max_prompt_length": 2048,
                "max_response_length": 2048,
                "rollout_batch_size": 512,
                "seed": 1,
                "min_pixels": 262144,
                "max_pixels": 4194304,
                "image_condition": builder.CONDITIONS[arm],
            },
            "algorithm": {
                "adv_estimator": "grpo",
                "disable_kl": False,
                "use_kl_loss": True,
                "kl_penalty": "low_var_kl",
                "kl_coef": 0.01,
            },
            "worker": {
                "actor": {
                    "global_batch_size": 128,
                    "micro_batch_size_per_device_for_update": 1,
                    "micro_batch_size_per_device_for_experience": 2,
                    "model": {
                        "model_path": "model",
                        "freeze_vision_tower": True,
                    },
                    "optim": {
                        "lr": 1e-6,
                        "weight_decay": 0.01,
                        "strategy": "adamw",
                    },
                },
                "rollout": {
                    "n": 5,
                    "temperature": 1.0,
                    "top_p": 1.0,
                    "tensor_parallel_size": 1,
                },
                "reward": {
                    "reward_function": "pilot_reward:compute_score",
                    "reward_function_kwargs": {"format_weight": 0.5},
                },
            },
            "trainer": {
                "total_epochs": 1,
                "max_steps": 100,
                "nnodes": 1,
                "n_gpus_per_node": 4,
                "val_freq": 10,
                "save_freq": 20,
            },
        }
        if arm == mismatch_arm:
            config["worker"]["rollout"]["n"] = 7
        config_path = root / f"{arm}.yaml"
        config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
        omitted = 37 if arm == gap_arm else None
        metric_path = root / f"{arm}.jsonl"
        metric_path.write_text(
            "".join(
                builder.json.dumps(
                    {
                        "step": step,
                        "perf": {
                            "total_num_tokens": 1000 + step,
                            "time_per_step": 10.0 + step / 10,
                        },
                    }
                )
                + "\n"
                for step in range(1, 101)
                if step != omitted
            ),
            encoding="utf-8",
        )
        resolved[arm] = {
            "config": config_path,
            "metric_segments": [
                {
                    "path": metric_path,
                    "sha256": builder._sha256(metric_path),
                    "start_step": 1,
                    "end_step": 100,
                }
            ],
            "payload": {
                "start_time_utc": "2026-07-01T00:00:00Z",
                "end_time_utc": "2026-07-01T01:00:00Z",
                "node": "node",
                "gpu_ids": [0, 1, 2, 3],
                "tensor_parallel_width": 1,
                "replica_count": 4,
            },
        }
    return resolved


def test_training_resource_accounting_rejects_missing_retained_step(
    tmp_path: Path,
) -> None:
    resolved = _resource_fixture(tmp_path, gap_arm="a2_gray")

    with pytest.raises(ValueError, match=r"a2_gray: missing=\[37\]"):
        builder._load_training_resources(resolved, tmp_path)


def test_training_resource_accounting_rejects_budget_drift(tmp_path: Path) -> None:
    resolved = _resource_fixture(tmp_path, mismatch_arm="a3_caption")

    with pytest.raises(ValueError, match="worker.rollout.n"):
        builder._load_training_resources(resolved, tmp_path)


def test_primary_geometry_scope_uses_frozen_instrument_category() -> None:
    scope = f"category:{builder.R19_GEOMETRY_CATEGORY}"
    r19 = {
        "arms": {
            arm: {str(step): {scope: {"n": 600}} for step in (60, 100)}
            for arm in builder.ARMS
        }
    }

    assert builder._primary_geometry_scope(r19) == scope


def test_primary_geometry_scope_rejects_human_alias() -> None:
    r19 = {
        "primary_endpoint_scope": "category:geometry",
        "arms": {
            arm: {
                str(step): {"category:geometry": {"n": 600}}
                for step in (60, 100)
            }
            for arm in builder.ARMS
        },
    }

    with pytest.raises(ValueError, match="unexpected R19 primary geometry scope"):
        builder._primary_geometry_scope(r19)
