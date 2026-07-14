#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any


RAW_RE = re.compile(r"^(model|optim)_world_size_(\d+)_rank_(\d+)\.pt$")
EXTRA_RE = re.compile(r"^extra_state_world_size_(\d+)_rank_(\d+)\.pt$")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _snapshot(path: Path) -> tuple[int, int]:
    stat = path.stat()
    if stat.st_size <= 0:
        raise ValueError(f"checkpoint file is empty: {path}")
    return stat.st_size, stat.st_mtime_ns


def _atomic_text(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite audit artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def audit_checkpoint(
    checkpoint_dir: Path,
    *,
    expected_step: int,
    expected_world_size: int = 4,
) -> tuple[dict[str, Any], str]:
    checkpoint_dir = checkpoint_dir.resolve()
    if checkpoint_dir.name != f"global_step_{expected_step}":
        raise ValueError("checkpoint basename does not match expected resume step")
    actor_dir = checkpoint_dir / "actor"
    if not actor_dir.is_dir():
        raise ValueError(f"actor directory is absent: {actor_dir}")

    raw: dict[str, dict[int, Path]] = {"model": {}, "optim": {}}
    unexpected_rank_files: list[str] = []
    for path in sorted(actor_dir.glob("*_world_size_*_rank_*.pt")):
        raw_match = RAW_RE.fullmatch(path.name)
        extra_match = EXTRA_RE.fullmatch(path.name)
        if raw_match:
            family, world_text, rank_text = raw_match.groups()
            world_size, rank = int(world_text), int(rank_text)
            if world_size != expected_world_size or rank in raw[family]:
                unexpected_rank_files.append(path.name)
            else:
                raw[family][rank] = path
        elif not extra_match:
            unexpected_rank_files.append(path.name)
    if unexpected_rank_files:
        raise ValueError(f"unexpected or conflicting rank files: {unexpected_rank_files}")

    expected_ranks = set(range(expected_world_size))
    for family in ("model", "optim"):
        observed = set(raw[family])
        if observed != expected_ranks:
            raise ValueError(
                f"{family} rank set mismatch: expected {sorted(expected_ranks)}, "
                f"found {sorted(observed)}"
            )

    extras: dict[int, Path] = {}
    for path in sorted(actor_dir.glob("extra_state_world_size_*_rank_*.pt")):
        match = EXTRA_RE.fullmatch(path.name)
        if not match:
            raise ValueError(f"malformed extra-state rank file: {path.name}")
        world_size, rank = map(int, match.groups())
        if world_size != expected_world_size or rank in extras:
            raise ValueError(f"unexpected or conflicting extra-state file: {path.name}")
        extras[rank] = path
    if set(extras) != expected_ranks:
        raise ValueError(
            f"extra-state rank set mismatch: expected {sorted(expected_ranks)}, "
            f"found {sorted(extras)}"
        )

    dataloader = checkpoint_dir / "dataloader.pt"
    if not dataloader.is_file():
        raise ValueError(f"dataloader state is absent: {dataloader}")

    files = [
        *(raw[family][rank] for family in ("model", "optim") for rank in sorted(expected_ranks)),
        *(extras[rank] for rank in sorted(expected_ranks)),
        dataloader,
    ]
    before = {path: _snapshot(path) for path in files}
    records = []
    for path in files:
        relative = path.relative_to(checkpoint_dir)
        size, mtime_ns = before[path]
        records.append(
            {
                "path": str(relative),
                "size_bytes": size,
                "mtime_ns": mtime_ns,
                "sha256": _sha256(path),
            }
        )
    after = {path: _snapshot(path) for path in files}
    if before != after:
        raise RuntimeError("checkpoint files changed during SHA256 audit")

    checksum_text = "".join(
        f"{record['sha256']}  {record['path']}\n" for record in records
    )
    marker_records = []
    for name in ("RAW_STATE_RELOCATED.json", "RAW_STATE_RESTORED_FOR_RESUME.json"):
        marker = actor_dir / name
        if marker.is_file():
            marker_records.append({"path": str(marker), "sha256": _sha256(marker)})
    payload = {
        "schema_version": "blind-gains.easyr1-resume-checkpoint-audit.v1",
        "status": "pass",
        "audited_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "checkpoint_dir": str(checkpoint_dir),
        "expected_step": expected_step,
        "world_size": expected_world_size,
        "model_rank_count": len(raw["model"]),
        "optimizer_rank_count": len(raw["optim"]),
        "extra_state_rank_count": len(extras),
        "file_count": len(records),
        "total_size_bytes": sum(record["size_bytes"] for record in records),
        "checksum_manifest_sha256": hashlib.sha256(checksum_text.encode("utf-8")).hexdigest(),
        "files": records,
        "markers": marker_records,
        "files_stable_during_hash": True,
    }
    return payload, checksum_text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint-dir", type=Path, required=True)
    parser.add_argument("--expected-step", type=int, required=True)
    parser.add_argument("--expected-world-size", type=int, default=4)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-sha256", type=Path, required=True)
    args = parser.parse_args()
    payload, checksums = audit_checkpoint(
        args.checkpoint_dir,
        expected_step=args.expected_step,
        expected_world_size=args.expected_world_size,
    )
    _atomic_text(args.output_sha256, checksums)
    payload["checksum_manifest"] = str(args.output_sha256.resolve())
    _atomic_text(args.output_json, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
