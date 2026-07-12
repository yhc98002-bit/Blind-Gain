#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
from typing import Any


EXPECTED_FILES = {
    "checkpoint_tracker.json",
    "experiment_config.json",
    "experiment_log.jsonl",
    "generations.log",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _replace_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.legacy-metadata.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def relocate_metadata(
    source: Path,
    destination: Path,
    run_manifest_path: Path,
) -> dict[str, Any]:
    manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))
    run_id = str(manifest.get("run_id", ""))
    existing_events = manifest.get("storage_retention_events", [])
    if (
        manifest.get("job_type") != "l3_pilot_reward_plumbing_smoke"
        or manifest.get("status") != "complete"
        or manifest.get("exit_code") != 0
    ):
        raise ValueError("legacy metadata source run is not a completed pilot reward smoke")
    if destination.exists():
        raise FileExistsError(f"legacy metadata destination already exists: {destination}")
    if not isinstance(existing_events, list) or any(
        isinstance(item, dict) and item.get("source") == str(source)
        for item in existing_events
    ):
        raise ValueError("run manifest already records this metadata relocation")
    if not source.is_dir():
        raise FileNotFoundError(f"legacy metadata source is absent: {source}")
    entries = sorted(source.iterdir())
    if any(path.is_symlink() or not path.is_file() for path in entries):
        raise ValueError("legacy metadata source contains a link, directory, or special file")
    names = {path.name for path in entries}
    if names != EXPECTED_FILES:
        raise ValueError(
            f"legacy metadata file set differs: expected={sorted(EXPECTED_FILES)} "
            f"found={sorted(names)}"
        )
    config = json.loads((source / "experiment_config.json").read_text(encoding="utf-8"))
    if config.get("trainer", {}).get("experiment_name") != run_id:
        raise ValueError("legacy metadata experiment name does not match the smoke run")
    if (
        config.get("trainer", {}).get("max_steps") != 5
        or config.get("worker", {}).get("rollout", {}).get("tensor_parallel_size") != 2
    ):
        raise ValueError("legacy metadata does not match the superseded five-step TP2 smoke")

    records = [
        {
            "file": path.name,
            "sha256": _sha256(path),
            "size_bytes": path.stat().st_size,
        }
        for path in entries
    ]
    temporary = destination.with_name(f".{destination.name}.partial.{os.getpid()}")
    temporary.mkdir(parents=True)
    try:
        for path in entries:
            shutil.copy2(path, temporary / path.name)
        for record in records:
            copied = temporary / record["file"]
            if copied.stat().st_size != record["size_bytes"] or _sha256(copied) != record["sha256"]:
                raise RuntimeError(f"legacy metadata copy failed verification: {copied}")
        checksum_text = "".join(
            f"{record['sha256']}  {record['file']}\n" for record in records
        )
        (temporary / "source.sha256").write_text(checksum_text, encoding="ascii")
        payload = {
            "schema_version": "blind-gains.legacy-smoke-metadata-relocation.v1",
            "status": "relocated",
            "classification": "superseded",
            "run_id": run_id,
            "source": str(source),
            "destination": str(destination),
            "size_bytes": sum(record["size_bytes"] for record in records),
            "file_count": len(records),
            "files": records,
            "recorded_at_utc": dt.datetime.now(dt.timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
        }
        (temporary / "relocation.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)

    for record in records:
        copied = destination / record["file"]
        if copied.stat().st_size != record["size_bytes"] or _sha256(copied) != record["sha256"]:
            raise RuntimeError(f"published legacy metadata failed verification: {copied}")
    for path in entries:
        path.unlink()
    source.rmdir()
    if source.exists():
        raise RuntimeError(f"legacy metadata source remains after relocation: {source}")

    event = {
        "event": "legacy_checkpoint_metadata_relocation",
        "status": "superseded-metadata-relocated",
        "source": str(source),
        "destination": str(destination),
        "size_bytes": sum(record["size_bytes"] for record in records),
        "relocation_record": str(destination / "relocation.json"),
        "recorded_at_utc": payload["recorded_at_utc"],
    }
    events = manifest.setdefault("storage_retention_events", [])
    events.append(event)
    _replace_json(run_manifest_path, manifest)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--run-manifest", type=Path, required=True)
    args = parser.parse_args()
    payload = relocate_metadata(args.source, args.destination, args.run_manifest)
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
