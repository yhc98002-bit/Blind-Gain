#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.watch_anchor_checkpoints import (
    process_step,
    refresh_usage_snapshot_if_needed,
    relocate_merged,
    require_code_bundle,
    wait_for_evaluation_marker,
)
from scripts.watch_pilot_checkpoints import PILOT_CODE_BUNDLE_PATHS, code_bundle_hash


ROOT = Path(__file__).resolve().parents[1]
RECOVERY_CODE_BUNDLE_PATHS = (
    *PILOT_CODE_BUNDLE_PATHS,
    ROOT / "scripts/watch_pilot_completed_parent_checkpoints.py",
)


def recovery_code_bundle_hash() -> str:
    return code_bundle_hash(RECOVERY_CODE_BUNDLE_PATHS)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def validate_recovery_inputs(parent: dict[str, Any], failed_watcher: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if parent.get("job_type") != "m3_mechanical_pilot_arm":
        errors.append("parent_job_type")
    if parent.get("status") != "complete" or parent.get("exit_code") != 0:
        errors.append("parent_not_complete")
    if parent.get("artifacts_exist") is not True:
        errors.append("parent_artifacts_unverified")
    if failed_watcher.get("job_type") != "pilot_checkpoint_retention_watch":
        errors.append("failed_watcher_job_type")
    if failed_watcher.get("status") != "fail" or failed_watcher.get("exit_code") == 0:
        errors.append("watcher_not_failed")
    expected_parent = failed_watcher.get("parent_training_run")
    observed_parent = f"experiments/runs/{parent.get('run_id', '')}"
    if expected_parent != observed_parent:
        errors.append("watcher_parent_mismatch")
    return errors


def execution_plan() -> tuple[tuple[int, str], ...]:
    return (
        (40, "relocate_after_merge"),
        (60, "retain_for_registered_evaluation"),
        (80, "relocate_after_merge"),
        (100, "retain_final_on_shared"),
        (60, "relocate_after_registered_evaluation"),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--run-manifest", type=Path, required=True)
    parser.add_argument("--failed-watcher-manifest", type=Path, required=True)
    parser.add_argument("--node", choices=("an12", "an29"), required=True)
    parser.add_argument("--run-label", required=True)
    parser.add_argument("--step60-evaluation-marker", type=Path, required=True)
    parser.add_argument("--expected-code-hash", required=True)
    args = parser.parse_args()
    errors = validate_recovery_inputs(
        read_json(args.run_manifest), read_json(args.failed_watcher_manifest)
    )
    if errors:
        raise ValueError(f"completed-parent recovery input errors: {errors}")
    require_code_bundle(args.expected_code_hash, RECOVERY_CODE_BUNDLE_PATHS)
    for step, action in execution_plan():
        if action == "relocate_after_registered_evaluation":
            actor_dir = args.run_root / f"global_step_{step}" / "actor"
            wait_for_evaluation_marker(
                args.step60_evaluation_marker,
                step=step,
                actor_dir=actor_dir,
            )
            require_code_bundle(args.expected_code_hash, RECOVERY_CODE_BUNDLE_PATHS)
            relocate_merged(
                actor_dir,
                args.archive_root,
                step,
                scope="pilot",
                run_label=args.run_label,
            )
            refresh_usage_snapshot_if_needed(
                step, "post_evaluation_relocation", scope="pilot"
            )
            continue
        process_step(
            run_root=args.run_root,
            archive_root=args.archive_root,
            anchor_manifest=args.run_manifest,
            step=step,
            node=args.node,
            relocate_merged_output=action == "relocate_after_merge",
            expected_code_hash=args.expected_code_hash,
            scope="pilot",
            run_label=args.run_label,
            retention_report=ROOT / "reports/pilot_raw_checkpoint_retention.md",
            evaluation_marker=None,
            code_bundle_paths=RECOVERY_CODE_BUNDLE_PATHS,
        )


if __name__ == "__main__":
    main()
