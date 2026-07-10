#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import socket
from pathlib import Path
from typing import Any


RAW_SHARD_RE = re.compile(r"^(model|optim)_world_size_(\d+)_rank_(\d+)\.pt$")
MARKER_NAME = "RAW_STATE_RELOCATED.json"
CHECKSUM_NAME = "raw_training_state.source.sha256"


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
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
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


def relocate_raw_checkpoint(actor_dir: Path, archive_dir: Path) -> dict[str, Any]:
    actor_dir = actor_dir.resolve()
    archive_dir = archive_dir.resolve()
    if actor_dir == archive_dir or actor_dir in archive_dir.parents:
        raise ValueError("archive directory must be outside the checkpoint actor directory")

    huggingface_dir = actor_dir / "huggingface"
    if not (huggingface_dir / "model.safetensors.index.json").is_file():
        raise FileNotFoundError("merged Hugging Face checkpoint index is missing")
    if not any(huggingface_dir.glob("*.safetensors")):
        raise FileNotFoundError("merged Hugging Face checkpoint shards are missing")

    shards = _discover_complete_shards(actor_dir)
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
        "archive_medium": "login-node local filesystem",
        "relocated_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "checksum_manifest_sha256": checksum_digest,
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
    args = parser.parse_args()
    payload = relocate_raw_checkpoint(args.actor_dir, args.archive_dir)
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
