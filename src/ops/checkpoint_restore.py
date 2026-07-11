from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any, Callable


CHECKSUM_NAME = "raw_training_state.source.sha256"
RELOCATION_MARKER = "RAW_STATE_RELOCATED.json"
RESTORE_MARKER = "RAW_STATE_RESTORED_FOR_RESUME.json"
SHARD_RE = re.compile(r"^(model|optim)_world_size_([1-9][0-9]*)_rank_([0-9]+)\.pt$")


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


def load_raw_checksum_manifest(path: Path) -> dict[str, str]:
    records: dict[str, str] = {}
    families: dict[str, set[int]] = {"model": set(), "optim": set()}
    world_sizes: set[int] = set()
    for line in path.read_text(encoding="ascii").splitlines():
        digest, separator, name = line.partition("  ")
        match = SHARD_RE.fullmatch(name)
        if len(digest) != 64 or separator != "  " or match is None:
            raise ValueError(f"malformed raw checksum entry: {line!r}")
        if name in records:
            raise ValueError(f"duplicate raw checksum entry: {name}")
        family, world_size_text, rank_text = match.groups()
        world_size = int(world_size_text)
        rank = int(rank_text)
        if rank >= world_size:
            raise ValueError(f"raw checksum rank exceeds world size: {name}")
        records[name] = digest
        world_sizes.add(world_size)
        families[family].add(rank)
    if len(world_sizes) != 1:
        raise ValueError(f"raw checksum has inconsistent world sizes: {world_sizes}")
    world_size = next(iter(world_sizes))
    expected_ranks = set(range(world_size))
    for family, ranks in families.items():
        if ranks != expected_ranks:
            raise ValueError(f"raw checksum has incomplete {family} ranks: {sorted(ranks)}")
    return records


def restore_raw_checkpoint(
    actor_dir: Path,
    archive_dir: Path,
    *,
    guard: Callable[[int], None] | None = None,
) -> dict[str, Any]:
    actor_dir = actor_dir.resolve()
    archive_dir = archive_dir.resolve()
    relocation_marker = json.loads(
        (actor_dir / RELOCATION_MARKER).read_text(encoding="utf-8")
    )
    if Path(str(relocation_marker.get("archive_path", ""))).resolve() != archive_dir:
        raise ValueError("raw relocation marker points to a different archive")
    checksum_path = archive_dir / CHECKSUM_NAME
    checksums = load_raw_checksum_manifest(checksum_path)

    source_records: list[dict[str, Any]] = []
    required_bytes = 0
    for name, expected_digest in checksums.items():
        source = archive_dir / name
        if not source.is_file():
            raise FileNotFoundError(f"archived raw shard is missing: {source}")
        observed_digest = _sha256(source)
        if observed_digest != expected_digest:
            raise RuntimeError(f"archived raw shard checksum mismatch: {source}")
        size = source.stat().st_size
        target = actor_dir / name
        if target.exists():
            if not target.is_file() or target.stat().st_size != size or _sha256(target) != expected_digest:
                raise RuntimeError(f"shared raw shard conflicts with archive: {target}")
        else:
            required_bytes += size
        source_records.append(
            {"file": name, "bytes": size, "sha256": expected_digest}
        )

    if guard is not None:
        guard(required_bytes)

    restored: list[str] = []
    reused: list[str] = []
    for record in source_records:
        name = str(record["file"])
        source = archive_dir / name
        target = actor_dir / name
        if target.exists():
            reused.append(name)
            continue
        partial = target.with_name(f".{target.name}.restore.partial")
        if partial.exists():
            raise FileExistsError(f"stale raw restore partial exists: {partial}")
        with source.open("rb") as source_handle, partial.open("xb") as target_handle:
            shutil.copyfileobj(source_handle, target_handle, length=8 * 1024 * 1024)
            target_handle.flush()
            os.fsync(target_handle.fileno())
        if partial.stat().st_size != record["bytes"] or _sha256(partial) != record["sha256"]:
            raise RuntimeError(f"restored raw shard failed checksum before publish: {partial}")
        os.replace(partial, target)
        restored.append(name)

    for record in source_records:
        target = actor_dir / str(record["file"])
        if target.stat().st_size != record["bytes"] or _sha256(target) != record["sha256"]:
            raise RuntimeError(f"published raw shard failed final checksum: {target}")

    payload = {
        "schema_version": "blind-gains.raw-checkpoint-restore.v1",
        "status": "restored_for_optimizer_resume",
        "restored_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_dir": str(actor_dir),
        "archive_dir": str(archive_dir),
        "checksum_manifest": str(checksum_path),
        "checksum_manifest_sha256": _sha256(checksum_path),
        "required_bytes": required_bytes,
        "restored_files": restored,
        "reused_verified_files": reused,
        "files": source_records,
        "archive_retained": True,
    }
    _atomic_json(actor_dir / RESTORE_MARKER, payload)
    return payload
