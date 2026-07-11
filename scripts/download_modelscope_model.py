#!/usr/bin/env python3
from __future__ import annotations

import argparse
import functools
import json
import os
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
    parser.add_argument("--checkout-manifest", type=Path)
    parser.add_argument(
        "--allow-memory-filesystem",
        action="store_true",
        help="Allow disposable model staging on /dev/shm; never use for persistent artifacts.",
    )
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
        reject_memory_filesystem=not args.allow_memory_filesystem,
    )
    append_guard_log(Path(args.guard_log), guard)
    if not guard.allowed:
        raise StorageGuardRefusal(guard)
    local_dir.parent.mkdir(parents=True, exist_ok=True)
    path = snapshot_download(args.model_id, revision=args.revision, local_dir=str(local_dir))
    digest = sha256_tree(path)
    files = sorted(item for item in Path(path).rglob("*") if item.is_file())
    total_bytes = sum(item.stat().st_size for item in files)
    if args.checkout_manifest:
        if args.checkout_manifest.exists():
            raise FileExistsError(
                f"refusing to overwrite model checkout manifest: {args.checkout_manifest}"
            )
        args.checkout_manifest.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "blind-gains.ephemeral-model-checkout.v1",
            "status": "pass",
            "model_id": args.model_id,
            "source": "ModelScope",
            "source_url": f"https://modelscope.cn/models/{args.model_id}",
            "revision": args.revision,
            "license": args.license,
            "redistribution": args.redistribution,
            "local_path": str(path),
            "storage_tier": args.storage_tier,
            "memory_filesystem": args.allow_memory_filesystem,
            "file_count": len(files),
            "total_bytes": total_bytes,
            "sha256_tree": digest,
        }
        temporary = args.checkout_manifest.with_name(
            f".{args.checkout_manifest.name}.partial.{os.getpid()}"
        )
        temporary.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, args.checkout_manifest)
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
