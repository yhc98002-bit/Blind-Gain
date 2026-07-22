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
from typing import Any, Callable

from src.ops.storage_guard import (
    DEFAULT_SHARED_FLOOR_BYTES,
    DEFAULT_SHARED_QUOTA_BYTES,
    GuardResult,
    StorageGuardRefusal,
    allocated_bytes_from_snapshot,
    append_guard_log,
    check_storage,
)


ROOT = Path(__file__).resolve().parents[1]
SHARED_QUOTA_ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289")
SHARED_USAGE_SNAPSHOT = ROOT / "reports/storage_usage_snapshot.json"
CHECKSUM_NAME = "merged_checkpoint.source.sha256"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite restore report: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.partial")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _checksum_records(archive: Path) -> list[dict[str, Any]]:
    checksum = archive / CHECKSUM_NAME
    if not checksum.is_file():
        raise FileNotFoundError(f"archive checksum manifest is absent: {checksum}")
    records: list[dict[str, Any]] = []
    observed: set[str] = set()
    for line_number, line in enumerate(
        checksum.read_text(encoding="utf-8").splitlines(), start=1
    ):
        digest, separator, relative_text = line.partition("  ")
        relative = Path(relative_text)
        if (
            separator != "  "
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
            or relative.is_absolute()
            or ".." in relative.parts
            or relative_text in observed
        ):
            raise ValueError(f"unsafe checksum entry at line {line_number}")
        source = archive / relative
        if not source.is_file() or source.is_symlink():
            raise FileNotFoundError(f"archive file is absent or unsafe: {source}")
        observed.add(relative_text)
        stat = source.stat()
        records.append(
            {
                "file": relative.as_posix(),
                "sha256": digest,
                "size_bytes": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
            }
        )
    if not records:
        raise ValueError("archive checksum manifest is empty")
    return records


def _copy_verified(
    archive: Path,
    destination: Path,
    records: list[dict[str, Any]],
) -> None:
    for record in records:
        relative = Path(record["file"])
        source = archive / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256()
        copied = 0
        with source.open("rb") as reader, target.open("xb") as writer:
            for chunk in iter(lambda: reader.read(8 * 1024 * 1024), b""):
                writer.write(chunk)
                digest.update(chunk)
                copied += len(chunk)
            writer.flush()
            os.fsync(writer.fileno())
        if (
            copied != record["size_bytes"]
            or digest.hexdigest() != record["sha256"]
            or source.stat().st_size != record["size_bytes"]
            or source.stat().st_mtime_ns != record["mtime_ns"]
            or _sha256(target) != record["sha256"]
        ):
            raise RuntimeError(f"restore verification failed: {source}")


def restore_merged_checkpoint_for_evaluation(
    *,
    archive: Path,
    destination: Path,
    relocation_marker: Path,
    r19_marker: Path,
    output: Path,
    storage_check: Callable[[int], GuardResult] | None = None,
    guard_log: Path | None = None,
) -> dict[str, Any]:
    archive = archive.resolve()
    destination = destination.absolute()
    if not archive.is_dir() or archive.is_symlink():
        raise ValueError(f"archive must be a real directory: {archive}")
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"restore destination already exists: {destination}")
    records = _checksum_records(archive)
    total_bytes = sum(record["size_bytes"] for record in records)

    relocation = _read_json(relocation_marker)
    relocation_records = {
        (item.get("file"), item.get("sha256"), item.get("size_bytes"))
        for item in relocation.get("files", [])
        if isinstance(item, dict)
    }
    expected_records = {
        (record["file"], record["sha256"], record["size_bytes"])
        for record in records
    }
    if (
        relocation.get("status") != "merged_checkpoint_relocated"
        or Path(str(relocation.get("archive_path", ""))).resolve() != archive
        or Path(str(relocation.get("source_path", ""))).absolute() != destination
        or relocation_records != expected_records
    ):
        raise ValueError("relocation marker does not bind the requested restore")

    r19 = _read_json(r19_marker)
    archive_index = archive / "model.safetensors.index.json"
    if (
        r19.get("schema_version") != "blind-gains.pilot-step-eval-marker.v1"
        or r19.get("status") != "complete"
        or r19.get("global_step") != 60
        or Path(str(r19.get("checkpoint_path", ""))).absolute() != destination
        or r19.get("checkpoint_index_sha256") != _sha256(archive_index)
    ):
        raise ValueError("R19 marker does not bind the archived step-60 checkpoint")

    if storage_check is None:
        guard = check_storage(
            tier="S",
            path=destination,
            operation="restore_pilot_step60_for_registered_evaluation",
            required_bytes=total_bytes,
            shared_quota_root=SHARED_QUOTA_ROOT,
            shared_quota_bytes=DEFAULT_SHARED_QUOTA_BYTES,
            shared_floor_bytes=DEFAULT_SHARED_FLOOR_BYTES,
            usage_probe=functools.partial(
                allocated_bytes_from_snapshot,
                SHARED_USAGE_SNAPSHOT,
                max_age_seconds=6 * 60 * 60,
            ),
        )
    else:
        guard = storage_check(total_bytes)
    if guard_log is not None:
        append_guard_log(guard_log, guard)
    if not guard.allowed:
        raise StorageGuardRefusal(guard)

    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = Path(
        tempfile.mkdtemp(
            prefix=f".{destination.name}.restore.partial.",
            dir=str(destination.parent),
        )
    )
    published = False
    try:
        _copy_verified(archive, partial, records)
        os.replace(partial, destination)
        published = True
    finally:
        if not published and partial.exists():
            shutil.rmtree(partial)

    payload = {
        "schema_version": "blind-gains.pilot-step60-eval-restore.v1",
        "status": "restored_for_registered_evaluation",
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "archive": str(archive),
        "destination": str(destination),
        "source_preserved": True,
        "total_bytes": total_bytes,
        "file_count": len(records),
        "files": [
            {key: record[key] for key in ("file", "sha256", "size_bytes")}
            for record in records
        ],
        "relocation_marker": str(relocation_marker),
        "relocation_marker_sha256": _sha256(relocation_marker),
        "r19_marker": str(r19_marker),
        "r19_marker_sha256": _sha256(r19_marker),
        "storage_guard": asdict(guard),
        "performance_values_opened": False,
        "scientific_gate_decision": None,
    }
    _atomic_json(output, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--relocation-marker", type=Path, required=True)
    parser.add_argument("--r19-marker", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--guard-log", type=Path, default=ROOT / "logs/storage_guard.jsonl"
    )
    args = parser.parse_args()
    payload = restore_merged_checkpoint_for_evaluation(
        archive=args.archive,
        destination=args.destination,
        relocation_marker=args.relocation_marker,
        r19_marker=args.r19_marker,
        output=args.output,
        guard_log=args.guard_log,
    )
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
