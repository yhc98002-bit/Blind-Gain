#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
from fractions import Fraction
from pathlib import Path
from typing import Any

import yaml

from src.analysis.pilot_fourarm import (
    deterministic_seed,
    floor_and_tail_deciles,
    hurdle_summary,
    mean_with_paired_bootstrap,
    paired_difference,
    paired_ratio,
    tied_spearman,
)
from src.analysis.support_sharpening import build_resampling_candidates
from src.eval.fliptrack_metrics import pair_score
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT
from src.eval.scorer_accounting import strict_gain_decomposition


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "blind-gains.pilot-fourarm-seed1-readout.v1"
CONFIG_SCHEMA_VERSION = "blind-gains.pilot-fourarm-seed1-readout-config.v1"
FOLLOWUP_CONFIG_SCHEMA_VERSION = "blind-gains.pilot-fourarm-followup-readout-config.v1"
ARMS = ("a1_real", "a2_gray", "a2b_noimage", "a3_caption")
CONDITIONS = {
    "a1_real": "real",
    "a2_gray": "gray",
    "a2b_noimage": "none",
    "a3_caption": "caption",
}
DISPLAY_NAMES = {
    "a1_real": "A1 real",
    "a2_gray": "A2 gray",
    "a2b_noimage": "A2b no-image",
    "a3_caption": "A3 caption",
}
BASELINE_SHA256 = {
    "a1_real": "021da42f00eab94bc431ed0e7924110c237f77454b23ded5a8f1064c48fd6aa3",
    "a2_gray": "55a215966904306e69fbbe1d2c5be8c7829873d0e653ec7738cd36df8f0b24a8",
    "a2b_noimage": "60db78c675680507f1c3bc28ae7294da4cf5811f5cea75306dfdb70318ea2a6d",
    "a3_caption": "6c04277cca314dc22396c3a56175336e2ea0d81661ea2d52a96e5873d7746bd2",
}
R19_GEOMETRY_CATEGORY = "geometry_coordinate_indexing"
R19_GEOMETRY_TEMPLATE = "coordinate_register_twenty_point_x_v02"
MATCHED_BUDGET_PATHS = (
    "data.train_files",
    "data.max_prompt_length",
    "data.max_response_length",
    "data.rollout_batch_size",
    "data.seed",
    "data.min_pixels",
    "data.max_pixels",
    "algorithm.adv_estimator",
    "algorithm.disable_kl",
    "algorithm.use_kl_loss",
    "algorithm.kl_penalty",
    "algorithm.kl_coef",
    "worker.actor.global_batch_size",
    "worker.actor.micro_batch_size_per_device_for_update",
    "worker.actor.micro_batch_size_per_device_for_experience",
    "worker.actor.model.model_path",
    "worker.actor.model.freeze_vision_tower",
    "worker.actor.optim.lr",
    "worker.actor.optim.weight_decay",
    "worker.actor.optim.strategy",
    "worker.rollout.n",
    "worker.rollout.temperature",
    "worker.rollout.top_p",
    "worker.rollout.tensor_parallel_size",
    "worker.reward.reward_function",
    "worker.reward.reward_function_kwargs.format_weight",
    "trainer.total_epochs",
    "trainer.max_steps",
    "trainer.nnodes",
    "trainer.n_gpus_per_node",
    "trainer.val_freq",
    "trainer.save_freq",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve(root: Path, value: str) -> Path:
    candidate = Path(value)
    result = (candidate if candidate.is_absolute() else root / candidate).resolve()
    try:
        result.relative_to(root.resolve())
    except ValueError as error:
        raise ValueError(f"input path escapes repository root: {value}") from error
    return result


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid JSONL at {path}:{line_number}") from error
        if not isinstance(row, dict):
            raise ValueError(f"non-object JSONL row at {path}:{line_number}")
        rows.append(row)
    return rows


def _write_text(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def _exact_arms(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != set(ARMS):
        raise ValueError(f"{label} must contain exactly all four registered arms")
    return value


def validate_config_structure(config: dict[str, Any]) -> None:
    schema_version = config.get("schema_version")
    seed = config.get("seed")
    if schema_version not in {CONFIG_SCHEMA_VERSION, FOLLOWUP_CONFIG_SCHEMA_VERSION}:
        raise ValueError("unsupported four-arm readout config schema")
    if schema_version == CONFIG_SCHEMA_VERSION and seed != 1:
        raise ValueError("seed-1 readout config is pinned to seed 1")
    if schema_version == FOLLOWUP_CONFIG_SCHEMA_VERSION and seed not in {2, 3}:
        raise ValueError("follow-up readout config requires seed 2 or 3")
    if config.get("bootstrap_draws") != 5000:
        raise ValueError("pilot readout is pinned to 5000 bootstrap draws")
    for label in (
        "training_runs",
        "training_metric_segments",
        "geo_baselines",
        "geo_audits",
        "r19_markers",
    ):
        _exact_arms(config.get(label), label)
    for arm, segments in config["training_metric_segments"].items():
        if not isinstance(segments, list) or not segments:
            raise ValueError(f"{arm} requires at least one training metric segment")
        for segment in segments:
            if (
                not isinstance(segment, dict)
                or set(segment) != {"path", "sha256", "start_step", "end_step"}
                or not isinstance(segment["path"], str)
                or not isinstance(segment["sha256"], str)
                or not isinstance(segment["start_step"], int)
                or not isinstance(segment["end_step"], int)
                or segment["start_step"] > segment["end_step"]
            ):
                raise ValueError(f"invalid training metric segment for {arm}")
    for arm, markers in config["r19_markers"].items():
        if not isinstance(markers, dict) or set(markers) != {"60", "100"}:
            raise ValueError(f"{arm} requires exact R19 markers at steps 60 and 100")
    if not isinstance(config.get("r19_base_run"), str):
        raise ValueError("r19_base_run is required")
    if schema_version == FOLLOWUP_CONFIG_SCHEMA_VERSION:
        if not isinstance(config.get("evaluation_lifecycle_manifest"), str):
            raise ValueError("follow-up readout requires an evaluation lifecycle manifest")
        children_hash = config.get("evaluation_lifecycle_children_sha256")
        if not isinstance(children_hash, str) or len(children_hash) != 64:
            raise ValueError("follow-up readout requires the lifecycle children hash")
        if config.get("support_sharpening_candidates") is not False:
            raise ValueError("follow-up seeds must not mint new M10 candidate sets")


def _validate_complete_manifest(path: Path, expected_job_type: str) -> dict[str, Any]:
    manifest = _read_json(path)
    checks = {
        "job_type": manifest.get("job_type") == expected_job_type,
        "status": manifest.get("status") == "complete",
        "exit_code": manifest.get("exit_code", 0) == 0,
        "artifacts_exist": manifest.get("artifacts_exist") is True,
    }
    if not all(checks.values()):
        raise ValueError(f"incomplete or mismatched manifest {path}: {checks}")
    return manifest


def _validate_followup_lifecycle_gate(
    config: dict[str, Any], root: Path
) -> dict[str, Any] | None:
    """Validate the sealed 8/8 gate before any prediction row can be opened."""
    if config["schema_version"] == CONFIG_SCHEMA_VERSION:
        return None
    seed = int(config["seed"])
    manifest_path = _resolve(root, str(config["evaluation_lifecycle_manifest"]))
    manifest = _read_json(manifest_path)
    expected_job_types = {
        "pilot_followup_evaluation_lifecycle",
        "pilot_followup_evaluation_recovery_lifecycle",
    }
    expected_artifacts = manifest.get("expected_artifacts")
    checks = {
        "job_type": manifest.get("job_type") in expected_job_types,
        "pilot_seed": manifest.get("pilot_seed") == seed,
        "status": manifest.get("status") == "complete",
        "exit_code": manifest.get("exit_code") == 0,
        "artifacts_exist": manifest.get("artifacts_exist") is True,
        "performance_values_unopened": manifest.get("performance_values_opened") is False,
        "two_expected_artifacts": isinstance(expected_artifacts, list)
        and len(expected_artifacts) == 2,
    }
    if not all(checks.values()):
        raise ValueError(f"follow-up evaluation lifecycle is not complete: {checks}")

    children_path = _resolve(root, str(expected_artifacts[0]))
    output_path = _resolve(root, str(expected_artifacts[1]))
    expected_children_hash = str(config["evaluation_lifecycle_children_sha256"])
    children_hash = _sha256(children_path)
    if (
        children_hash != expected_children_hash
        or manifest.get("data_manifest_hash") != expected_children_hash
    ):
        raise ValueError("follow-up lifecycle children hash mismatch")
    output = _read_json(output_path)
    output_checks = output.get("checks")
    endpoints = output.get("endpoints")
    observed_endpoints = (
        {
            (item.get("arm"), item.get("global_step"))
            for item in endpoints
            if isinstance(item, dict)
        }
        if isinstance(endpoints, list)
        else set()
    )
    expected_endpoints = {(arm, step) for arm in ARMS for step in (60, 100)}
    if (
        output.get("status") != "complete"
        or output.get("seed") != seed
        or output.get("performance_values_opened") is not False
        or not isinstance(endpoints, list)
        or len(endpoints) != 8
        or observed_endpoints != expected_endpoints
        or not all(
            isinstance(item, dict)
            and item.get("geo3k_row_count") == 601
            and all(
                isinstance(item.get(field), str) and len(item[field]) == 64
                for field in (
                    "r19_queue_manifest_sha256",
                    "r19_state_sha256",
                    "r19_marker_sha256",
                    "geo3k_queue_manifest_sha256",
                    "geo3k_state_sha256",
                    "geo3k_audit_sha256",
                )
            )
            for item in endpoints
        )
        or not isinstance(output_checks, dict)
        or not output_checks
        or not all(output_checks.values())
        or _resolve(root, str(output.get("children_manifest"))) != children_path
        or output.get("children_manifest_sha256") != expected_children_hash
    ):
        raise ValueError("follow-up lifecycle output did not pass the sealed 8/8 gate")
    return {
        "manifest": manifest_path,
        "children": children_path,
        "output": output_path,
        "payload": output,
    }


def preflight_inputs(config: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    """Validate every arm before any scientific per-item row is opened."""
    validate_config_structure(config)
    lifecycle = _validate_followup_lifecycle_gate(config, root)
    seed = int(config["seed"])
    training_job_type = (
        "l13_mechanical_pilot_arm" if seed == 1 else "m3_mechanical_pilot_arm"
    )
    geo_job_type = (
        "m2_pilot_geo3k_step100_eval"
        if seed == 1
        else "m3_pilot_geo3k_checkpoint_eval"
    )
    resolved: dict[str, Any] = {
        "training": {},
        "geo": {},
        "r19": {},
        "lifecycle": lifecycle,
    }
    prereg = root / "reports/preregistration_pilot_v1.md"
    expected_prereg = str(config.get("preregistration_sha256", ""))
    if not prereg.is_file() or _sha256(prereg) != expected_prereg:
        raise ValueError("preregistration hash mismatch")

    for arm in ARMS:
        training_run = _resolve(root, str(config["training_runs"][arm]))
        training_manifest_path = training_run / "run_manifest.json"
        training = _validate_complete_manifest(
            training_manifest_path, training_job_type
        )
        identity = {
            "arm": arm,
            "image_condition": CONDITIONS[arm],
            "seed": seed,
        }
        if any(training.get(key) != value for key, value in identity.items()):
            raise ValueError(f"training identity mismatch for {arm}")
        training_config = _resolve(root, str(training.get("config_path")))
        if not training_config.is_file() or _sha256(training_config) != training.get(
            "config_hash"
        ):
            raise ValueError(f"training config hash mismatch for {arm}")
        metric_segments: list[dict[str, Any]] = []
        for segment in config["training_metric_segments"][arm]:
            segment_path = _resolve(root, segment["path"])
            if not segment_path.is_file() or _sha256(segment_path) != segment["sha256"]:
                raise ValueError(f"training metric segment hash mismatch for {arm}")
            metric_segments.append({**segment, "path": segment_path})
        resolved["training"][arm] = {
            "run": training_run,
            "manifest": training_manifest_path,
            "payload": training,
            "config": training_config,
            "metric_segments": metric_segments,
        }

        baseline = _resolve(root, str(config["geo_baselines"][arm]))
        if not baseline.is_file() or _sha256(baseline) != BASELINE_SHA256[arm]:
            raise ValueError(f"frozen baseline hash mismatch for {arm}")

        audit_path = _resolve(root, str(config["geo_audits"][arm]))
        audit = _read_json(audit_path)
        audit_checks = audit.get("checks")
        if (
            audit.get("status") != "pass"
            or audit.get("row_count") != 601
            or audit.get("performance_values_reported") is not False
            or not isinstance(audit_checks, dict)
            or not audit_checks
            or not all(audit_checks.values())
            or audit.get("static_mismatch_count") != 0
            or audit.get("score_recomputation_mismatch_count") != 0
            or audit.get("strict_identity_mismatch_count") != 0
        ):
            raise ValueError(f"Geometry3K audit does not pass for {arm}")
        evaluation_manifest_path = _resolve(root, str(audit.get("run_manifest")))
        if _sha256(evaluation_manifest_path) != audit.get("run_manifest_sha256"):
            raise ValueError(f"Geometry3K manifest hash mismatch for {arm}")
        evaluation = _validate_complete_manifest(
            evaluation_manifest_path, geo_job_type
        )
        if (
            evaluation.get("arm") != arm
            or evaluation.get("condition") != CONDITIONS[arm]
            or evaluation.get("global_step") != 100
            or evaluation.get("expected_row_count") != 601
        ):
            raise ValueError(f"Geometry3K evaluation identity mismatch for {arm}")
        output = _resolve(root, str(audit.get("output")))
        if not output.is_file() or _sha256(output) != audit.get("output_sha256"):
            raise ValueError(f"Geometry3K output hash mismatch for {arm}")
        resolved["geo"][arm] = {
            "baseline": baseline,
            "audit": audit_path,
            "evaluation_manifest": evaluation_manifest_path,
            "output": output,
        }

        resolved["r19"][arm] = {}
        for step in (60, 100):
            marker_path = _resolve(root, str(config["r19_markers"][arm][str(step)]))
            marker = _read_json(marker_path)
            marker_checks = marker.get("checks")
            if (
                marker.get("status") != "complete"
                or marker.get("global_step") != step
                or not isinstance(marker_checks, dict)
                or not marker_checks
                or not all(marker_checks.values())
            ):
                raise ValueError(f"R19 step-{step} marker does not pass for {arm}")
            evaluation_run = _resolve(root, str(marker.get("evaluation_run")))
            evaluation_manifest_path = evaluation_run / "run_manifest.json"
            evaluation = _validate_complete_manifest(
                evaluation_manifest_path, "fliptrack_v02_image_evaluation"
            )
            if (
                evaluation.get("global_step") != step
                or evaluation.get("source_training_run")
                != str(training_run.relative_to(root))
                or evaluation.get("image_mode") != "real"
            ):
                raise ValueError(f"R19 step-{step} evaluation identity mismatch for {arm}")
            shards = sorted((evaluation_run / "shards").glob("shard_*.jsonl"))
            if not shards:
                raise ValueError(f"R19 step-{step} shards are absent for {arm}")
            resolved["r19"][arm][step] = {
                "marker": marker_path,
                "evaluation_run": evaluation_run,
                "evaluation_manifest": evaluation_manifest_path,
                "shards": shards,
            }

    base_run = _resolve(root, config["r19_base_run"])
    base_manifest_path = base_run / "run_manifest.json"
    base_manifest = _validate_complete_manifest(
        base_manifest_path, "fliptrack_v02_image_evaluation"
    )
    if base_manifest.get("image_mode") != "real":
        raise ValueError("R19 base run is not the locked real-image condition")
    base_shards = sorted((base_run / "shards").glob("shard_*.jsonl"))
    if not base_shards:
        raise ValueError("R19 base shards are absent")
    resolved["r19_base"] = {
        "run": base_run,
        "manifest": base_manifest_path,
        "shards": base_shards,
    }
    return resolved


def _nested_value(payload: dict[str, Any], dotted_path: str) -> Any:
    value: Any = payload
    for part in dotted_path.split("."):
        if not isinstance(value, dict) or part not in value:
            raise ValueError(f"missing registered budget field: {dotted_path}")
        value = value[part]
    return value


def _load_training_resources(
    resolved_training: dict[str, dict[str, Any]], root: Path
) -> dict[str, Any]:
    """Load all four retained trajectories only after the four-arm preflight passes."""
    budget_signatures: dict[str, dict[str, Any]] = {}
    results: dict[str, Any] = {}
    for arm in ARMS:
        config_payload = yaml.safe_load(
            resolved_training[arm]["config"].read_text(encoding="utf-8")
        )
        if not isinstance(config_payload, dict):
            raise ValueError(f"invalid effective training config for {arm}")
        if _nested_value(config_payload, "data.image_condition") != CONDITIONS[arm]:
            raise ValueError(f"effective image condition mismatch for {arm}")
        signature = {
            path: _nested_value(config_payload, path) for path in MATCHED_BUDGET_PATHS
        }
        budget_signatures[arm] = signature

        rows_by_step: dict[int, dict[str, Any]] = {}
        segment_provenance: list[dict[str, Any]] = []
        for segment in resolved_training[arm]["metric_segments"]:
            rows = _read_jsonl(segment["path"])
            selected = 0
            for row in rows:
                step = row.get("step")
                perf = row.get("perf")
                if (
                    not isinstance(step, int)
                    or step < segment["start_step"]
                    or step > segment["end_step"]
                    or not isinstance(perf, dict)
                    or "total_num_tokens" not in perf
                    or "time_per_step" not in perf
                ):
                    continue
                if step in rows_by_step:
                    raise ValueError(f"duplicate retained metric step {step} for {arm}")
                token_count = int(perf["total_num_tokens"])
                active_seconds = float(perf["time_per_step"])
                if token_count <= 0 or not math.isfinite(active_seconds) or active_seconds <= 0:
                    raise ValueError(f"invalid retained resource metric at {arm} step {step}")
                rows_by_step[step] = {
                    "total_num_tokens": token_count,
                    "time_per_step_seconds": active_seconds,
                }
                selected += 1
            segment_provenance.append(
                {
                    "path": str(segment["path"].relative_to(root)),
                    "sha256": segment["sha256"],
                    "registered_step_range": [
                        segment["start_step"],
                        segment["end_step"],
                    ],
                    "selected_training_rows": selected,
                }
            )
        expected_steps = set(range(1, 101))
        if set(rows_by_step) != expected_steps:
            missing = sorted(expected_steps - set(rows_by_step))
            extra = sorted(set(rows_by_step) - expected_steps)
            raise ValueError(
                f"retained metric trajectory mismatch for {arm}: "
                f"missing={missing}, extra={extra}"
            )
        training = resolved_training[arm]["payload"]
        start = dt.datetime.fromisoformat(str(training["start_time_utc"]).replace("Z", "+00:00"))
        end = dt.datetime.fromisoformat(str(training["end_time_utc"]).replace("Z", "+00:00"))
        if end <= start:
            raise ValueError(f"invalid final process timestamps for {arm}")
        results[arm] = {
            "optimizer_steps": len(rows_by_step),
            "retained_trajectory_tokens": sum(
                row["total_num_tokens"] for row in rows_by_step.values()
            ),
            "retained_trajectory_active_seconds": sum(
                row["time_per_step_seconds"] for row in rows_by_step.values()
            ),
            "final_process_segment_wall_seconds": (end - start).total_seconds(),
            "node": training["node"],
            "gpu_ids": training["gpu_ids"],
            "tensor_parallel_width": training["tensor_parallel_width"],
            "replica_count": training["replica_count"],
            "metric_segments": segment_provenance,
            "effective_config": str(resolved_training[arm]["config"].relative_to(root)),
            "effective_config_sha256": _sha256(resolved_training[arm]["config"]),
        }

    reference = budget_signatures["a1_real"]
    mismatches = {
        arm: {
            path: {"a1_real": reference[path], arm: signature[path]}
            for path in MATCHED_BUDGET_PATHS
            if signature[path] != reference[path]
        }
        for arm, signature in budget_signatures.items()
        if arm != "a1_real"
    }
    mismatches = {arm: fields for arm, fields in mismatches.items() if fields}
    if mismatches:
        raise ValueError(f"matched optimizer budget mismatch: {mismatches}")
    canonical = json.dumps(reference, sort_keys=True, separators=(",", ":"))
    return {
        "claim": "matched optimizer budget; no FLOP-equality claim",
        "matched": True,
        "budget_signature": reference,
        "budget_signature_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "arms": results,
    }


def _index_rows(rows: list[dict[str, Any]], label: str) -> dict[tuple[str, int], dict[str, Any]]:
    indexed: dict[tuple[str, int], dict[str, Any]] = {}
    for row in rows:
        identity = (str(row.get("split")), int(row.get("row_index")))
        if identity in indexed:
            raise ValueError(f"duplicate {label} identity: {identity}")
        indexed[identity] = row
    return indexed


def _load_geo_arm(paths: dict[str, Path], arm: str) -> tuple[list[dict], list[dict]]:
    baseline = [row for row in _read_jsonl(paths["baseline"]) if row.get("split") == "test"]
    post = _read_jsonl(paths["output"])
    if len(baseline) != 601 or len(post) != 601:
        raise ValueError(f"Geometry3K row count mismatch for {arm}")
    baseline_index = _index_rows(baseline, f"{arm} baseline")
    post_index = _index_rows(post, f"{arm} post")
    if baseline_index.keys() != post_index.keys():
        raise ValueError(f"Geometry3K row identity mismatch for {arm}")
    ordered_baseline: list[dict] = []
    ordered_post: list[dict] = []
    for identity in sorted(baseline_index):
        before = baseline_index[identity]
        after = post_index[identity]
        if (
            before.get("condition") != CONDITIONS[arm]
            or after.get("arm") != arm
            or after.get("condition") != CONDITIONS[arm]
            or before.get("sample_count") != 16
            or before.get("ground_truth") != after.get("ground_truth")
        ):
            raise ValueError(f"Geometry3K semantic binding mismatch for {arm}:{identity}")
        ordered_baseline.append(before)
        ordered_post.append(after)
    return ordered_baseline, ordered_post


def _load_r19_shards(paths: list[Path], label: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        rows.extend(_read_jsonl(path))
    pair_ids = [str(row.get("pair_id")) for row in rows]
    if len(rows) != 1200 or len(set(pair_ids)) != 1200:
        raise ValueError(f"R19 coverage mismatch for {label}")
    return rows


def _score_r19(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        pair_id = str(row["pair_id"])
        scored = pair_score(row, prompt_contract=DEFAULT_PROMPT_CONTRACT)
        result[pair_id] = {
            "pair_id": pair_id,
            "template_id": str(row.get("template_id")),
            "category": str(row.get("category")),
            "pair_correct": bool(scored["pair_correct"]),
            "strict_pair_correct": bool(scored["strict_pair_correct"]),
            "collapsed": bool(scored["collapsed"]),
        }
    return result


def _rate(values: list[bool]) -> float:
    return sum(values) / len(values)


def _metric_seed(config: dict[str, Any], label: str) -> int:
    return deterministic_seed(int(config["bootstrap_seed"]), label)


def _geo_results(
    config: dict[str, Any], geo_rows: dict[str, tuple[list[dict], list[dict]]]
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    draws = int(config["bootstrap_draws"])
    results: dict[str, Any] = {"arms": {}, "contrasts": {}, "mechanism": {}}
    joined: dict[str, list[dict[str, Any]]] = {}
    gains: dict[str, list[float]] = {}
    final: dict[str, list[bool]] = {}
    for arm in ARMS:
        baseline, post = geo_rows[arm]
        base_final = [bool(row["greedy_canonical_correct"]) for row in baseline]
        post_final = [bool(row["acc_final"]) for row in post]
        base_strict = [bool(row["greedy_acc_strict"]) for row in baseline]
        post_strict = [bool(row["acc_strict"]) for row in post]
        base_contract = [bool(row["greedy_contract_valid"]) for row in baseline]
        post_contract = [bool(row["contract_valid"]) for row in post]
        base_pilot = [bool(row["greedy_correct"]) for row in baseline]
        post_pilot = [bool(float(row["pilot_accuracy_reward"]) > 0.5) for row in post]
        gain = [float(after) - float(before) for before, after in zip(base_final, post_final)]
        gains[arm] = gain
        final[arm] = post_final

        before_accounting = [
            {"acc_final": value, "acc_strict": strict}
            for value, strict in zip(base_final, base_strict)
        ]
        after_accounting = [
            {"acc_final": value, "acc_strict": strict}
            for value, strict in zip(post_final, post_strict)
        ]
        exact = strict_gain_decomposition(before_accounting, after_accounting)
        accounting = {key: float(value) for key, value in exact.items()}
        accounting["identity_exact"] = exact["StrictGain"] == (
            exact["AnswerGain"] + exact["G_format"]
        )

        arm_rows: list[dict[str, Any]] = []
        for before, after, item_gain in zip(baseline, post, gain):
            arm_rows.append(
                {
                    "split": before["split"],
                    "row_index": before["row_index"],
                    "sample_correct_count": before["sample_correct_count"],
                    "sample_count": before["sample_count"],
                    "q_i": before["q_i"],
                    "gain": item_gain,
                    "step0_acc_final": bool(before["greedy_canonical_correct"]),
                    "target_acc_final": bool(after["acc_final"]),
                    "target_step": 100,
                }
            )
        joined[arm] = arm_rows
        counts = [int(row["sample_correct_count"]) for row in arm_rows]
        q_values = [float(row["q_i"]) for row in arm_rows]
        above_indices = [index for index, count in enumerate(counts) if count > 0]
        mechanism = hurdle_summary(
            counts,
            gain,
            draws=draws,
            seed=_metric_seed(config, f"{arm}:hurdle"),
        )
        mechanism.update(
            {
                "spearman_all": tied_spearman(q_values, gain),
                "spearman_above_floor": tied_spearman(
                    [q_values[index] for index in above_indices],
                    [gain[index] for index in above_indices],
                ),
                "floor_and_above_tail_deciles": floor_and_tail_deciles(arm_rows),
                "q_i_interpretation": (
                    "Jeffreys-smoothed estimate of baseline reward-opportunity; "
                    "not a directly observed latent"
                ),
            }
        )
        results["mechanism"][arm] = mechanism

        results["arms"][arm] = {
            "n": len(baseline),
            "acc_final_step0": _rate(base_final),
            "acc_final_step100": _rate(post_final),
            "delta_acc_final": paired_difference(
                base_final,
                post_final,
                draws=draws,
                seed=_metric_seed(config, f"{arm}:acc_final"),
            ),
            "acc_strict_step0": _rate(base_strict),
            "acc_strict_step100": _rate(post_strict),
            "contract_valid_step0": _rate(base_contract),
            "contract_valid_step100": _rate(post_contract),
            "delta_contract_valid": paired_difference(
                base_contract,
                post_contract,
                draws=draws,
                seed=_metric_seed(config, f"{arm}:format"),
            ),
            "pilot_accuracy_step0": _rate(base_pilot),
            "pilot_accuracy_step100": _rate(post_pilot),
            "delta_pilot_accuracy": paired_difference(
                base_pilot,
                post_pilot,
                draws=draws,
                seed=_metric_seed(config, f"{arm}:pilot_accuracy"),
            ),
            "strict_gain_accounting": accounting,
        }

    a1_gain = gains["a1_real"]
    contrast_specs = {
        "D_gray": "a2_gray",
        "D_none": "a2b_noimage",
        "D_caption": "a3_caption",
    }
    for name, arm in contrast_specs.items():
        contributions = [left - right for left, right in zip(a1_gain, gains[arm])]
        results["contrasts"][name] = mean_with_paired_bootstrap(
            contributions,
            draws=draws,
            seed=_metric_seed(config, name),
        )

    caption_final = [
        float(caption) - float(real)
        for caption, real in zip(final["a3_caption"], final["a1_real"])
    ]
    caption_gain = [right - left for left, right in zip(a1_gain, gains["a3_caption"])]
    gray_none = [
        gray - none for gray, none in zip(gains["a2_gray"], gains["a2b_noimage"])
    ]
    results["contrasts"]["D_caption_final_A3_minus_A1"] = mean_with_paired_bootstrap(
        caption_final,
        draws=draws,
        seed=_metric_seed(config, "D_caption_final"),
    )
    results["contrasts"]["D_caption_gain_A3_minus_A1"] = mean_with_paired_bootstrap(
        caption_gain,
        draws=draws,
        seed=_metric_seed(config, "D_caption_gain"),
    )
    gray_none_summary = mean_with_paired_bootstrap(
        gray_none,
        draws=draws,
        seed=_metric_seed(config, "gray_none_equivalence"),
    )
    gray_none_summary["equivalence_margin"] = [-0.05, 0.05]
    gray_none_summary["equivalence_supported"] = (
        gray_none_summary["ci95"][0] >= -0.05
        and gray_none_summary["ci95"][1] <= 0.05
    )
    results["contrasts"]["gray_minus_none_gain"] = gray_none_summary

    denominator = results["arms"]["a1_real"]["delta_acc_final"]
    stable = denominator["estimate"] >= 2 * denominator["paired_se"]
    results["recovery_fraction_denominator_stable"] = stable
    results["recovery_fractions"] = {}
    for arm in ("a2_gray", "a2b_noimage", "a3_caption"):
        ratio = paired_ratio(
            gains[arm],
            a1_gain,
            draws=draws,
            seed=_metric_seed(config, f"recovery:{arm}"),
        )
        ratio["interpretation_permitted"] = stable
        results["recovery_fractions"][arm] = ratio

    a1_format_gain = results["arms"]["a1_real"]["delta_contract_valid"]["estimate"]
    results["format_prediction"] = {
        "a1_format_gain": a1_format_gain,
        "conditional_on_nontrivial_a1_gain": a1_format_gain > 0,
        "margin": 0.05,
        "blind_arms": {
            arm: {
                "format_gain": results["arms"][arm]["delta_contract_valid"]["estimate"],
                "prediction_holds": results["arms"][arm]["delta_contract_valid"]["estimate"]
                >= a1_format_gain - 0.05,
            }
            for arm in ("a2_gray", "a2b_noimage", "a3_caption")
        },
    }
    return results, joined


def _r19_scope_summary(
    config: dict[str, Any],
    base: dict[str, dict[str, Any]],
    observed: dict[str, dict[str, Any]],
    *,
    label: str,
) -> dict[str, Any]:
    common = sorted(set(base) & set(observed))
    if len(common) != len(base) or len(common) != len(observed):
        raise ValueError(f"R19 identity mismatch for {label}")
    before = [base[pair_id]["pair_correct"] for pair_id in common]
    after = [observed[pair_id]["pair_correct"] for pair_id in common]
    strict_before = [base[pair_id]["strict_pair_correct"] for pair_id in common]
    strict_after = [observed[pair_id]["strict_pair_correct"] for pair_id in common]
    collapsed_before = [base[pair_id]["collapsed"] for pair_id in common]
    collapsed_after = [observed[pair_id]["collapsed"] for pair_id in common]
    draws = int(config["bootstrap_draws"])
    delta = paired_difference(
        before,
        after,
        draws=draws,
        seed=_metric_seed(config, f"r19:{label}:pair"),
    )
    delta["sesoi"] = [-0.05, 0.05]
    delta["no_material_change_supported"] = (
        delta["ci95"][0] >= -0.05 and delta["ci95"][1] <= 0.05
    )
    return {
        "n": len(common),
        "pair_accuracy_step0": _rate(before),
        "pair_accuracy_observed": _rate(after),
        "delta_pair_accuracy": delta,
        "strict_pair_accuracy_step0": _rate(strict_before),
        "strict_pair_accuracy_observed": _rate(strict_after),
        "collapse_rate_step0": _rate(collapsed_before),
        "collapse_rate_observed": _rate(collapsed_after),
    }


def _r19_results(
    config: dict[str, Any],
    base_rows: list[dict[str, Any]],
    observed_rows: dict[str, dict[int, list[dict[str, Any]]]],
) -> dict[str, Any]:
    base = _score_r19(base_rows)
    results: dict[str, Any] = {"base_pair_count": len(base), "arms": {}}
    base_identity = {
        pair_id: (row["template_id"], row["category"]) for pair_id, row in base.items()
    }
    geometry_identity = [
        category
        for template, category in base_identity.values()
        if template == R19_GEOMETRY_TEMPLATE
    ]
    if (
        len(geometry_identity) != 600
        or set(geometry_identity) != {R19_GEOMETRY_CATEGORY}
    ):
        raise ValueError("frozen R19 geometry template/category binding mismatch")
    for arm in ARMS:
        results["arms"][arm] = {}
        for step in (60, 100):
            observed = _score_r19(observed_rows[arm][step])
            identity = {
                pair_id: (row["template_id"], row["category"])
                for pair_id, row in observed.items()
            }
            if identity != base_identity:
                raise ValueError(f"R19 template/category identity mismatch for {arm} step {step}")
            scopes: dict[str, dict[str, Any]] = {
                "overall": _r19_scope_summary(
                    config, base, observed, label=f"{arm}:step{step}:overall"
                )
            }
            categories = sorted({row[1] for row in base_identity.values()})
            for category in categories:
                selected = {
                    pair_id
                    for pair_id, (_, observed_category) in base_identity.items()
                    if observed_category == category
                }
                scopes[f"category:{category}"] = _r19_scope_summary(
                    config,
                    {key: base[key] for key in selected},
                    {key: observed[key] for key in selected},
                    label=f"{arm}:step{step}:category:{category}",
                )
            templates = sorted({row[0] for row in base_identity.values()})
            for template in templates:
                selected = {
                    pair_id
                    for pair_id, (observed_template, _) in base_identity.items()
                    if observed_template == template
                }
                scopes[f"template:{template}"] = _r19_scope_summary(
                    config,
                    {key: base[key] for key in selected},
                    {key: observed[key] for key in selected},
                    label=f"{arm}:step{step}:template:{template}",
                )
            results["arms"][arm][str(step)] = scopes
    results["primary_endpoint"] = (
        f"category:{R19_GEOMETRY_CATEGORY} at step 100"
    )
    results["primary_endpoint_scope"] = f"category:{R19_GEOMETRY_CATEGORY}"
    results["chart_label"] = "cued chart point-value reading"
    results["document_role"] = "calibration only"
    results["r19_r20_pooling"] = False
    return results


def _fmt(value: float | None) -> str:
    return "NA" if value is None else f"{value:.4f}"


def _fmt_estimate(summary: dict[str, Any]) -> str:
    low, high = summary["ci95"]
    return f"{summary['estimate']:.4f} [{low:.4f}, {high:.4f}]"


def _output_schema_version(seed: int) -> str:
    if seed == 1:
        return SCHEMA_VERSION
    return f"blind-gains.pilot-fourarm-seed{seed}-readout.v1"


def _primary_geometry_scope(r19: dict[str, Any]) -> str:
    scope = str(
        r19.get("primary_endpoint_scope", f"category:{R19_GEOMETRY_CATEGORY}")
    )
    expected = f"category:{R19_GEOMETRY_CATEGORY}"
    if scope != expected:
        raise ValueError(f"unexpected R19 primary geometry scope: {scope}")
    for arm in ARMS:
        for step in (60, 100):
            if scope not in r19["arms"][arm][str(step)]:
                raise ValueError(f"missing frozen R19 geometry scope for {arm} step {step}")
    return scope


def render_markdown(payload: dict[str, Any], machine_path: Path) -> str:
    seed = int(payload["seed"])
    geo = payload["geo3k"]
    r19 = payload["fliptrack_r19"]
    resources = payload["training_resources"]
    geometry_scope = _primary_geometry_scope(r19)
    lines = [
        f"# Pilot Four-Arm Seed-{seed} Results V1",
        "",
        "Status:",
        f"- Registered seed-{seed} readout: `complete`.",
        "- This report computes registered analyses only and makes no PI gate decision.",
        "- Proposal-A4 text-only transfer was not launched and is outside Paper-1 scope.",
        "",
        "Evidence:",
        f"- Machine artifact: `{machine_path}`.",
        f"- Geometry3K: `{payload['checks']['geo_row_count_per_arm']}` audited rows per arm.",
        f"- FlipTrack R19: `{r19['base_pair_count']}` paired items at steps 0, 60, and 100.",
        f"- Bootstrap: `{payload['bootstrap']['draws']}` paired item draws, seed `{payload['bootstrap']['seed']}`.",
        "- All four inputs passed independent audit before any per-item result was loaded.",
        "- Training is reported as a matched optimizer budget; no FLOP-equality claim is made.",
        "",
        "## Training Resource Accounting",
        "",
        "| Arm | Steps | Retained trajectory tokens | Active step time (h) | Final process segment (h) | Node / GPUs |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for arm in ARMS:
        row = resources["arms"][arm]
        gpu_text = ",".join(str(gpu) for gpu in row["gpu_ids"])
        lines.append(
            f"| {DISPLAY_NAMES[arm]} | {row['optimizer_steps']} | "
            f"{row['retained_trajectory_tokens']} | "
            f"{row['retained_trajectory_active_seconds'] / 3600:.2f} | "
            f"{row['final_process_segment_wall_seconds'] / 3600:.2f} | "
            f"{row['node']} / {gpu_text} |"
        )
    lines.extend(
        [
            "",
            f"Matched budget signature: `{resources['budget_signature_sha256']}`. Active step time is the sum of EasyR1's per-step `perf.time_per_step` on the retained 1-100 trajectory; final process time covers only the immutable terminal run segment and is not used as a compute-equivalence claim.",
        "",
        "## Primary RQ1: Geometry3K",
        "",
        "| Arm | Acc step 0 | Acc step 100 | Delta Acc_final (95% CI) | Strict step 0 | Strict step 100 |",
        "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for arm in ARMS:
        row = geo["arms"][arm]
        lines.append(
            f"| {DISPLAY_NAMES[arm]} | {_fmt(row['acc_final_step0'])} | "
            f"{_fmt(row['acc_final_step100'])} | {_fmt_estimate(row['delta_acc_final'])} | "
            f"{_fmt(row['acc_strict_step0'])} | {_fmt(row['acc_strict_step100'])} |"
        )
    lines.extend(
        [
            "",
            "| Registered contrast | Estimate (paired 95% CI) |",
            "|---|---:|",
        ]
    )
    for key in ("D_gray", "D_none", "D_caption"):
        lines.append(f"| {key} | {_fmt_estimate(geo['contrasts'][key])} |")
    lines.extend(
        [
            "",
            f"Recovery denominator stable: `{str(geo['recovery_fraction_denominator_stable']).lower()}`.",
            "",
            "| Arm | Recovery fraction (95% CI) | Interpretation permitted |",
            "|---|---:|---:|",
        ]
    )
    for arm, row in geo["recovery_fractions"].items():
        interval = row["ci95"]
        shown = "NA" if row["estimate"] is None or interval is None else (
            f"{row['estimate']:.4f} [{interval[0]:.4f}, {interval[1]:.4f}]"
        )
        lines.append(
            f"| {DISPLAY_NAMES[arm]} | {shown} | "
            f"{str(row['interpretation_permitted']).lower()} |"
        )
    lines.extend(
        [
            "",
            "## Registered Secondary Contrasts",
            "",
            "| Estimand | Estimate (paired 95% CI) |",
            "|---|---:|",
            f"| D_caption^final = Acc_A3,100 - Acc_A1,100 | {_fmt_estimate(geo['contrasts']['D_caption_final_A3_minus_A1'])} |",
            f"| D_caption^gain = Delta_A3 - Delta_A1 | {_fmt_estimate(geo['contrasts']['D_caption_gain_A3_minus_A1'])} |",
            f"| Delta_A2gray - Delta_A2b | {_fmt_estimate(geo['contrasts']['gray_minus_none_gain'])} |",
            "",
            f"Gray/no-image equivalence within +/-0.05 supported: `{str(geo['contrasts']['gray_minus_none_gain']['equivalence_supported']).lower()}`.",
            "",
            "## Strict Accounting",
            "",
            "| Arm | StrictGain | AnswerGain | G_format | Exact identity |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for arm in ARMS:
        row = geo["arms"][arm]["strict_gain_accounting"]
        lines.append(
            f"| {DISPLAY_NAMES[arm]} | {_fmt(row['StrictGain'])} | {_fmt(row['AnswerGain'])} | "
            f"{_fmt(row['G_format'])} | {str(row['identity_exact']).lower()} |"
        )
    lines.extend(
        [
            "",
            "## Mechanism: Baseline Reward-Opportunity",
            "",
            "`q_i` is a Jeffreys-smoothed estimate of baseline reward-opportunity, not a directly observed latent.",
            "",
            "| Arm | Hurdle contrast (95% CI) | Floor n | Above n | Spearman all | Spearman above floor |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for arm in ARMS:
        row = geo["mechanism"][arm]
        lines.append(
            f"| {DISPLAY_NAMES[arm]} | {_fmt_estimate(row)} | {row['floor_n']} | "
            f"{row['above_floor_n']} | {_fmt(row['spearman_all'])} | "
            f"{_fmt(row['spearman_above_floor'])} |"
        )
    lines.extend(
        [
            "",
            "The machine artifact contains the registered floor group and ten equal-count above-floor deciles for every arm.",
            "",
            "## Primary RQ2: FlipTrack R19 Geometry",
            "",
            "| Arm | Step | Pair acc step 0 | Pair acc checkpoint | Delta (paired 95% CI) | No material change supported |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for arm in ARMS:
        for step in (60, 100):
            row = r19["arms"][arm][str(step)][geometry_scope]
            lines.append(
                f"| {DISPLAY_NAMES[arm]} | {step} | {_fmt(row['pair_accuracy_step0'])} | "
                f"{_fmt(row['pair_accuracy_observed'])} | {_fmt_estimate(row['delta_pair_accuracy'])} | "
                f"{str(row['delta_pair_accuracy']['no_material_change_supported']).lower()} |"
            )
    lines.extend(
        [
            "",
            "## R19 Overall and Categories",
            "",
            "Overall R19 is shown with every per-category result; no R19-minus-chart composite is computed.",
            "The chart label is **cued chart point-value reading**. Document is calibration only.",
            "",
            "| Arm | Step | Scope | Pair acc step 0 | Pair acc checkpoint | Delta (95% CI) |",
            "|---|---:|---|---:|---:|---:|",
        ]
    )
    for arm in ARMS:
        for step in (60, 100):
            scopes = r19["arms"][arm][str(step)]
            for scope in ["overall"] + sorted(key for key in scopes if key.startswith("category:")):
                row = scopes[scope]
                lines.append(
                    f"| {DISPLAY_NAMES[arm]} | {step} | {scope} | "
                    f"{_fmt(row['pair_accuracy_step0'])} | {_fmt(row['pair_accuracy_observed'])} | "
                    f"{_fmt_estimate(row['delta_pair_accuracy'])} |"
                )
    lines.extend(
        [
            "",
        ]
    )
    if seed == 1:
        lines.extend(
            [
                "## Support-Sharpening Candidates",
                "",
                "| Arm | Base 0/16, greedy wrong -> step-100 correct | Candidate artifact |",
                "|---|---:|---|",
            ]
        )
        for arm in ARMS:
            row = payload["support_sharpening"][arm]
            lines.append(
                f"| {DISPLAY_NAMES[arm]} | {row['candidate_count']} | "
                f"`{row['candidate_artifact']}` |"
            )
        lines.extend(
            [
                "",
                "The registered 64-sample frozen-base follow-up is reported separately under M10; candidate selection here does not claim that RL created or taught a capability.",
            ]
        )
    else:
        lines.extend(
            [
                "## Support-Sharpening",
                "",
                "- No new M10 candidate set is minted from a follow-up seed; the registered frozen seed-1 candidate sets remain authoritative.",
            ]
        )
    lines.extend(
        [
            "",
            "Problems:",
            "- This single-seed report does not by itself quantify run-to-run RL variance; the registered multi-seed summary remains pending.",
            "",
            "Decision:",
            "- None. PIs interpret the registered estimands and decide subsequent gates.",
            "",
            "Next actions:",
            "- Complete the remaining registered pilot seeds and build the pooled descriptive summary.",
            "- Keep R19/R20 unpooled and preserve all raw per-item artifacts.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_readout(
    config: dict[str, Any],
    *,
    root: Path,
    artifact_dir: Path,
) -> dict[str, Any]:
    resolved = preflight_inputs(config, root)
    training_resources = _load_training_resources(resolved["training"], root)
    geo_rows = {
        arm: _load_geo_arm(resolved["geo"][arm], arm)
        for arm in ARMS
    }
    base_r19_rows = _load_r19_shards(
        resolved["r19_base"]["shards"], "base"
    )
    observed_r19_rows = {
        arm: {
            step: _load_r19_shards(resolved["r19"][arm][step]["shards"], f"{arm}:{step}")
            for step in (60, 100)
        }
        for arm in ARMS
    }
    geo_results, joined = _geo_results(config, geo_rows)
    r19_results = _r19_results(config, base_r19_rows, observed_r19_rows)

    if artifact_dir.exists():
        raise FileExistsError(f"refusing to overwrite artifact directory: {artifact_dir}")
    artifact_dir.mkdir(parents=True)
    generate_support = bool(config.get("support_sharpening_candidates", True))
    support: dict[str, Any] = (
        {} if generate_support else {"status": "seed1_candidate_sets_remain_authoritative"}
    )
    if generate_support:
        for arm in ARMS:
            baseline, post = geo_rows[arm]
            adapted = [
                {
                    **row,
                    "step0_acc_final": bool(before["greedy_canonical_correct"]),
                    "target_step": 100,
                    "target_acc_final": bool(row["acc_final"]),
                }
                for before, row in zip(baseline, post)
            ]
            candidates = build_resampling_candidates(
                baseline,
                adapted,
                arm=arm,
                condition=CONDITIONS[arm],
                target_step=100,
            )
            candidate_path = artifact_dir / f"support_candidates_{arm}.jsonl"
            candidate_path.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in candidates),
                encoding="utf-8",
            )
            support[arm] = {
                "candidate_count": len(candidates),
                "candidate_artifact": str(candidate_path.relative_to(root)),
                "candidate_sha256": _sha256(candidate_path),
                "followup_samples_per_candidate": 64,
                "followup_status": "pending",
            }

    joined_path = artifact_dir / "geo3k_joined_items.jsonl"
    joined_path.write_text(
        "".join(
            json.dumps({"arm": arm, **row}, sort_keys=True) + "\n"
            for arm in ARMS
            for row in joined[arm]
        ),
        encoding="utf-8",
    )
    provenance = {
        "config": str(_resolve(root, str(config["config_path"])).relative_to(root)),
        "config_sha256": _sha256(_resolve(root, str(config["config_path"]))),
        "preregistration_sha256": config["preregistration_sha256"],
        "training_manifests": {
            arm: {
                "path": str(resolved["training"][arm]["manifest"].relative_to(root)),
                "sha256": _sha256(resolved["training"][arm]["manifest"]),
            }
            for arm in ARMS
        },
        "geo_audits": {
            arm: {
                "path": str(resolved["geo"][arm]["audit"].relative_to(root)),
                "sha256": _sha256(resolved["geo"][arm]["audit"]),
            }
            for arm in ARMS
        },
        "r19_markers": {
            arm: {
                str(step): {
                    "path": str(resolved["r19"][arm][step]["marker"].relative_to(root)),
                    "sha256": _sha256(resolved["r19"][arm][step]["marker"]),
                }
                for step in (60, 100)
            }
            for arm in ARMS
        },
    }
    if resolved["lifecycle"] is not None:
        provenance["evaluation_lifecycle"] = {
            "manifest": str(resolved["lifecycle"]["manifest"].relative_to(root)),
            "manifest_sha256": _sha256(resolved["lifecycle"]["manifest"]),
            "children": str(resolved["lifecycle"]["children"].relative_to(root)),
            "children_sha256": _sha256(resolved["lifecycle"]["children"]),
            "output": str(resolved["lifecycle"]["output"].relative_to(root)),
            "output_sha256": _sha256(resolved["lifecycle"]["output"]),
            "performance_values_opened_before_gate": False,
        }
    seed = int(config["seed"])
    payload = {
        "schema_version": _output_schema_version(seed),
        "status": "complete",
        "scientific_gate_decision": None,
        "seed": seed,
        "registered_arms": list(ARMS),
        "proposal_a4_launched": False,
        "bootstrap": {
            "draws": config["bootstrap_draws"],
            "seed": config["bootstrap_seed"],
            "unit": "paired item",
        },
        "checks": {
            "all_four_arms_preflight_before_row_loading": True,
            "geo_row_count_per_arm": 601,
            "r19_pair_count": 1200,
            "strict_gain_identity_all_arms": all(
                geo_results["arms"][arm]["strict_gain_accounting"]["identity_exact"]
                for arm in ARMS
            ),
            "r19_r20_not_pooled": True,
        },
        "provenance": provenance,
        "training_resources": training_resources,
        "geo3k": geo_results,
        "fliptrack_r19": r19_results,
        "support_sharpening": support,
        "joined_geo3k_artifact": str(joined_path.relative_to(root)),
        "joined_geo3k_sha256": _sha256(joined_path),
        "registered_scope_statement": (
            "These are pilot estimands and directional predictions, not definitive hypothesis "
            "tests of the training procedure; item-level paired intervals quantify evaluation "
            "uncertainty, not run-to-run RL variance."
        ),
    }
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    root = ROOT.resolve()
    config_path = _resolve(root, str(args.config))
    config = _read_json(config_path)
    config["config_path"] = str(config_path.relative_to(root))
    artifact_dir = _resolve(root, str(args.artifact_dir))
    json_output = _resolve(root, str(args.json_output))
    markdown_output = _resolve(root, str(args.markdown_output))
    if json_output.exists() or markdown_output.exists():
        raise FileExistsError("refusing to overwrite four-arm report artifacts")
    payload = build_readout(
        config,
        root=root,
        artifact_dir=artifact_dir,
    )
    markdown = render_markdown(payload, json_output.relative_to(root))
    _write_text(json_output, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    _write_text(markdown_output, markdown)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "json": str(json_output.relative_to(root)),
                "markdown": str(markdown_output.relative_to(root)),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
