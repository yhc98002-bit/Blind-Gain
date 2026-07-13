#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from scripts.watch_anchor_checkpoints import CODE_BUNDLE_PATHS, code_bundle_hash, process_step, require_code_bundle


ROOT = Path(__file__).resolve().parents[1]
RESUME_STEPS = (40, 60, 80, 100)
RESUME_CODE_BUNDLE_PATHS = (*CODE_BUNDLE_PATHS, ROOT / "scripts/watch_pilot_resume_checkpoints.py")


def resume_code_bundle_hash() -> str:
    return code_bundle_hash(RESUME_CODE_BUNDLE_PATHS)


def relocation_plan() -> dict[int, str]:
    return {
        40: "relocate_after_merge",
        60: "relocate_after_registered_evaluation",
        80: "relocate_after_merge",
        100: "retain_final_on_shared",
    }


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
    require_code_bundle(args.expected_code_hash, RESUME_CODE_BUNDLE_PATHS)
    plan = relocation_plan()
    for step in RESUME_STEPS:
        process_step(
            run_root=args.run_root,
            archive_root=args.archive_root,
            anchor_manifest=args.run_manifest,
            step=step,
            node=args.node,
            relocate_merged_output=step != 100,
            expected_code_hash=args.expected_code_hash,
            scope="pilot_resume20",
            run_label=args.run_label,
            retention_report=ROOT / "reports/pilot_raw_checkpoint_retention.md",
            evaluation_marker=(
                args.step60_evaluation_marker
                if plan[step] == "relocate_after_registered_evaluation"
                else None
            ),
            code_bundle_paths=RESUME_CODE_BUNDLE_PATHS,
        )


if __name__ == "__main__":
    main()
