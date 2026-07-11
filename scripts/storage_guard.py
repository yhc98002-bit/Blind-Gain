#!/usr/bin/env python3
from __future__ import annotations

import argparse
import functools
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ops.storage_guard import (
    DEFAULT_SCRATCH_FLOOR_BYTES,
    DEFAULT_SHARED_FLOOR_BYTES,
    DEFAULT_SHARED_QUOTA_BYTES,
    append_guard_log,
    allocated_bytes_from_snapshot,
    check_storage,
)


DEFAULT_QUOTA_ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289")
DEFAULT_USAGE_SNAPSHOT = ROOT / "reports" / "storage_usage_snapshot.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Refuse writes that violate Blind Gains storage floors.")
    parser.add_argument("--tier", choices=("S", "T"), required=True)
    parser.add_argument("--path", type=Path, required=True)
    parser.add_argument("--operation", required=True)
    parser.add_argument("--required-bytes", type=int, required=True)
    parser.add_argument("--shared-quota-root", type=Path, default=DEFAULT_QUOTA_ROOT)
    parser.add_argument("--shared-quota-bytes", type=int, default=DEFAULT_SHARED_QUOTA_BYTES)
    parser.add_argument("--shared-floor-bytes", type=int, default=DEFAULT_SHARED_FLOOR_BYTES)
    parser.add_argument("--shared-usage-snapshot", type=Path, default=DEFAULT_USAGE_SNAPSHOT)
    parser.add_argument("--snapshot-max-age-seconds", type=int, default=6 * 60 * 60)
    parser.add_argument("--scratch-floor-bytes", type=int, default=DEFAULT_SCRATCH_FLOOR_BYTES)
    parser.add_argument("--log", type=Path, default=ROOT / "logs" / "storage_guard.jsonl")
    parser.add_argument(
        "--allow-memory-filesystem",
        action="store_true",
        help="Only for disposable staging tests; never use for process-survival artifacts.",
    )
    args = parser.parse_args()

    usage_probe = functools.partial(
        allocated_bytes_from_snapshot,
        args.shared_usage_snapshot,
        max_age_seconds=args.snapshot_max_age_seconds,
    )
    result = check_storage(
        tier=args.tier,
        path=args.path,
        operation=args.operation,
        required_bytes=args.required_bytes,
        shared_quota_root=args.shared_quota_root,
        shared_quota_bytes=args.shared_quota_bytes,
        shared_floor_bytes=args.shared_floor_bytes,
        scratch_floor_bytes=args.scratch_floor_bytes,
        usage_probe=usage_probe,
        reject_memory_filesystem=not args.allow_memory_filesystem,
    )
    append_guard_log(args.log, result)
    print(json.dumps(asdict(result), sort_keys=True))
    raise SystemExit(0 if result.allowed else 75)


if __name__ == "__main__":
    main()
