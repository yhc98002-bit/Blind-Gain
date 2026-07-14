#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from scripts.watch_anchor_checkpoints import (
    CODE_BUNDLE_PATHS,
    code_bundle_hash,
    process_step,
    require_code_bundle,
)


ROOT = Path(__file__).resolve().parents[1]
RESUME60_STEPS = (80, 100)
RESUME60_CODE_BUNDLE_PATHS = (
    *CODE_BUNDLE_PATHS,
    ROOT / "scripts/watch_pilot_resume60_checkpoints.py",
)


def resume60_code_bundle_hash() -> str:
    return code_bundle_hash(RESUME60_CODE_BUNDLE_PATHS)


def relocation_plan() -> dict[int, str]:
    return {80: "relocate_after_merge", 100: "retain_final_on_shared"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--run-manifest", type=Path, required=True)
    parser.add_argument("--node", choices=("an12", "an21", "an29"), required=True)
    parser.add_argument("--run-label", required=True)
    parser.add_argument("--expected-code-hash", required=True)
    args = parser.parse_args()
    require_code_bundle(args.expected_code_hash, RESUME60_CODE_BUNDLE_PATHS)
    for step in RESUME60_STEPS:
        process_step(
            run_root=args.run_root,
            archive_root=args.archive_root,
            anchor_manifest=args.run_manifest,
            step=step,
            node=args.node,
            relocate_merged_output=step != 100,
            expected_code_hash=args.expected_code_hash,
            scope="pilot_resume60",
            run_label=args.run_label,
            retention_report=ROOT / "reports/pilot_raw_checkpoint_retention.md",
            evaluation_marker=None,
            code_bundle_paths=RESUME60_CODE_BUNDLE_PATHS,
        )


if __name__ == "__main__":
    main()
