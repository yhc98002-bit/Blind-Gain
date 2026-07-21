#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from scripts.watch_anchor_checkpoints import (
    CODE_BUNDLE_PATHS,
    code_bundle_hash,
    process_step,
    refresh_usage_snapshot_if_needed,
    relocate_merged,
    require_code_bundle,
    wait_for_evaluation_marker,
)


ROOT = Path(__file__).resolve().parents[1]
PILOT_STEPS = (20, 40, 60, 80, 100)
PILOT_CODE_BUNDLE_PATHS = (*CODE_BUNDLE_PATHS, ROOT / "scripts/watch_pilot_checkpoints.py")


def pilot_code_bundle_hash() -> str:
    return code_bundle_hash(PILOT_CODE_BUNDLE_PATHS)


def relocation_plan() -> dict[int, str]:
    return {
        20: "relocate_after_merge",
        40: "relocate_after_merge",
        60: "relocate_after_registered_evaluation",
        80: "relocate_after_merge",
        100: "retain_final_on_shared",
    }


def execution_plan() -> tuple[tuple[int, str], ...]:
    """Keep the evaluated step on shared without blocking later raw retention."""
    return (
        (20, "relocate_after_merge"),
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
    parser.add_argument("--node", choices=("an12", "an29"), required=True)
    parser.add_argument("--run-label", required=True)
    parser.add_argument("--step60-evaluation-marker", type=Path, required=True)
    parser.add_argument("--expected-code-hash", required=True)
    args = parser.parse_args()
    require_code_bundle(args.expected_code_hash, PILOT_CODE_BUNDLE_PATHS)
    for step, action in execution_plan():
        if action == "relocate_after_registered_evaluation":
            actor_dir = args.run_root / f"global_step_{step}" / "actor"
            wait_for_evaluation_marker(
                args.step60_evaluation_marker,
                step=step,
                actor_dir=actor_dir,
            )
            require_code_bundle(args.expected_code_hash, PILOT_CODE_BUNDLE_PATHS)
            relocate_merged(
                actor_dir,
                args.archive_root,
                step,
                scope="pilot",
                run_label=args.run_label,
            )
            refresh_usage_snapshot_if_needed(
                step,
                "post_evaluation_relocation",
                scope="pilot",
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
            code_bundle_paths=PILOT_CODE_BUNDLE_PATHS,
        )


if __name__ == "__main__":
    main()
