#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import functools
import hashlib
import json
import os
import re
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


RAW_SHARD_RE = re.compile(r"^(model|optim)_world_size_(\d+)_rank_(\d+)\.pt$")
STEP_RE = re.compile(r"^global_step_(\d+)$")
MARKER_NAME = "RAW_STATE_RELOCATED.json"
CHECKSUM_NAME = "raw_training_state.source.sha256"
SHARED_QUOTA_ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289")
SHARED_USAGE_SNAPSHOT = ROOT / "reports" / "storage_usage_snapshot.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _copy_with_sha256(source: Path, destination: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    temporary = destination.with_name(f".{destination.name}.partial.{os.getpid()}")
    if temporary.exists():
        raise FileExistsError(f"temporary archive file already exists: {temporary}")
    try:
        with source.open("rb") as reader, temporary.open("xb") as writer:
            for chunk in iter(lambda: reader.read(8 * 1024 * 1024), b""):
                writer.write(chunk)
                digest.update(chunk)
                size += len(chunk)
            writer.flush()
            os.fsync(writer.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()
    return digest.hexdigest(), size


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _discover_complete_shards(actor_dir: Path) -> list[Path]:
    parsed: dict[str, tuple[int, set[int]]] = {}
    shards: list[Path] = []
    for path in sorted(actor_dir.glob("*_world_size_*_rank_*.pt")):
        match = RAW_SHARD_RE.fullmatch(path.name)
        if not match:
            continue
        family, world_size_text, rank_text = match.groups()
        world_size = int(world_size_text)
        rank = int(rank_text)
        if family not in parsed:
            parsed[family] = (world_size, set())
        registered_world_size, ranks = parsed[family]
        if registered_world_size != world_size:
            raise ValueError(f"mixed world sizes for {family} shards")
        if rank in ranks:
            raise ValueError(f"duplicate {family} rank {rank}")
        ranks.add(rank)
        shards.append(path)

    for family in ("model", "optim"):
        if family not in parsed:
            raise ValueError(f"missing {family} raw checkpoint shards")
        world_size, ranks = parsed[family]
        expected = set(range(world_size))
        if ranks != expected:
            raise ValueError(
                f"incomplete {family} shards: expected ranks {sorted(expected)}, found {sorted(ranks)}"
            )
    if parsed["model"][0] != parsed["optim"][0]:
        raise ValueError("model and optimizer shard world sizes differ")
    return shards


def _merged_checkpoint_records(actor_dir: Path) -> tuple[list[dict[str, Any]], str]:
    huggingface_dir = actor_dir / "huggingface"
    index_path = huggingface_dir / "model.safetensors.index.json"
    if not index_path.is_file():
        raise FileNotFoundError("merged Hugging Face checkpoint index is missing")
    index = json.loads(index_path.read_text(encoding="utf-8"))
    weight_map = index.get("weight_map")
    if not isinstance(weight_map, dict) or not weight_map:
        raise ValueError("merged Hugging Face checkpoint index has no weight map")
    shard_names = sorted(set(weight_map.values()))
    if any(not isinstance(name, str) or Path(name).name != name for name in shard_names):
        raise ValueError("merged checkpoint index contains an unsafe shard path")

    files = [index_path]
    for name in shard_names:
        shard = huggingface_dir / name
        if not shard.is_file():
            raise FileNotFoundError(f"merged Hugging Face checkpoint shard is missing: {name}")
        files.append(shard)
    records = [
        {"file": str(path.relative_to(actor_dir)), "sha256": _sha256(path), "size_bytes": path.stat().st_size}
        for path in files
    ]
    digest = hashlib.sha256(
        "".join(f"{record['sha256']}  {record['file']}\n" for record in records).encode("utf-8")
    ).hexdigest()
    return records, digest


def _parse_step(path: Path) -> int:
    match = STEP_RE.fullmatch(path.name)
    if not match:
        raise ValueError(f"expected a global_step_N directory, found: {path}")
    return int(match.group(1))


def _verify_raw_archive(actor_archive: Path) -> dict[str, Any]:
    checksum_path = actor_archive / CHECKSUM_NAME
    if not checksum_path.is_file():
        raise FileNotFoundError(f"raw archive checksum manifest is missing: {checksum_path}")
    records: list[dict[str, Any]] = []
    listed_names: set[str] = set()
    for line in checksum_path.read_text(encoding="ascii").splitlines():
        digest, separator, name = line.partition("  ")
        if not separator or len(digest) != 64 or Path(name).name != name:
            raise ValueError(f"malformed raw archive checksum line: {line!r}")
        if name in listed_names:
            raise ValueError(f"duplicate raw archive checksum entry: {name}")
        listed_names.add(name)
        path = actor_archive / name
        if not path.is_file():
            raise FileNotFoundError(f"raw archive file is missing: {path}")
        actual = _sha256(path)
        if actual != digest:
            raise RuntimeError(f"raw archive checksum mismatch: {path}")
        records.append({"file": name, "sha256": digest, "size_bytes": path.stat().st_size})
    raw_names = {path.name for path in actor_archive.glob("*_world_size_*_rank_*.pt")}
    if raw_names != listed_names:
        raise RuntimeError(
            f"raw archive manifest/file set differs: listed={sorted(listed_names)} files={sorted(raw_names)}"
        )
    allowed = listed_names | {CHECKSUM_NAME}
    unexpected = sorted(
        path.name
        for path in actor_archive.iterdir()
        if path.name not in allowed and path.name != "huggingface"
    )
    if unexpected:
        raise RuntimeError(f"raw archive contains unexpected entries: {unexpected}")
    merged_sibling = actor_archive / "huggingface"
    if merged_sibling.exists():
        if not merged_sibling.is_dir():
            raise RuntimeError("raw archive huggingface sibling is not a directory")
        if not (merged_sibling / "model.safetensors.index.json").is_file():
            raise RuntimeError("raw archive merged sibling has no model index")
        if not (merged_sibling / "merged_checkpoint.source.sha256").is_file():
            raise RuntimeError("raw archive merged sibling has no checksum manifest")
    if not records:
        raise ValueError(f"raw archive checksum manifest is empty: {checksum_path}")
    return {
        "path": str(actor_archive),
        "size_bytes": sum(record["size_bytes"] for record in records),
        "checksum_manifest_sha256": _sha256(checksum_path),
        "files": records,
    }


def _append_retention_report(report_path: Path, *, current_step: int, records: list[dict[str, Any]]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    if not report_path.exists():
        report_path.write_text(
            "# Raw Checkpoint Retention Events\n\n"
            "Entries are written and fsynced before retention-expired bytes are removed.\n\n"
            "| Recorded UTC | New verified step | Retention-expired path | Size bytes | Checksum manifest SHA256 |\n"
            "| --- | ---: | --- | ---: | --- |\n",
            encoding="utf-8",
        )
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = "".join(
        f"| {timestamp} | {current_step} | `{record['path']}` | {record['size_bytes']} | "
        f"`{record['checksum_manifest_sha256']}` |\n"
        for record in records
    )
    descriptor = os.open(report_path, os.O_APPEND | os.O_WRONLY)
    try:
        os.write(descriptor, lines.encode("utf-8"))
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _set_manifest_retention_event(
    manifest_path: Path,
    *,
    current_step: int,
    merged_checkpoint_sha256: str,
    records: list[dict[str, Any]],
    status: str,
) -> None:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    event = {
        "event": "raw_state_retention",
        "current_step": current_step,
        "merged_checkpoint_sha256": merged_checkpoint_sha256,
        "status": status,
        "recorded_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expired_states": records,
    }
    events = payload.setdefault("storage_retention_events", [])
    matching_index = next(
        (index for index, existing in enumerate(events) if existing.get("current_step") == current_step),
        None,
    )
    if matching_index is None:
        events.append(event)
    else:
        events[matching_index] = event
    _atomic_json(manifest_path, payload)


def enforce_latest_raw_retention(
    *,
    run_archive_root: Path,
    current_step: int,
    merged_checkpoint_sha256: str,
    run_manifest: Path,
    retention_report: Path,
) -> list[dict[str, Any]]:
    run_archive_root = run_archive_root.resolve()
    candidates: list[tuple[int, Path]] = []
    if run_archive_root.exists():
        for step_dir in run_archive_root.glob("global_step_*"):
            try:
                step = _parse_step(step_dir)
            except ValueError:
                continue
            actor_archive = step_dir / "actor"
            if step < current_step and actor_archive.is_dir():
                candidates.append((step, actor_archive))
    if not candidates:
        return []

    verified = []
    for step, actor_archive in sorted(candidates):
        record = _verify_raw_archive(actor_archive)
        record["step"] = step
        record["retention_reason"] = "retention-expired after a newer merged checkpoint was hash-verified"
        verified.append(record)

    _append_retention_report(retention_report, current_step=current_step, records=verified)
    _set_manifest_retention_event(
        run_manifest,
        current_step=current_step,
        merged_checkpoint_sha256=merged_checkpoint_sha256,
        records=verified,
        status="listed_before_deletion",
    )
    for record in verified:
        actor_archive = Path(record["path"])
        for file_record in record["files"]:
            (actor_archive / file_record["file"]).unlink()
        (actor_archive / CHECKSUM_NAME).unlink()
        if not any(actor_archive.iterdir()):
            actor_archive.rmdir()
        step_dir = actor_archive.parent
        if not any(step_dir.iterdir()):
            step_dir.rmdir()
    _set_manifest_retention_event(
        run_manifest,
        current_step=current_step,
        merged_checkpoint_sha256=merged_checkpoint_sha256,
        records=verified,
        status="deleted_after_verification",
    )
    return verified


def relocate_raw_checkpoint(
    actor_dir: Path,
    archive_dir: Path,
    *,
    run_archive_root: Path | None = None,
    run_manifest: Path | None = None,
    retention_report: Path | None = None,
    guard_log: Path | None = None,
) -> dict[str, Any]:
    actor_dir = actor_dir.resolve()
    archive_dir = archive_dir.resolve()
    if actor_dir == archive_dir or actor_dir in archive_dir.parents:
        raise ValueError("archive directory must be outside the checkpoint actor directory")

    shards = _discover_complete_shards(actor_dir)
    merged_records, merged_digest = _merged_checkpoint_records(actor_dir)
    retention_records: list[dict[str, Any]] = []
    retention_args = (run_archive_root, run_manifest, retention_report)
    shared_guard_result = None
    if actor_dir.is_relative_to(SHARED_QUOTA_ROOT):
        shared_guard_result = check_storage(
            tier="S",
            path=actor_dir / MARKER_NAME,
            operation="raw_checkpoint_relocation_metadata",
            required_bytes=2 * 1024 * 1024,
            shared_quota_root=SHARED_QUOTA_ROOT,
            usage_probe=functools.partial(
                allocated_bytes_from_snapshot,
                SHARED_USAGE_SNAPSHOT,
                max_age_seconds=6 * 60 * 60,
            ),
        )
        if guard_log is not None:
            append_guard_log(guard_log, shared_guard_result)
        if not shared_guard_result.allowed:
            raise StorageGuardRefusal(shared_guard_result)
    if any(item is not None for item in retention_args):
        if not all(item is not None for item in retention_args):
            raise ValueError(
                "run_archive_root, run_manifest, and retention_report must be supplied together"
            )
        current_step = _parse_step(actor_dir.parent)
        retention_records = enforce_latest_raw_retention(
            run_archive_root=run_archive_root,  # type: ignore[arg-type]
            current_step=current_step,
            merged_checkpoint_sha256=merged_digest,
            run_manifest=run_manifest,  # type: ignore[arg-type]
            retention_report=retention_report,  # type: ignore[arg-type]
        )

    required_bytes = sum(path.stat().st_size for path in shards if not (archive_dir / path.name).exists())
    guard_result = check_storage(
        tier="T",
        path=archive_dir,
        operation="raw_checkpoint_relocation",
        required_bytes=required_bytes,
    )
    if guard_log is not None:
        append_guard_log(guard_log, guard_result)
    if not guard_result.allowed:
        raise StorageGuardRefusal(guard_result)

    archive_dir.mkdir(parents=True, exist_ok=True)
    allowed_existing = {path.name for path in shards} | {CHECKSUM_NAME}
    unexpected = sorted(
        path.name for path in archive_dir.iterdir() if path.name not in allowed_existing
    )
    if unexpected:
        raise FileExistsError(f"archive directory contains unexpected files: {unexpected}")

    records = []
    for source in shards:
        before = source.stat()
        destination = archive_dir / source.name
        if destination.exists():
            source_digest = _sha256(source)
            destination_digest = _sha256(destination)
            copied_size = destination.stat().st_size
        else:
            source_digest, copied_size = _copy_with_sha256(source, destination)
            destination_digest = _sha256(destination)
        after = source.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise RuntimeError(f"source shard changed during relocation: {source}")
        if copied_size != before.st_size or destination.stat().st_size != before.st_size:
            raise RuntimeError(f"size mismatch after relocating {source.name}")
        if source_digest != destination_digest:
            raise RuntimeError(f"SHA256 mismatch after relocating {source.name}")
        records.append(
            {"file": source.name, "sha256": source_digest, "size_bytes": before.st_size}
        )

    checksum_path = archive_dir / CHECKSUM_NAME
    checksum_text = "".join(f"{record['sha256']}  {record['file']}\n" for record in records)
    checksum_path.write_text(checksum_text, encoding="ascii")
    checksum_digest = _sha256(checksum_path)
    payload = {
        "status": "raw_training_state_relocated_due_to_shared_quota",
        "archive_node": socket.gethostname(),
        "archive_path": str(archive_dir),
        "archive_medium": "Tier T node-local scratch",
        "relocated_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "checksum_manifest_sha256": checksum_digest,
        "merged_checkpoint_sha256": merged_digest,
        "merged_checkpoint_files": merged_records,
        "retention_expired_states": retention_records,
        "storage_guard": {
            "scratch": {
                "status": guard_result.status,
                "free_bytes_before": guard_result.free_bytes_before,
                "free_bytes_after": guard_result.free_bytes_after,
                "floor_bytes": guard_result.floor_bytes,
            },
            "shared": (
                {
                    "status": shared_guard_result.status,
                    "free_bytes_before": shared_guard_result.free_bytes_before,
                    "free_bytes_after": shared_guard_result.free_bytes_after,
                    "floor_bytes": shared_guard_result.floor_bytes,
                }
                if shared_guard_result is not None
                else None
            ),
        },
        "files": records,
        "verification": (
            "source bytes hashed while copying; archive bytes re-read and SHA256/size matched "
            "before source removal"
        ),
        "restore_note": (
            "Restore all listed model/optimizer shards before optimizer-state resume. "
            "The merged Hugging Face checkpoint remains in shared storage."
        ),
    }
    marker = actor_dir / MARKER_NAME
    if marker.exists():
        existing = json.loads(marker.read_text(encoding="utf-8"))
        if existing.get("archive_path") != str(archive_dir):
            raise FileExistsError(f"relocation marker points to a different archive: {marker}")
    _atomic_json(marker, payload)
    for source in shards:
        source.unlink()
    if any(source.exists() for source in shards):
        raise RuntimeError("one or more raw source shards remain after relocation")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--actor-dir", type=Path, required=True)
    parser.add_argument("--archive-dir", type=Path, required=True)
    parser.add_argument("--run-archive-root", type=Path)
    parser.add_argument("--run-manifest", type=Path)
    parser.add_argument("--retention-report", type=Path)
    parser.add_argument("--guard-log", type=Path, default=ROOT / "logs" / "storage_guard.jsonl")
    args = parser.parse_args()
    payload = relocate_raw_checkpoint(
        args.actor_dir,
        args.archive_dir,
        run_archive_root=args.run_archive_root,
        run_manifest=args.run_manifest,
        retention_report=args.retention_report,
        guard_log=args.guard_log,
    )
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
