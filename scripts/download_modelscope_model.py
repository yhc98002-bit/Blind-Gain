#!/usr/bin/env python3
from __future__ import annotations

import argparse
import functools
import sys
from pathlib import Path

from modelscope import snapshot_download

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.model_registry import ModelArtifact, append_artifact, sha256_tree
from src.ops.storage_guard import (
    StorageGuardRefusal,
    allocated_bytes_from_snapshot,
    append_guard_log,
    check_storage,
)


SHARED_QUOTA_ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289")
SHARED_USAGE_SNAPSHOT = Path(__file__).resolve().parents[1] / "reports" / "storage_usage_snapshot.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--revision", default="master")
    parser.add_argument("--local-dir", required=True)
    parser.add_argument("--license", default="VERIFY")
    parser.add_argument("--redistribution", default="VERIFY")
    parser.add_argument("--registry", default="experiments/manifests/model_registry.jsonl")
    parser.add_argument("--notes", default="")
    parser.add_argument("--storage-tier", choices=("S", "T"), required=True)
    parser.add_argument("--expected-bytes", type=int, required=True)
    parser.add_argument("--guard-log", default="logs/storage_guard.jsonl")
    args = parser.parse_args()

    local_dir = Path(args.local_dir)
    if args.expected_bytes <= 0:
        raise ValueError("--expected-bytes must be positive")
    guard = check_storage(
        tier=args.storage_tier,
        path=local_dir,
        operation="modelscope_model_download",
        required_bytes=args.expected_bytes,
        shared_quota_root=SHARED_QUOTA_ROOT,
        usage_probe=functools.partial(
            allocated_bytes_from_snapshot,
            SHARED_USAGE_SNAPSHOT,
            max_age_seconds=6 * 60 * 60,
        ),
    )
    append_guard_log(Path(args.guard_log), guard)
    if not guard.allowed:
        raise StorageGuardRefusal(guard)
    local_dir.parent.mkdir(parents=True, exist_ok=True)
    path = snapshot_download(args.model_id, revision=args.revision, local_dir=str(local_dir))
    digest = sha256_tree(path)
    append_artifact(
        ModelArtifact(
            name=args.model_id,
            source="ModelScope",
            source_url=f"https://modelscope.cn/models/{args.model_id}",
            revision=args.revision,
            license=args.license,
            local_path=str(path),
            redistribution=args.redistribution,
            sha256=digest,
            notes=args.notes,
        ),
        args.registry,
    )
    print(path)


if __name__ == "__main__":
    main()
