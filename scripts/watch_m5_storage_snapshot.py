#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from scripts.build_conservative_storage_snapshot import (
    atomic_write,
    build_snapshot,
    sha256_file,
)


ROOT = Path(__file__).resolve().parents[1]


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def utc_text(value: dt.datetime | None = None) -> str:
    return (value or utc_now()).strftime("%Y-%m-%dT%H:%M:%SZ")


def git_hash() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def snapshot_age_seconds(payload: dict[str, Any], *, now: dt.datetime) -> float:
    measured_text = payload.get("measured_at_utc")
    if not isinstance(measured_text, str):
        raise ValueError("snapshot has no measured_at_utc")
    measured = dt.datetime.fromisoformat(measured_text.replace("Z", "+00:00"))
    if measured.tzinfo is None:
        raise ValueError("snapshot timestamp has no timezone")
    age = (now - measured).total_seconds()
    if age < 0:
        raise ValueError("snapshot timestamp is future-dated")
    return age


def refresh_needed(
    payload: dict[str, Any], *, now: dt.datetime, refresh_age_seconds: int
) -> bool:
    if payload.get("status") != "pass":
        return True
    try:
        return snapshot_age_seconds(payload, now=now) >= refresh_age_seconds
    except (TypeError, ValueError):
        return True


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o664)
    try:
        os.write(descriptor, (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8"))
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_manifest(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.partial")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exact-source", type=Path, required=True)
    parser.add_argument("--exact-source-sha256", required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--target-run-manifest", type=Path, required=True)
    parser.add_argument("--reserve-bytes", type=int, required=True)
    parser.add_argument("--required-bytes", type=int, required=True)
    parser.add_argument("--floor-bytes", type=int, required=True)
    parser.add_argument("--refresh-age-seconds", type=int, default=4 * 60 * 60)
    parser.add_argument("--poll-seconds", type=int, default=300)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    if args.refresh_age_seconds <= 0 or args.poll_seconds < 0:
        raise ValueError("refresh age must be positive and poll interval nonnegative")
    source_hash = sha256_file(args.exact_source)
    if source_hash != args.exact_source_sha256:
        raise ValueError("exact source hash does not match the registered hash")
    source = json.loads(args.exact_source.read_text(encoding="utf-8"))
    args.run_dir.mkdir(parents=True, exist_ok=False)
    events = args.run_dir / "events.jsonl"
    command = " ".join(os.sys.argv)
    manifest_path = args.run_dir / "run_manifest.json"
    manifest = {
        "schema_version": "blind-gains.m5-storage-freshness-watch.v1",
        "run_id": args.run_dir.name,
        "job_type": "m5_storage_snapshot_freshness_watch",
        "node": "login",
        "gpu_ids": [],
        "tensor_parallel_width": 0,
        "replica_count": 0,
        "placement_justification": "CPU-only freshness maintenance for the fail-closed checkpoint guard.",
        "git_hash": git_hash(),
        "config_hash": hashlib.sha256(command.encode("utf-8")).hexdigest(),
        "data_manifest": str(args.exact_source),
        "data_manifest_hash": source_hash,
        "seed": None,
        "command": command,
        "start_time_utc": utc_text(),
        "end_time_utc": None,
        "status": "running",
        "performance_values_opened": False,
        "expected_artifacts": [str(events), str(args.current)],
        "deviations": [],
    }
    write_manifest(manifest_path, manifest)
    exit_code = 0
    try:
        while True:
            target = json.loads(args.target_run_manifest.read_text(encoding="utf-8"))
            if target.get("status") != "running":
                append_jsonl(
                    events,
                    {
                        "at_utc": utc_text(),
                        "event": "target_terminal",
                        "target_status": target.get("status"),
                        "performance_values_opened": False,
                    },
                )
                break
            current = json.loads(args.current.read_text(encoding="utf-8"))
            now = utc_now()
            if refresh_needed(
                current, now=now, refresh_age_seconds=args.refresh_age_seconds
            ):
                payload = build_snapshot(
                    source,
                    source_sha256=source_hash,
                    reserve_bytes=args.reserve_bytes,
                    required_bytes=args.required_bytes,
                    floor_bytes=args.floor_bytes,
                    measured_at_utc=utc_text(now),
                )
                versioned = args.current.with_name(
                    f"storage_usage_snapshot_conservative_{now.strftime('%Y%m%dT%H%M%SZ')}.json"
                )
                atomic_write(versioned, payload, replace=False)
                atomic_write(args.current, payload, replace=True)
                append_jsonl(
                    events,
                    {
                        "at_utc": utc_text(now),
                        "event": "conservative_snapshot_published",
                        "output": str(versioned),
                        "output_sha256": sha256_file(versioned),
                        "performance_values_opened": False,
                    },
                )
            else:
                append_jsonl(
                    events,
                    {
                        "at_utc": utc_text(now),
                        "event": "snapshot_still_fresh",
                        "age_seconds": snapshot_age_seconds(current, now=now),
                        "performance_values_opened": False,
                    },
                )
            if args.once:
                break
            time.sleep(args.poll_seconds)
    except Exception as error:
        exit_code = 1
        append_jsonl(
            events,
            {
                "at_utc": utc_text(),
                "event": "watcher_failed",
                "error": f"{type(error).__name__}: {error}",
                "performance_values_opened": False,
            },
        )
        raise
    finally:
        manifest.update(
            {
                "end_time_utc": utc_text(),
                "exit_code": exit_code,
                "status": "complete" if exit_code == 0 else "failed",
            }
        )
        write_manifest(manifest_path, manifest)


if __name__ == "__main__":
    main()
