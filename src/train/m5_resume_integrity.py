from __future__ import annotations

import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Any

import yaml


ALLOWED_CONFIG_DIFFS = {
    "integrity": {
        "trainer.max_steps": 101,
        "trainer.experiment_name": "m5_anchor_resume_integrity_step101",
        "trainer.save_freq": 101,
        "trainer.save_checkpoint_path": (
            "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/"
            "checkpoints/m5_anchor_resume_integrity_step101"
        ),
        "trainer.load_checkpoint_path": (
            "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/"
            "checkpoints/anchor_a0_recipe_3b_geo3k/"
            "anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_100"
        ),
    },
    "longhorizon": {
        "trainer.max_steps": 400,
        "trainer.experiment_name": "m5_anchor_longhorizon_400",
        "trainer.save_freq": 50,
        "trainer.save_checkpoint_path": (
            "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/"
            "checkpoints/m5_anchor_longhorizon_400"
        ),
        "trainer.load_checkpoint_path": (
            "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/"
            "checkpoints/anchor_a0_recipe_3b_geo3k/"
            "anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_100"
        ),
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    if not isinstance(value, dict):
        return {prefix: value}
    result: dict[str, Any] = {}
    for key, child in value.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        result.update(_flatten(child, path))
    return result


def validate_config_derivation(
    base_path: Path, derived_path: Path, *, mode: str
) -> dict[str, Any]:
    if mode not in ALLOWED_CONFIG_DIFFS:
        raise ValueError(f"unknown M5 config mode: {mode}")
    base = yaml.safe_load(base_path.read_text(encoding="utf-8"))
    derived = yaml.safe_load(derived_path.read_text(encoding="utf-8"))
    if not isinstance(base, dict) or not isinstance(derived, dict):
        raise ValueError("M5 configs must be YAML mappings")
    base_flat = _flatten(base)
    derived_flat = _flatten(derived)
    keys = set(base_flat) | set(derived_flat)
    observed = {
        key: {"base": base_flat.get(key), "derived": derived_flat.get(key)}
        for key in sorted(keys)
        if base_flat.get(key) != derived_flat.get(key)
    }
    expected_values = ALLOWED_CONFIG_DIFFS[mode]
    expected_keys = set(expected_values)
    values_match = all(
        observed.get(key, {}).get("derived") == expected
        for key, expected in expected_values.items()
    )
    checks = {
        "exact_allowed_diff_keys": set(observed) == expected_keys,
        "exact_registered_derived_values": values_match,
        "native_reward_unchanged": derived_flat.get("worker.reward.reward_function")
        == base_flat.get("worker.reward.reward_function")
        and str(derived_flat.get("worker.reward.reward_function", "")).endswith(
            "examples/reward_function/r1v.py:compute_score"
        ),
        "vision_tower_setting_unchanged": derived_flat.get(
            "worker.actor.model.freeze_vision_tower"
        )
        is False,
        "rollout_tp_unchanged": derived_flat.get("worker.rollout.tensor_parallel_size")
        == base_flat.get("worker.rollout.tensor_parallel_size")
        == 2,
        "seed_unchanged": derived_flat.get("data.seed") == base_flat.get("data.seed") == 1,
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "mode": mode,
        "checks": checks,
        "observed_diffs": observed,
        "base_config": str(base_path),
        "base_config_sha256": sha256(base_path),
        "derived_config": str(derived_path),
        "derived_config_sha256": sha256(derived_path),
    }


def read_training_metrics(path: Path) -> dict[int, dict[str, Any]]:
    rows: dict[int, dict[str, Any]] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        row = json.loads(line)
        step = row.get("step")
        if not isinstance(step, int) or not isinstance(row.get("perf"), dict):
            continue
        if step in rows:
            raise ValueError(f"duplicate training metric step {step} at {path}:{line_number}")
        rows[step] = row
    return rows


def continuity_checks(
    source_rows: dict[int, dict[str, Any]], integrity_rows: dict[int, dict[str, Any]]
) -> dict[str, Any]:
    source_tail = [source_rows.get(step) for step in range(91, 101)]
    observed_integrity_steps = sorted(integrity_rows)
    row = integrity_rows.get(101)
    finite_fields: dict[str, float] = {}
    if row is not None:
        finite_fields = {
            "actor.pg_loss": float(row.get("actor", {}).get("pg_loss", math.nan)),
            "actor.kl_loss": float(row.get("actor", {}).get("kl_loss", math.nan)),
            "actor.grad_norm": float(row.get("actor", {}).get("grad_norm", math.nan)),
            "reward.overall": float(row.get("reward", {}).get("overall", math.nan)),
            "perf.total_num_tokens": float(
                row.get("perf", {}).get("total_num_tokens", math.nan)
            ),
            "perf.time_per_step": float(
                row.get("perf", {}).get("time_per_step", math.nan)
            ),
        }
    source_token_values = [
        float(item["perf"]["total_num_tokens"])
        for item in source_tail
        if isinstance(item, dict)
        and isinstance(item.get("perf"), dict)
        and "total_num_tokens" in item["perf"]
    ]
    median_tokens = statistics.median(source_token_values) if source_token_values else math.nan
    checks = {
        "source_steps_91_through_100_present": all(item is not None for item in source_tail),
        "integrity_training_steps_exactly_101": observed_integrity_steps == [101],
        "all_continuity_fields_finite": bool(finite_fields)
        and all(math.isfinite(value) for value in finite_fields.values()),
        "learning_rate_continuity": row is not None
        and float(row.get("actor", {}).get("lr", math.nan)) == 1.0e-6,
        "kl_coefficient_continuity": row is not None
        and float(row.get("actor", {}).get("kl_coef", math.nan)) == 0.01,
        "policy_loss_bounded": bool(finite_fields)
        and abs(finite_fields["actor.pg_loss"]) <= 1.0,
        "kl_loss_bounded": bool(finite_fields)
        and abs(finite_fields["actor.kl_loss"]) <= 1.0,
        "gradient_norm_bounded": bool(finite_fields)
        and 0.0 <= finite_fields["actor.grad_norm"] <= 10.0,
        "reward_bounded": bool(finite_fields)
        and 0.0 <= finite_fields["reward.overall"] <= 1.0,
        "token_count_within_recent_factor_two": bool(finite_fields)
        and math.isfinite(median_tokens)
        and 0.5 * median_tokens
        <= finite_fields["perf.total_num_tokens"]
        <= 2.0 * median_tokens,
        "step_time_positive": bool(finite_fields)
        and finite_fields["perf.time_per_step"] > 0.0,
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "source_tail_steps": list(range(91, 101)),
        "integrity_training_steps": observed_integrity_steps,
        "source_tail_median_total_num_tokens": median_tokens,
        "step101_fields": finite_fields,
        "predeclared_bounds": {
            "abs_policy_loss_max": 1.0,
            "abs_kl_loss_max": 1.0,
            "gradient_norm": [0.0, 10.0],
            "reward": [0.0, 1.0],
            "tokens_vs_source_tail_median": [0.5, 2.0],
        },
    }


def raw_hash_continuity(
    relocation_marker: dict[str, Any], restored_audit: dict[str, Any]
) -> dict[str, Any]:
    expected = {
        str(row["file"]): str(row["sha256"])
        for row in relocation_marker.get("files", [])
    }
    observed = {
        Path(str(row["path"])).name: str(row["sha256"])
        for row in restored_audit.get("files", [])
        if Path(str(row.get("path", ""))).name.startswith(("model_", "optim_"))
    }
    checks = {
        "relocation_marker_status": relocation_marker.get("status")
        == "raw_training_state_relocated_due_to_shared_quota",
        "restored_checkpoint_audit_pass": restored_audit.get("status") == "pass",
        "eight_raw_shards_registered": len(expected) == 8,
        "raw_shard_names_and_hashes_exact": observed == expected,
        "restored_checkpoint_files_stable_during_hash": restored_audit.get(
            "files_stable_during_hash"
        )
        is True,
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "raw_shard_count": len(expected),
    }
