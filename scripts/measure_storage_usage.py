#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import json
import os
import subprocess
import time
from pathlib import Path

from src.ops.storage_guard import DEFAULT_SHARED_QUOTA_BYTES


DEFAULT_ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289")
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "reports" / "storage_usage_snapshot.json"


def _measure(path: Path, timeout_seconds: int) -> tuple[str, int]:
    completed = subprocess.run(
        ["du", "-sx", "--block-size=1", str(path)],
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    value = int(completed.stdout.split(maxsplit=1)[0])
    return str(path), value


def _parse_project_listing(output: str, root: Path) -> int:
    expected = str(root.resolve())
    matches: list[int] = []
    for line in output.splitlines():
        fields = line.split(maxsplit=2)
        if len(fields) == 3 and fields[0].isdigit() and fields[2] == expected:
            matches.append(int(fields[0]))
    if len(matches) != 1 or matches[0] <= 0:
        raise RuntimeError(f"could not resolve one positive Lustre project ID for {expected}")
    return matches[0]


def _parse_project_quota_kib(output: str, root: Path) -> tuple[int, int]:
    """Parse Lustre's two-line filesystem row without trusting human units."""
    expected = str(root.resolve())
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    for index, line in enumerate(lines[:-1]):
        if line == expected:
            fields = lines[index + 1].split()
            if len(fields) < 5 or not fields[0].isdigit() or not fields[4].isdigit():
                break
            return int(fields[0]), int(fields[4])
    raise RuntimeError(f"could not parse Lustre project quota row for {expected}")


def _measure_lustre_project(root: Path, timeout_seconds: int) -> dict[str, object] | None:
    try:
        listing = subprocess.run(
            ["lfs", "project", "-d", str(root)],
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    project_id = _parse_project_listing(listing.stdout, root)
    quota = subprocess.run(
        ["lfs", "quota", "-p", str(project_id), str(root)],
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    used_kib, file_count = _parse_project_quota_kib(quota.stdout, root)
    return {
        "measurement": "Lustre project-quota allocated KiB from lfs quota -p",
        "used_bytes": used_kib * 1024,
        "project_id": project_id,
        "project_file_count": file_count,
        "components": {f"lustre_project_id:{project_id}": used_kib * 1024},
    }


def measure(root: Path, *, workers: int, timeout_seconds: int) -> dict[str, object]:
    root = root.resolve()
    started = time.monotonic()
    lustre = _measure_lustre_project(root, timeout_seconds)
    if lustre is None:
        before = sorted(path for path in root.iterdir())
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            components = dict(executor.map(lambda path: _measure(path, timeout_seconds), before))
        after = sorted(path for path in root.iterdir())
        if before != after:
            raise RuntimeError("quota-root top-level entries changed during measurement")
        measurement = "parallel GNU du -sx --block-size=1 over every direct quota-root child"
        used_bytes = sum(components.values())
        extra: dict[str, object] = {}
    else:
        components = dict(lustre["components"])
        measurement = str(lustre["measurement"])
        used_bytes = int(lustre["used_bytes"])
        extra = {
            "project_id": lustre["project_id"],
            "project_file_count": lustre["project_file_count"],
        }
    quota_bytes = DEFAULT_SHARED_QUOTA_BYTES
    return {
        "schema_version": 1,
        "status": "pass",
        "measurement": measurement,
        "quota_root": str(root),
        "quota_bytes": quota_bytes,
        "used_bytes": used_bytes,
        "free_bytes": quota_bytes - used_bytes,
        "measured_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_seconds": round(time.monotonic() - started, 3),
        "components": components,
        **extra,
    }


def atomic_write(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout-seconds", type=int, default=7200)
    args = parser.parse_args()
    payload = measure(args.root, workers=args.workers, timeout_seconds=args.timeout_seconds)
    atomic_write(args.output, payload)
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
