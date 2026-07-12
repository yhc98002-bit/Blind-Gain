#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from scripts.relocate_easyr1_raw_checkpoint import (
    enforce_restored_shared_retention,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--current-step", type=int, required=True)
    parser.add_argument("--current-raw-marker", type=Path, required=True)
    parser.add_argument("--run-manifest", type=Path, required=True)
    parser.add_argument("--retention-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite restored-retention output: {args.output}")
    marker = json.loads(args.current_raw_marker.read_text(encoding="utf-8"))
    if marker.get("status") != "raw_training_state_relocated_due_to_shared_quota":
        raise ValueError("current raw relocation marker is not verified")
    merged_digest = marker.get("merged_checkpoint_sha256")
    if not isinstance(merged_digest, str) or len(merged_digest) != 64:
        raise ValueError("current raw relocation marker lacks the merged-checkpoint hash")
    records = enforce_restored_shared_retention(
        run_shared_root=args.run_root,
        current_step=args.current_step,
        merged_checkpoint_sha256=merged_digest,
        run_manifest=args.run_manifest,
        retention_report=args.retention_report,
    )
    if not records:
        raise RuntimeError("no verified restored shared raw state was found to expire")
    payload = {
        "status": "pass",
        "current_step": args.current_step,
        "merged_checkpoint_sha256": merged_digest,
        "expired_restored_states": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(f".{args.output.name}.partial.{os.getpid()}")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, args.output)
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
