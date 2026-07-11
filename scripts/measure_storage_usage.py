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


def measure(root: Path, *, workers: int, timeout_seconds: int) -> dict[str, object]:
    root = root.resolve()
    before = sorted(path for path in root.iterdir())
    started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        components = dict(executor.map(lambda path: _measure(path, timeout_seconds), before))
    after = sorted(path for path in root.iterdir())
    if before != after:
        raise RuntimeError("quota-root top-level entries changed during measurement")
    quota_bytes = 500 * 1024**3
    used_bytes = sum(components.values())
    return {
        "schema_version": 1,
        "status": "pass",
        "measurement": "parallel GNU du -sx --block-size=1 over every direct quota-root child",
        "quota_root": str(root),
        "quota_bytes": quota_bytes,
        "used_bytes": used_bytes,
        "free_bytes": quota_bytes - used_bytes,
        "measured_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_seconds": round(time.monotonic() - started, 3),
        "components": components,
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
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    args = parser.parse_args()
    payload = measure(args.root, workers=args.workers, timeout_seconds=args.timeout_seconds)
    atomic_write(args.output, payload)
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
