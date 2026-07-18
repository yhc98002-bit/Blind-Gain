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
M5_STEPS = (150, 200, 250, 300, 350, 400)
M5_CODE_BUNDLE_PATHS = (*CODE_BUNDLE_PATHS, ROOT / "scripts/watch_m5_checkpoints.py")


def m5_code_bundle_hash() -> str:
    return code_bundle_hash(M5_CODE_BUNDLE_PATHS)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--run-manifest", type=Path, required=True)
    parser.add_argument("--node", choices=("an12", "an29"), required=True)
    parser.add_argument("--run-label", required=True)
    parser.add_argument("--expected-code-hash", required=True)
    parser.add_argument("--resume-after-step", type=int, default=0)
    args = parser.parse_args()
    require_code_bundle(args.expected_code_hash, M5_CODE_BUNDLE_PATHS)

    # Evaluation and merged-checkpoint relocation are intentionally separate.
    # This queue only makes an immutable merge and enforces latest-raw retention.
    if args.resume_after_step not in {0, 100, 150}:
        raise ValueError("M5 resume-after step must be 0, 100, or 150")
    for step in (item for item in M5_STEPS if item > args.resume_after_step):
        process_step(
            run_root=args.run_root,
            archive_root=args.archive_root,
            anchor_manifest=args.run_manifest,
            step=step,
            node=args.node,
            relocate_merged_output=False,
            expected_code_hash=args.expected_code_hash,
            scope="m5_longhorizon",
            run_label=args.run_label,
            retention_report=ROOT / "reports/m5_raw_checkpoint_retention.md",
            code_bundle_paths=M5_CODE_BUNDLE_PATHS,
        )


if __name__ == "__main__":
    main()
