#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
from typing import Any


EXACT_MEASUREMENT = "parallel GNU du -sx --block-size=1 over every direct quota-root child"
CONSERVATIVE_MEASUREMENT = (
    "conservative upper bound from one exact snapshot plus an explicit "
    "unmeasured-growth reserve"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_snapshot(
    source: dict[str, Any],
    *,
    source_sha256: str,
    reserve_bytes: int,
    required_bytes: int,
    floor_bytes: int,
    measured_at_utc: str,
) -> dict[str, Any]:
    if source.get("status") != "pass":
        raise ValueError("source snapshot must have pass status")
    if source.get("measurement") != EXACT_MEASUREMENT:
        raise ValueError("source must be an exact du snapshot; conservative chaining is forbidden")
    if reserve_bytes <= 0 or required_bytes < 0 or floor_bytes < 0:
        raise ValueError("reserve must be positive and write/floor budgets nonnegative")
    quota_bytes = source.get("quota_bytes")
    used_bytes = source.get("used_bytes")
    if not isinstance(quota_bytes, int) or not isinstance(used_bytes, int):
        raise ValueError("source quota_bytes and used_bytes must be integers")
    conservative_used = used_bytes + reserve_bytes
    conservative_free = quota_bytes - conservative_used
    after_write = conservative_free - required_bytes
    if after_write < floor_bytes:
        raise ValueError(
            "conservative snapshot cannot authorize the requested write: "
            f"after_write={after_write}, floor={floor_bytes}"
        )
    components = dict(source.get("components") or {})
    components["__unmeasured_growth_reserve__"] = reserve_bytes
    return {
        "schema_version": 1,
        "status": "pass",
        "measurement": CONSERVATIVE_MEASUREMENT,
        "quota_root": source["quota_root"],
        "quota_bytes": quota_bytes,
        "used_bytes": conservative_used,
        "free_bytes": conservative_free,
        "measured_at_utc": measured_at_utc,
        "components": components,
        "provenance": {
            "source_snapshot_sha256": source_sha256,
            "source_measured_at_utc": source.get("measured_at_utc"),
            "source_used_bytes": used_bytes,
            "unmeasured_growth_reserve_bytes": reserve_bytes,
            "authorized_write_bytes": required_bytes,
            "guard_floor_bytes": floor_bytes,
            "conservative_free_after_authorized_write_bytes": after_write,
            "exact_refresh_attempt": "failed after its per-component timeout",
        },
    }


def atomic_write(path: Path, payload: dict[str, Any], *, replace: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not replace:
        raise FileExistsError(f"refusing to overwrite immutable snapshot: {path}")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.partial")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--publish-current", type=Path)
    parser.add_argument("--reserve-bytes", type=int, required=True)
    parser.add_argument("--required-bytes", type=int, required=True)
    parser.add_argument("--floor-bytes", type=int, required=True)
    args = parser.parse_args()
    source = json.loads(args.source.read_text(encoding="utf-8"))
    payload = build_snapshot(
        source,
        source_sha256=sha256_file(args.source),
        reserve_bytes=args.reserve_bytes,
        required_bytes=args.required_bytes,
        floor_bytes=args.floor_bytes,
        measured_at_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    atomic_write(args.output, payload, replace=False)
    if args.publish_current is not None:
        atomic_write(args.publish_current, payload, replace=True)
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
