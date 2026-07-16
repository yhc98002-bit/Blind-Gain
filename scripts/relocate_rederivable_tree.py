#!/usr/bin/env python3
from __future__ import annotations

import argparse
import functools
import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.ops.storage_guard import (
    DEFAULT_SHARED_FLOOR_BYTES,
    DEFAULT_SHARED_QUOTA_BYTES,
    Tier,
    allocated_bytes_from_snapshot,
    check_storage,
)


SCRATCH_FLOOR_BYTES = 40 * 1024**3
SHARED_QUOTA_ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289")
SHARED_USAGE_SNAPSHOT = (
    Path(__file__).resolve().parents[1] / "reports/storage_usage_snapshot.json"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory_tree(root: Path) -> list[dict[str, Any]]:
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"source must be a real directory: {root}")
    records: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"source contains a symlink: {path}")
        if not path.is_file():
            continue
        stat = path.stat()
        records.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size_bytes": stat.st_size,
                "sha256": _sha256(path),
            }
        )
    return records


def relocate_tree(
    *,
    source: Path,
    destination: Path,
    manifest_path: Path,
    operation: str,
    destination_tier: Tier,
    shared_quota_root: Path = SHARED_QUOTA_ROOT,
    shared_usage_snapshot: Path = SHARED_USAGE_SNAPSHOT,
) -> dict[str, Any]:
    source = source.resolve()
    destination = destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"destination already exists: {destination}")
    if manifest_path.exists():
        raise FileExistsError(f"manifest already exists: {manifest_path}")

    source_inventory = inventory_tree(source)
    source_bytes = sum(record["size_bytes"] for record in source_inventory)
    destination.parent.mkdir(parents=True, exist_ok=True)
    guard_arguments: dict[str, Any] = {
        "tier": destination_tier,
        "path": destination.parent,
        "operation": operation,
        "required_bytes": source_bytes,
    }
    if destination_tier == "S":
        guard_arguments.update(
            shared_quota_root=shared_quota_root,
            shared_quota_bytes=DEFAULT_SHARED_QUOTA_BYTES,
            shared_floor_bytes=DEFAULT_SHARED_FLOOR_BYTES,
            usage_probe=functools.partial(
                allocated_bytes_from_snapshot,
                shared_usage_snapshot,
                max_age_seconds=6 * 60 * 60,
            ),
        )
    else:
        guard_arguments["scratch_floor_bytes"] = SCRATCH_FLOOR_BYTES
    guard = check_storage(**guard_arguments)
    if not guard.allowed:
        raise RuntimeError(f"storage_guard refused relocation: {guard.reason}")

    partial = Path(
        tempfile.mkdtemp(
            prefix=f".{destination.name}.partial.", dir=str(destination.parent)
        )
    )
    published = False
    try:
        shutil.copytree(source, partial, dirs_exist_ok=True, copy_function=shutil.copy2)
        copied_inventory = inventory_tree(partial)
        if copied_inventory != source_inventory:
            raise RuntimeError("copied tree differs from source inventory")
        if inventory_tree(source) != source_inventory:
            raise RuntimeError("source changed while relocation was in progress")
        os.replace(partial, destination)
        published = True

        shutil.rmtree(source)
        source.symlink_to(destination, target_is_directory=True)
        payload = {
            "schema_version": "blind-gains.rederivable-relocation.v1",
            "status": "relocated",
            "operation": operation,
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
            "source": str(source),
            "destination": str(destination),
            "source_replaced_by_symlink": True,
            "total_bytes": source_bytes,
            "file_count": len(source_inventory),
            "files": source_inventory,
            "storage_guard": asdict(guard),
        }
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_manifest = manifest_path.with_name(
            f".{manifest_path.name}.partial.{os.getpid()}"
        )
        temporary_manifest.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(temporary_manifest, manifest_path)
        return payload
    finally:
        if not published and partial.exists():
            shutil.rmtree(partial)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--operation", required=True)
    parser.add_argument("--destination-tier", choices=("S", "T"), required=True)
    parser.add_argument("--shared-quota-root", type=Path, default=SHARED_QUOTA_ROOT)
    parser.add_argument(
        "--shared-usage-snapshot", type=Path, default=SHARED_USAGE_SNAPSHOT
    )
    args = parser.parse_args()
    payload = relocate_tree(
        source=args.source,
        destination=args.destination,
        manifest_path=args.manifest,
        operation=args.operation,
        destination_tier=args.destination_tier,
        shared_quota_root=args.shared_quota_root,
        shared_usage_snapshot=args.shared_usage_snapshot,
    )
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
