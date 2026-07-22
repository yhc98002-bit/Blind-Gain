#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any


DEFAULT_ARCHIVE_ROOT = Path(
    "/XYFS02/HDD_POOL/paratera_xy/pxy1289/blindgain_archive/"
    "login_tmp_checkpoint_archive"
)
DEFAULT_SYMLINK_ROOT = Path("/tmp/blindgain_checkpoint_archive")


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _checksum_manifest(path: Path) -> dict[Path, str]:
    records: dict[Path, str] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        digest, separator, raw_name = line.partition("  ")
        if separator != "  " or len(digest) != 64:
            raise ValueError(f"malformed checksum line {line_number}: {path}")
        try:
            int(digest, 16)
        except ValueError as error:
            raise ValueError(f"invalid SHA256 at line {line_number}: {path}") from error
        relative = Path(raw_name.removeprefix("./"))
        if relative.is_absolute() or ".." in relative.parts or relative == Path("."):
            raise ValueError(f"unsafe checksum path at line {line_number}: {raw_name}")
        if relative in records:
            raise ValueError(f"duplicate checksum path: {relative}")
        records[relative] = digest
    if not records:
        raise ValueError(f"empty checksum manifest: {path}")
    return records


def _direct_child(path: Path, root: Path, *, label: str) -> Path:
    if path.is_symlink():
        raise ValueError(f"{label} must not be a symlink: {path}")
    resolved = path.resolve(strict=True)
    expected_root = root.resolve(strict=True)
    if resolved.parent != expected_root:
        raise ValueError(f"{label} is outside the allowlisted root: {path}")
    return resolved


def validate_entry(
    entry: dict[str, Any],
    *,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    symlink_root: Path = DEFAULT_SYMLINK_ROOT,
) -> dict[str, Any]:
    destination = _direct_child(Path(str(entry["destination"])), archive_root, label="archive")
    source_link = Path(str(entry["source_symlink"]))
    expected_link_root = symlink_root.resolve(strict=True)
    if not source_link.is_symlink() or source_link.parent.resolve(strict=True) != expected_link_root:
        raise ValueError(f"source is not an allowlisted symlink: {source_link}")
    if source_link.resolve(strict=True) != destination:
        raise ValueError(f"source symlink does not target the archive: {source_link}")

    failed = _read_object(Path(str(entry["failed_run_manifest"])))
    replacement = _read_object(Path(str(entry["replacement_run_manifest"])))
    if failed.get("status") != "fail" or failed.get("exit_code") in {None, 0}:
        raise ValueError("source run is not a recorded failure")
    if replacement.get("status") != "complete" or replacement.get("exit_code") != 0:
        raise ValueError("replacement run is not complete")
    if failed.get("seed") != replacement.get("seed") or failed.get("arm") != replacement.get("arm"):
        raise ValueError("failed and replacement runs do not identify the same seed/arm")

    manifest_path = Path(str(entry["checksum_manifest"]))
    expected = _checksum_manifest(manifest_path)
    observed_paths: set[Path] = set()
    observed_bytes = 0
    observed_hashes: dict[Path, str] = {}
    for current in sorted(destination.rglob("*")):
        if current.is_symlink():
            raise ValueError(f"archive contains a symlink: {current}")
        if not current.is_file():
            continue
        relative = current.relative_to(destination)
        observed_paths.add(relative)
        observed_bytes += current.stat().st_size
        observed_hashes[relative] = _sha256(current)
    if observed_paths != set(expected):
        missing = sorted(str(path) for path in set(expected) - observed_paths)
        extra = sorted(str(path) for path in observed_paths - set(expected))
        raise ValueError(f"archive file set differs from checksum manifest: missing={missing}, extra={extra}")
    mismatches = sorted(str(path) for path in expected if observed_hashes[path] != expected[path])
    if mismatches:
        raise ValueError(f"archive SHA256 mismatch: {mismatches}")

    expected_files = int(entry["expected_files"])
    expected_bytes = int(entry["expected_bytes"])
    if len(observed_paths) != expected_files or observed_bytes != expected_bytes:
        raise ValueError(
            "archive count/size mismatch: "
            f"found {len(observed_paths)}/{observed_bytes}, expected {expected_files}/{expected_bytes}"
        )
    return {
        "destination": str(destination),
        "source_symlink": str(source_link),
        "failed_run_id": failed.get("run_id"),
        "replacement_run_id": replacement.get("run_id"),
        "file_count": len(observed_paths),
        "size_bytes": observed_bytes,
        "checksum_manifest": str(manifest_path),
        "checksum_manifest_sha256": _sha256(manifest_path),
        "all_file_hashes_match": True,
    }


def retire_archives(
    plan_path: Path,
    output_path: Path,
    *,
    execute: bool,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    symlink_root: Path = DEFAULT_SYMLINK_ROOT,
) -> dict[str, Any]:
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite operation output: {output_path}")
    plan = _read_object(plan_path)
    entries = plan.get("entries")
    if plan.get("status") != "approved_for_exact_retirement" or not isinstance(entries, list) or not entries:
        raise ValueError("retirement plan is not explicitly approved and nonempty")
    validated = [
        validate_entry(entry, archive_root=archive_root, symlink_root=symlink_root)
        for entry in entries
    ]
    payload: dict[str, Any] = {
        "schema_version": "blind-gains.superseded-archive-retirement.v1",
        "status": "validated_not_executed",
        "plan": str(plan_path),
        "plan_sha256": _sha256(plan_path),
        "validated_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "entries": validated,
        "total_files": sum(item["file_count"] for item in validated),
        "total_bytes": sum(item["size_bytes"] for item in validated),
        "execute_requested": execute,
    }
    _atomic_json(output_path, payload)
    if not execute:
        return payload

    for index, item in enumerate(validated):
        destination = Path(item["destination"])
        source_link = Path(item["source_symlink"])
        retiring = destination.with_name(f".{destination.name}.retiring.{os.getpid()}")
        if retiring.exists():
            raise FileExistsError(f"retirement staging path exists: {retiring}")
        os.replace(destination, retiring)
        shutil.rmtree(retiring)
        source_link.unlink()
        item["deleted"] = True
        item["deleted_at_utc"] = dt.datetime.now(dt.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        payload["entries"][index] = item
        payload["status"] = "deleting"
        _atomic_json(output_path, payload)
    payload["status"] = "complete"
    payload["completed_at_utc"] = dt.datetime.now(dt.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    _atomic_json(output_path, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    result = retire_archives(args.plan, args.output, execute=args.execute)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
