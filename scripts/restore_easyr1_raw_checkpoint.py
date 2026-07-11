#!/usr/bin/env python3
from __future__ import annotations

import argparse
import functools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ops.checkpoint_restore import restore_raw_checkpoint  # noqa: E402
from src.ops.storage_guard import (  # noqa: E402
    StorageGuardRefusal,
    allocated_bytes_from_snapshot,
    append_guard_log,
    check_storage,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--actor-dir", type=Path, required=True)
    parser.add_argument("--archive-dir", type=Path, required=True)
    parser.add_argument(
        "--quota-root", type=Path, default=Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289")
    )
    parser.add_argument(
        "--usage-snapshot", type=Path, default=ROOT / "reports/storage_usage_snapshot.json"
    )
    parser.add_argument("--guard-log", type=Path, default=ROOT / "logs/storage_guard.jsonl")
    args = parser.parse_args()

    def guard(required_bytes: int) -> None:
        result = check_storage(
            tier="S",
            path=args.actor_dir,
            operation="restore_easyr1_raw_checkpoint",
            required_bytes=required_bytes,
            shared_quota_root=args.quota_root,
            usage_probe=functools.partial(
                allocated_bytes_from_snapshot, args.usage_snapshot
            ),
        )
        append_guard_log(args.guard_log, result)
        if not result.allowed:
            raise StorageGuardRefusal(result)

    payload = restore_raw_checkpoint(args.actor_dir, args.archive_dir, guard=guard)
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
