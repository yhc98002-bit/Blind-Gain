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
MINI_A5_STEPS = (20, 40, 60, 80, 100, 120)
MINI_A5_CODE_BUNDLE_PATHS = (*CODE_BUNDLE_PATHS, ROOT / "scripts/watch_mini_a5_checkpoints.py")


def mini_a5_code_bundle_hash() -> str:
    return code_bundle_hash(MINI_A5_CODE_BUNDLE_PATHS)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--run-manifest", type=Path, required=True)
    parser.add_argument("--node", choices=("an12", "an29"), required=True)
    parser.add_argument("--run-label", required=True)
    parser.add_argument("--expected-code-hash", required=True)
    args = parser.parse_args()
    require_code_bundle(args.expected_code_hash, MINI_A5_CODE_BUNDLE_PATHS)

    # Registered Mini-A5 endpoints are computed only after both arms complete;
    # this watcher makes an immutable merge at every save boundary and archives
    # the raw optimizer state off-quota. Merged checkpoints stay local.
    for step in MINI_A5_STEPS:
        process_step(
            run_root=args.run_root,
            archive_root=args.archive_root,
            anchor_manifest=args.run_manifest,
            step=step,
            node=args.node,
            relocate_merged_output=False,
            expected_code_hash=args.expected_code_hash,
            scope="mini_a5_main",
            run_label=args.run_label,
            retention_report=ROOT / "reports/mini_a5_raw_checkpoint_retention.md",
            code_bundle_paths=MINI_A5_CODE_BUNDLE_PATHS,
        )


if __name__ == "__main__":
    main()
