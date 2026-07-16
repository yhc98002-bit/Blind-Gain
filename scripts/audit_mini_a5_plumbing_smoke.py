#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from scripts.audit_mini_a5_advantages import ALLOWED_ARM_DIFFS, config_differences
from src.fliptrack.schema import sha256_file


CP_MARKER = "BLIND_GAINS_CP_ADVANTAGE_AUDIT "
FATAL_PATTERN = re.compile(
    r"traceback|cuda out of memory|nccl[^\n]*(?:error|fatal)|segmentation fault",
    re.IGNORECASE,
)
EXPECTED_CONFIG_HASHES = {
    "cp": "3dfcd9d8f2a9f654d51a0441166820d7b06ca4cf083bff97f781a065c00e4014",
    "member": "f94f8b4426d11f9eb8f183640bfeeca8c6258801125477f759b46e488ef2e118",
}
EXPECTED_DATA_SHA256 = "1ed1413f6ca92d67fdd9ea2f8bf9072d9126c97403ffcd9fef0f97d9cbb74475"


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _all_finite(value: Any) -> bool:
    if isinstance(value, dict):
        return all(_all_finite(child) for child in value.values())
    if isinstance(value, list):
        return all(_all_finite(child) for child in value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return math.isfinite(float(value))
    return True


def parse_cp_markers(text: str) -> tuple[list[dict[str, Any]], list[str]]:
    payloads: list[dict[str, Any]] = []
    errors: list[str] = []
    for line in text.splitlines():
        if CP_MARKER not in line:
            continue
        raw = line.split(CP_MARKER, maxsplit=1)[1].strip()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as error:
            errors.append(f"invalid CP runtime marker: {error}")
            continue
        if not isinstance(payload, dict):
            errors.append("CP runtime marker is not an object")
            continue
        payloads.append(payload)
    return payloads, errors


def _checkpoint_inventory(path: Path) -> dict[str, Any]:
    files = sorted(candidate for candidate in path.rglob("*") if candidate.is_file())
    return {
        "files": len(files),
        "bytes": sum(candidate.stat().st_size for candidate in files),
        "sha256": {
            str(candidate.relative_to(path)): sha256_file(candidate) for candidate in files
        },
    }


def audit_single_run(manifest_path: Path, expected_mode: str) -> dict[str, Any]:
    if expected_mode not in {"cp", "member"}:
        raise ValueError("expected mode must be cp or member")
    manifest = _read(manifest_path)
    config_path = Path(str(manifest.get("config_path", "")))
    log_path = Path(str(manifest.get("stdout_stderr_log", "")))
    checkpoint_path = Path(str(manifest.get("checkpoint_path", "")))
    registration_marker_path = Path(str(manifest.get("registration_marker", "")))
    overlay_snapshot_path = Path(str(manifest.get("easyr1_worktree_patch", "")))

    config = (
        yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if config_path.is_file()
        else {}
    )
    registration = (
        _read(registration_marker_path) if registration_marker_path.is_file() else {}
    )
    log_text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""
    cp_markers, marker_errors = parse_cp_markers(log_text)
    experiment_log = checkpoint_path / "experiment_log.jsonl"
    experiment_rows: list[dict[str, Any]] = []
    if experiment_log.is_file():
        for line_number, line in enumerate(
            experiment_log.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                marker_errors.append(
                    f"invalid experiment-log row {line_number}: {error}"
                )
                continue
            if isinstance(row, dict):
                experiment_rows.append(row)
            else:
                marker_errors.append(
                    f"experiment-log row {line_number} is not an object"
                )

    training_rows = [
        row
        for row in experiment_rows
        if row.get("step") == 1
        and isinstance(row.get("actor"), dict)
        and isinstance(row.get("reward"), dict)
    ]
    expected_reward_suffix = (
        "src/rewards/cp_grpo_reward.py:compute_score"
        if expected_mode == "cp"
        else "src/rewards/cp_grpo_reward.py:compute_member_score"
    )
    config_reward = str(
        config.get("worker", {}).get("reward", {}).get("reward_function", "")
    )
    cp_marker_exact = (
        len(cp_markers) == 1
        and cp_markers[0].get("row_count") == 80
        and cp_markers[0].get("pair_count") == 8
        and cp_markers[0].get("rollout_counts") == [5]
        and cp_markers[0].get("advantages_finite") is True
    )
    if expected_mode == "member":
        cp_marker_exact = not cp_markers

    checkpoint = checkpoint_path / "global_step_1"
    checkpoint_inventory = (
        _checkpoint_inventory(checkpoint) if checkpoint.is_dir() else {"files": 0, "bytes": 0, "sha256": {}}
    )
    checks = {
        "manifest_complete_exit0": manifest.get("status") == "complete"
        and manifest.get("exit_code") == 0,
        "manifest_job_and_mode_exact": manifest.get("job_type")
        == "m6_mini_a5_registered_plumbing_smoke"
        and manifest.get("smoke_mode") == expected_mode,
        "one_optimizer_step_only": manifest.get("optimizer_steps_expected") == 1
        and manifest.get("main_m6_optimizer_steps_authorized") == 0,
        "single_node_eight_gpu_tp1": len(manifest.get("gpu_ids", [])) == 8
        and len(set(manifest.get("gpu_ids", []))) == 8
        and manifest.get("tensor_parallel_width") == 1
        and manifest.get("replica_count") == 8,
        "effective_config_hash_exact": config_path.is_file()
        and sha256_file(config_path) == EXPECTED_CONFIG_HASHES[expected_mode]
        and manifest.get("config_hash") == EXPECTED_CONFIG_HASHES[expected_mode],
        "config_mode_reward_and_budget_exact": config.get("algorithm", {}).get(
            "pair_group_mode"
        )
        == ("joint" if expected_mode == "cp" else "member")
        and config_reward.endswith(expected_reward_suffix)
        and config.get("trainer", {}).get("max_steps") == 1
        and config.get("data", {}).get("rollout_batch_size") == 16
        and config.get("worker", {}).get("rollout", {}).get("n") == 5,
        "fixed_data_hash_exact": Path("data/mini_a5_plumbing_val_v1.jsonl").is_file()
        and sha256_file(Path("data/mini_a5_plumbing_val_v1.jsonl"))
        == EXPECTED_DATA_SHA256,
        "registration_marker_exact": registration.get("status") == "registered"
        and registration.get("registration_commit")
        == manifest.get("registration_commit")
        and registration_marker_path.is_file()
        and sha256_file(registration_marker_path)
        == manifest.get("registration_marker_sha256")
        and registration.get("main_optimizer_steps_authorized") == 0,
        "easyr1_revision_and_patch_exact": manifest.get("easyr1_revision")
        == "dd71bbd252694f5f850213eec15795b6b88d9fea"
        and overlay_snapshot_path.is_file()
        and sha256_file(overlay_snapshot_path)
        == manifest.get("easyr1_worktree_patch_sha256")
        == registration.get("easyr1_worktree_diff_sha256"),
        "training_log_present_without_fatal_signature": bool(log_text)
        and FATAL_PATTERN.search(log_text) is None,
        "runtime_advantage_branch_evidence_exact": cp_marker_exact
        and not marker_errors,
        "one_finite_actor_reward_training_row": len(training_rows) == 1
        and _all_finite(training_rows[0]),
        "expected_reward_metrics_present": len(training_rows) == 1
        and {
            "overall",
            "accuracy",
            "member_accuracy",
            "pair_joint_accuracy",
        }.issubset(training_rows[0].get("reward", {})),
        "actor_update_metrics_present": len(training_rows) == 1
        and {"pg_loss", "grad_norm"}.issubset(training_rows[0].get("actor", {})),
        "model_only_checkpoint_nonempty": checkpoint_inventory["files"] > 0
        and checkpoint_inventory["bytes"] > 0,
    }
    errors = marker_errors + [name for name, result in checks.items() if not result]
    return {
        "status": "pass" if all(checks.values()) and not errors else "fail",
        "mode": expected_mode,
        "manifest": str(manifest_path),
        "checks": checks,
        "errors": errors,
        "node": manifest.get("node"),
        "gpu_ids": manifest.get("gpu_ids"),
        "start_time_utc": manifest.get("start_time_utc"),
        "end_time_utc": manifest.get("end_time_utc"),
        "runtime_markers": cp_markers,
        "training_log_rows": len(training_rows),
        "checkpoint_inventory": checkpoint_inventory,
        "artifact_sha256": {
            "manifest": sha256_file(manifest_path),
            "effective_config": sha256_file(config_path) if config_path.is_file() else None,
            "training_log": sha256_file(log_path) if log_path.is_file() else None,
            "experiment_log": sha256_file(experiment_log)
            if experiment_log.is_file()
            else None,
        },
    }


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def build_audit(cp_manifest: Path, member_manifest: Path) -> dict[str, Any]:
    cp = audit_single_run(cp_manifest, "cp")
    member = audit_single_run(member_manifest, "member")
    cp_manifest_payload = _read(cp_manifest)
    member_manifest_payload = _read(member_manifest)
    cp_config = yaml.safe_load(
        Path(cp_manifest_payload["config_path"]).read_text(encoding="utf-8")
    )
    member_config = yaml.safe_load(
        Path(member_manifest_payload["config_path"]).read_text(encoding="utf-8")
    )
    cp_end = _parse_time(cp["end_time_utc"])
    member_start = _parse_time(member["start_time_utc"])
    combined_checks = {
        "cp_run_passed": cp["status"] == "pass",
        "member_run_passed": member["status"] == "pass",
        "same_single_node_and_gpu_set": cp["node"] == member["node"]
        and sorted(cp["gpu_ids"]) == sorted(member["gpu_ids"]),
        "sequential_nonoverlapping_runs": cp_end is not None
        and member_start is not None
        and cp_end <= member_start,
        "configs_differ_only_in_registered_fields": set(
            config_differences(cp_config, member_config)
        )
        == ALLOWED_ARM_DIFFS,
    }
    return {
        "schema_version": "blind-gains.mini-a5-plumbing-smoke-audit.v1",
        "status": "pass" if all(combined_checks.values()) else "fail",
        "checks": combined_checks,
        "cp": cp,
        "member": member,
        "scientific_gate_decision": None,
        "main_optimizer_steps_authorized_by_this_audit": 0,
    }


def render_markdown(payload: dict[str, Any], machine_path: Path) -> str:
    checks = [
        f"| `{name}` | `{'pass' if result else 'fail'}` |"
        for name, result in payload["checks"].items()
    ]
    return "\n".join(
        [
            "# Mini-A5 Plumbing Smoke Audit V1",
            "",
            "Status:",
            f"- Independent engineering audit: `{payload['status']}`.",
            "- This audit authorizes zero main-arm optimizer steps and makes no PI gate decision.",
            "",
            "Evidence:",
            f"- Machine artifact: `{machine_path}`.",
            f"- CP run: `{payload['cp']['manifest']}`; checks passed `{sum(payload['cp']['checks'].values())}/{len(payload['cp']['checks'])}`.",
            f"- Member run: `{payload['member']['manifest']}`; checks passed `{sum(payload['member']['checks'].values())}/{len(payload['member']['checks'])}`.",
            f"- CP runtime marker: `{payload['cp']['runtime_markers']}`.",
            f"- CP checkpoint inventory: `{payload['cp']['checkpoint_inventory']['files']}` files / `{payload['cp']['checkpoint_inventory']['bytes']}` bytes.",
            f"- Member checkpoint inventory: `{payload['member']['checkpoint_inventory']['files']}` files / `{payload['member']['checkpoint_inventory']['bytes']}` bytes.",
            "",
            "Checks:",
            "| Check | Result |",
            "| --- | --- |",
            *checks,
            "",
            "Problems:",
            f"- CP errors: `{payload['cp']['errors']}`.",
            f"- Member errors: `{payload['member']['errors']}`.",
            "",
            "Decision:",
            "- A pass establishes only the registered one-step plumbing path.",
            "- Main M6 arms remain blocked until a separate post-smoke marker binds this audit and the exact main configs.",
            "",
        ]
    )


def _atomic_write(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite smoke audit: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cp-manifest", type=Path, required=True)
    parser.add_argument("--member-manifest", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    payload = build_audit(args.cp_manifest, args.member_manifest)
    _atomic_write(args.json_output, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    _atomic_write(args.markdown_output, render_markdown(payload, args.json_output))
    print(json.dumps({"status": payload["status"], "checks": payload["checks"]}))
    raise SystemExit(0 if payload["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
