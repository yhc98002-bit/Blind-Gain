#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import functools
import hashlib
import json
import os
import socket
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ops.storage_guard import (  # noqa: E402
    StorageGuardRefusal,
    allocated_bytes_from_snapshot,
    append_guard_log,
    check_storage,
)


MARKER_NAME = "MERGED_CHECKPOINT_RELOCATED.json"
CHECKSUM_NAME = "merged_checkpoint.source.sha256"
SHARED_QUOTA_ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289")
SHARED_USAGE_SNAPSHOT = ROOT / "reports" / "storage_usage_snapshot.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _validated_files(source_dir: Path) -> list[Path]:
    index_path = source_dir / "model.safetensors.index.json"
    if not index_path.is_file():
        raise FileNotFoundError("merged Hugging Face checkpoint index is missing")
    index = json.loads(index_path.read_text(encoding="utf-8"))
    weight_map = index.get("weight_map")
    if not isinstance(weight_map, dict) or not weight_map:
        raise ValueError("merged Hugging Face checkpoint index has no weight map")
    shard_names = set(weight_map.values())
    if any(not isinstance(name, str) or Path(name).name != name for name in shard_names):
        raise ValueError("merged checkpoint index contains an unsafe shard path")
    missing = sorted(name for name in shard_names if not (source_dir / name).is_file())
    if missing:
        raise FileNotFoundError(f"merged checkpoint index references missing shards: {missing}")
    files = sorted(path for path in source_dir.rglob("*") if path.is_file())
    if not files:
        raise ValueError("merged Hugging Face checkpoint directory is empty")
    return files


def _copy_file(source: Path, destination: Path) -> tuple[str, int]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    size = 0
    with source.open("rb") as reader, destination.open("xb") as writer:
        for chunk in iter(lambda: reader.read(8 * 1024 * 1024), b""):
            writer.write(chunk)
            digest.update(chunk)
            size += len(chunk)
        writer.flush()
        os.fsync(writer.fileno())
    return digest.hexdigest(), size


def _remove_tree_files(root: Path) -> None:
    for path in sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if path.is_file() or path.is_symlink():
            path.unlink()
        elif path.is_dir():
            path.rmdir()
    root.rmdir()


def relocate_merged_checkpoint(
    source_dir: Path,
    archive_dir: Path,
    *,
    guard_log: Path | None = None,
) -> dict[str, Any]:
    source_dir = source_dir.resolve()
    archive_dir = archive_dir.resolve()
    if source_dir == archive_dir or source_dir in archive_dir.parents:
        raise ValueError("archive directory must be outside the merged checkpoint directory")
    if archive_dir.exists():
        raise FileExistsError(f"refusing to overwrite merged checkpoint archive: {archive_dir}")

    files = _validated_files(source_dir)
    source_stats = {
        path: (path.stat().st_size, path.stat().st_mtime_ns)
        for path in files
    }
    total_bytes = sum(size for size, _ in source_stats.values())

    scratch_guard = check_storage(
        tier="T",
        path=archive_dir,
        operation="merged_checkpoint_relocation",
        required_bytes=total_bytes,
    )
    if guard_log is not None:
        append_guard_log(guard_log, scratch_guard)
    if not scratch_guard.allowed:
        raise StorageGuardRefusal(scratch_guard)

    shared_guard = None
    marker = source_dir.parent / MARKER_NAME
    if source_dir.is_relative_to(SHARED_QUOTA_ROOT):
        shared_guard = check_storage(
            tier="S",
            path=marker,
            operation="merged_checkpoint_relocation_metadata",
            required_bytes=2 * 1024 * 1024,
            shared_quota_root=SHARED_QUOTA_ROOT,
            usage_probe=functools.partial(
                allocated_bytes_from_snapshot,
                SHARED_USAGE_SNAPSHOT,
                max_age_seconds=6 * 60 * 60,
            ),
        )
        if guard_log is not None:
            append_guard_log(guard_log, shared_guard)
        if not shared_guard.allowed:
            raise StorageGuardRefusal(shared_guard)

    partial = archive_dir.with_name(f".{archive_dir.name}.partial.{os.getpid()}")
    if partial.exists():
        raise FileExistsError(f"partial archive already exists: {partial}")
    partial.mkdir(parents=True)
    records: list[dict[str, Any]] = []
    try:
        for source in files:
            relative = source.relative_to(source_dir)
            destination = partial / relative
            source_digest, copied_size = _copy_file(source, destination)
            if source_stats[source] != (source.stat().st_size, source.stat().st_mtime_ns):
                raise RuntimeError(f"source changed during merged relocation: {source}")
            destination_digest = _sha256(destination)
            if copied_size != source_stats[source][0] or source_digest != destination_digest:
                raise RuntimeError(f"merged relocation verification failed: {source}")
            records.append(
                {"file": str(relative), "sha256": source_digest, "size_bytes": copied_size}
            )
        checksum_text = "".join(
            f"{record['sha256']}  {record['file']}\n" for record in records
        )
        checksum_path = partial / CHECKSUM_NAME
        checksum_path.write_text(checksum_text, encoding="utf-8")
        checksum_digest = _sha256(checksum_path)
        os.replace(partial, archive_dir)
    finally:
        if partial.exists():
            _remove_tree_files(partial)

    payload = {
        "status": "merged_checkpoint_relocated",
        "source_path": str(source_dir),
        "archive_path": str(archive_dir),
        "archive_node": socket.gethostname(),
        "archive_medium": "Tier T node-local scratch",
        "relocated_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "size_bytes": total_bytes,
        "checksum_manifest_sha256": checksum_digest,
        "files": records,
        "storage_guard": {
            "scratch": {
                "status": scratch_guard.status,
                "free_bytes_before": scratch_guard.free_bytes_before,
                "free_bytes_after": scratch_guard.free_bytes_after,
                "floor_bytes": scratch_guard.floor_bytes,
            },
            "shared": (
                {
                    "status": shared_guard.status,
                    "free_bytes_before": shared_guard.free_bytes_before,
                    "free_bytes_after": shared_guard.free_bytes_after,
                    "floor_bytes": shared_guard.floor_bytes,
                }
                if shared_guard is not None
                else None
            ),
        },
        "verification": "all source files were stable while copying and archive SHA256 values matched",
        "restore_note": "Restore this directory as actor/huggingface before checkpoint evaluation.",
    }
    if marker.exists():
        existing = json.loads(marker.read_text(encoding="utf-8"))
        if existing.get("archive_path") != str(archive_dir):
            raise FileExistsError(f"relocation marker points to a different archive: {marker}")
    _atomic_json(marker, payload)
    _remove_tree_files(source_dir)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--archive-dir", type=Path, required=True)
    parser.add_argument("--guard-log", type=Path, default=ROOT / "logs" / "storage_guard.jsonl")
    args = parser.parse_args()
    payload = relocate_merged_checkpoint(
        args.source_dir,
        args.archive_dir,
        guard_log=args.guard_log,
    )
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
