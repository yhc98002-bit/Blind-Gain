#!/usr/bin/env python3
"""Independent audit of the two Gate-1 completion plumbing smokes (T7).

Mirrors scripts/audit_mini_a5_plumbing_smoke.py for the std/necessity
one-step member-mode smokes: manifest complete/exit0, exactly one optimizer
step authorized and executed, single-node eight-GPU TP1 placement, effective
config and fixed 48-row subset hash-exact against the registered marker
values, member-mode discipline (zero CP advantage markers), no fatal log
signature, one finite step-1 training row with the member reward metrics,
non-empty model-only checkpoint, and the matched-difference discipline of
both smoke configs against the frozen member smoke template.

This audit authorizes zero main-arm optimizer steps.

Adversarial fixture (I10): tests/test_audit_mini_a5_gate1_plumbing_smoke_fixture.py.
"""
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

from scripts.check_mini_a5_matched_diff import check as matched_diff_check
from src.fliptrack.schema import sha256_file

SCHEMA_VERSION = "blind-gains.mini-a5-gate1-plumbing-smoke-audit.v1"
CP_MARKER = "BLIND_GAINS_CP_ADVANTAGE_AUDIT "
FATAL_PATTERN = re.compile(
    r"traceback|cuda out of memory|nccl[^\n]*(?:error|fatal)|segmentation fault",
    re.IGNORECASE,
)
# Registered Gate-1 smoke inputs (reports/mini_a5_gate1_smoke_inputs_build_v1.json
# and the committed smoke configs).
EXPECTED_CONFIG_HASHES = {
    "std": "e38d3b2cb6180c6951a4179e94cb86b5cd142d24d34a7150bc839da2907151c9",
    "necessity": "72729eab37ea38b5d313648f2dc9929bb7950088bf4eec07e1381d754edb42f2",
}
EXPECTED_DATA = {
    "std": (
        "data/mini_a5_std_plumbing_train_v1.jsonl",
        "233217dcf1b872781972ebd60bf39a6c6f4070b683f18f0693c57588b7e2ba44",
    ),
    "necessity": (
        "data/mini_a5_necessity_plumbing_train_v1.jsonl",
        "e5cf19f39cbc6a36cb38544af1ea90a5a71c4d9295f6c8af5f442cdad516d990",
    ),
}
SMOKE_TEMPLATE = Path("configs/train/mini_a5_member_plumbing_smoke_v1.yaml")
EXPECTED_REWARD_SUFFIX = "src/rewards/cp_grpo_reward.py:compute_member_score"


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


def _checkpoint_inventory(path: Path) -> dict[str, Any]:
    files = sorted(candidate for candidate in path.rglob("*") if candidate.is_file())
    return {
        "files": len(files),
        "bytes": sum(candidate.stat().st_size for candidate in files),
        "sha256": {
            str(candidate.relative_to(path)): sha256_file(candidate)
            for candidate in files
        },
    }


def audit_single_gate1_run(
    manifest_path: Path,
    expected_mode: str,
    *,
    expected_config_sha: str | None = None,
    expected_data: tuple[str, str] | None = None,
) -> dict[str, Any]:
    if expected_mode not in {"std", "necessity"}:
        raise ValueError("expected mode must be std or necessity")
    expected_config_sha = expected_config_sha or EXPECTED_CONFIG_HASHES[expected_mode]
    data_path_str, expected_data_sha = expected_data or EXPECTED_DATA[expected_mode]
    data_path = Path(data_path_str)

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
    log_text = (
        log_path.read_text(encoding="utf-8", errors="replace")
        if log_path.is_file()
        else ""
    )
    cp_marker_lines = [line for line in log_text.splitlines() if CP_MARKER in line]
    experiment_log = checkpoint_path / "experiment_log.jsonl"
    experiment_rows: list[dict[str, Any]] = []
    marker_errors: list[str] = []
    if experiment_log.is_file():
        for line_number, line in enumerate(
            experiment_log.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                marker_errors.append(f"invalid experiment-log row {line_number}: {error}")
                continue
            if isinstance(row, dict):
                experiment_rows.append(row)
            else:
                marker_errors.append(f"experiment-log row {line_number} is not an object")

    training_rows = [
        row
        for row in experiment_rows
        if row.get("step") == 1
        and isinstance(row.get("actor"), dict)
        and isinstance(row.get("reward"), dict)
    ]
    config_reward = str(
        config.get("worker", {}).get("reward", {}).get("reward_function", "")
    )
    checkpoint = checkpoint_path / "global_step_1"
    checkpoint_inventory = (
        _checkpoint_inventory(checkpoint)
        if checkpoint.is_dir()
        else {"files": 0, "bytes": 0, "sha256": {}}
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
        and sha256_file(config_path) == expected_config_sha
        and manifest.get("config_hash") == expected_config_sha,
        "config_mode_reward_and_budget_exact": config.get("algorithm", {}).get(
            "pair_group_mode"
        )
        == "member"
        and config_reward.endswith(EXPECTED_REWARD_SUFFIX)
        and config.get("trainer", {}).get("max_steps") == 1
        and config.get("data", {}).get("rollout_batch_size") == 16
        and config.get("worker", {}).get("rollout", {}).get("n") == 5
        and config.get("data", {}).get("train_files") == str(data_path),
        "fixed_data_hash_exact": data_path.is_file()
        and sha256_file(data_path) == expected_data_sha,
        "registration_marker_exact": registration.get("status") == "registered"
        and registration.get("registration_commit")
        == manifest.get("registration_commit")
        and registration_marker_path.is_file()
        and sha256_file(registration_marker_path)
        == manifest.get("registration_marker_sha256")
        and registration.get("smoke_optimizer_steps_authorized_per_mode") == 1,
        "easyr1_revision_and_patch_exact": manifest.get("easyr1_revision")
        == "dd71bbd252694f5f850213eec15795b6b88d9fea"
        and overlay_snapshot_path.is_file()
        and sha256_file(overlay_snapshot_path)
        == manifest.get("easyr1_worktree_patch_sha256")
        == registration.get("easyr1_worktree_diff_sha256"),
        "training_log_present_without_fatal_signature": bool(log_text)
        and FATAL_PATTERN.search(log_text) is None,
        "member_mode_no_joint_branch_evidence": not cp_marker_lines
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
        "cp_marker_lines": len(cp_marker_lines),
        "training_log_rows": len(training_rows),
        "checkpoint_inventory": checkpoint_inventory,
        "artifact_sha256": {
            "manifest": sha256_file(manifest_path),
            "effective_config": sha256_file(config_path)
            if config_path.is_file()
            else None,
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


def build_audit(std_manifest: Path, necessity_manifest: Path) -> dict[str, Any]:
    std = audit_single_gate1_run(std_manifest, "std")
    necessity = audit_single_gate1_run(necessity_manifest, "necessity")
    ends = [_parse_time(std["end_time_utc"]), _parse_time(necessity["end_time_utc"])]
    starts = [
        _parse_time(std["start_time_utc"]),
        _parse_time(necessity["start_time_utc"]),
    ]
    sequential = (
        all(ends)
        and all(starts)
        and (ends[0] <= starts[1] or ends[1] <= starts[0])
    )
    std_config = Path(str(_read(std_manifest).get("config_path", "")))
    necessity_config = Path(str(_read(necessity_manifest).get("config_path", "")))
    combined_checks = {
        "std_run_passed": std["status"] == "pass",
        "necessity_run_passed": necessity["status"] == "pass",
        "sequential_nonoverlapping_runs": bool(sequential),
        "std_config_matched_diff_vs_member_smoke": std_config.is_file()
        and not matched_diff_check(std_config, SMOKE_TEMPLATE),
        "necessity_config_matched_diff_vs_member_smoke": necessity_config.is_file()
        and not matched_diff_check(necessity_config, SMOKE_TEMPLATE),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "pass" if all(combined_checks.values()) else "fail",
        "checks": combined_checks,
        "std": std,
        "necessity": necessity,
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
            "# Mini-A5 Gate-1 Plumbing Smoke Audit V1",
            "",
            "Status:",
            f"- Independent engineering audit: `{payload['status']}`.",
            "- This audit authorizes zero main-arm optimizer steps and makes no PI gate decision.",
            "",
            "Evidence:",
            f"- Machine artifact: `{machine_path}`.",
            f"- std run: `{payload['std']['manifest']}`; checks passed `{sum(payload['std']['checks'].values())}/{len(payload['std']['checks'])}`.",
            f"- necessity run: `{payload['necessity']['manifest']}`; checks passed `{sum(payload['necessity']['checks'].values())}/{len(payload['necessity']['checks'])}`.",
            f"- std checkpoint inventory: `{payload['std']['checkpoint_inventory']['files']}` files / `{payload['std']['checkpoint_inventory']['bytes']}` bytes.",
            f"- necessity checkpoint inventory: `{payload['necessity']['checkpoint_inventory']['files']}` files / `{payload['necessity']['checkpoint_inventory']['bytes']}` bytes.",
            "",
            "Checks:",
            "| Check | Result |",
            "| --- | --- |",
            *checks,
            "",
            "Problems:",
            f"- std errors: `{payload['std']['errors']}`.",
            f"- necessity errors: `{payload['necessity']['errors']}`.",
            "",
            "Decision:",
            "- A pass establishes only the registered one-step plumbing path on the two Gate-1 corpora.",
            "- The main completion arms stay gated on the Gate-1 registration marker and launcher refusals.",
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
    parser.add_argument("--std-manifest", type=Path, required=True)
    parser.add_argument("--necessity-manifest", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    payload = build_audit(args.std_manifest, args.necessity_manifest)
    _atomic_write(
        args.json_output,
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
    )
    _atomic_write(args.markdown_output, render_markdown(payload, args.json_output))
    print(json.dumps({"status": payload["status"], "checks": payload["checks"]}))
    if payload["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
