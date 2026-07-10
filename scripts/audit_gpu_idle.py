#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any


def _timestamp(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp lacks timezone: {value}")
    return parsed.astimezone(dt.timezone.utc)


def audit_samples(
    samples: list[dict[str, Any]],
    since: dt.datetime,
    until: dt.datetime,
    max_idle_minutes: float = 30.0,
    max_gap_minutes: float = 12.0,
    active_memory_mib: int = 1024,
    active_utilization_pct: int = 5,
) -> dict[str, Any]:
    if until <= since:
        raise ValueError("until must be later than since")
    grouped: dict[tuple[str, int], list[tuple[dt.datetime, dict[str, Any]]]] = defaultdict(list)
    for sample in samples:
        timestamp = _timestamp(str(sample["ts"]))
        if since <= timestamp <= until:
            grouped[(str(sample["node"]), int(sample["gpu_index"]))].append((timestamp, sample))

    violations: list[dict[str, Any]] = []
    idle_intervals: list[dict[str, Any]] = []
    expected_devices = [(node, index) for node in ("an12", "an29") for index in range(8)]
    for device in expected_devices:
        observations = sorted(grouped.get(device, []), key=lambda item: item[0])
        if not observations:
            violations.append({"type": "missing_coverage", "node": device[0], "gpu_index": device[1]})
            continue
        if (observations[0][0] - since).total_seconds() > max_gap_minutes * 60:
            violations.append(
                {
                    "type": "late_coverage_start",
                    "node": device[0],
                    "gpu_index": device[1],
                    "first_sample_utc": observations[0][0].isoformat(),
                }
            )
        if (until - observations[-1][0]).total_seconds() > max_gap_minutes * 60:
            violations.append(
                {
                    "type": "stale_coverage_end",
                    "node": device[0],
                    "gpu_index": device[1],
                    "last_sample_utc": observations[-1][0].isoformat(),
                }
            )

        segment: list[tuple[dt.datetime, dict[str, Any]]] = []

        def flush() -> None:
            nonlocal segment
            if not segment:
                return
            duration_minutes = (segment[-1][0] - segment[0][0]).total_seconds() / 60
            interval = {
                "node": device[0],
                "gpu_index": device[1],
                "start_utc": segment[0][0].isoformat(),
                "end_utc": segment[-1][0].isoformat(),
                "duration_minutes_between_samples": duration_minutes,
                "n_samples": len(segment),
                "max_memory_used_mib": max(int(item[1]["memory_used_mib"]) for item in segment),
                "max_util_gpu_pct": max(int(item[1]["util_gpu_pct"]) for item in segment),
            }
            idle_intervals.append(interval)
            if duration_minutes > max_idle_minutes:
                violations.append({"type": "idle_over_limit", **interval})
            segment = []

        for timestamp, sample in observations:
            idle = (
                int(sample["memory_used_mib"]) < active_memory_mib
                and int(sample["util_gpu_pct"]) <= active_utilization_pct
            )
            if not idle:
                flush()
                continue
            if segment and (timestamp - segment[-1][0]).total_seconds() > max_gap_minutes * 60:
                flush()
            segment.append((timestamp, sample))
        flush()

    return {
        "schema_version": "blind-gains.gpu-idle-audit.v1",
        "since_utc": since.isoformat(),
        "until_utc": until.isoformat(),
        "definition": {
            "idle_memory_used_below_mib": active_memory_mib,
            "idle_utilization_at_most_pct": active_utilization_pct,
            "violation_if_minutes_between_idle_samples_exceeds": max_idle_minutes,
            "maximum_contiguous_sample_gap_minutes": max_gap_minutes,
        },
        "n_samples": sum(len(values) for values in grouped.values()),
        "idle_intervals": idle_intervals,
        "violations": violations,
        "status": len(violations) == 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--logs", type=Path, nargs="+", required=True)
    parser.add_argument("--since", required=True)
    parser.add_argument("--until", default=None)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    samples: list[dict[str, Any]] = []
    for path in args.logs:
        with path.open(encoding="utf-8") as handle:
            samples.extend(json.loads(line) for line in handle if line.strip())
    since = _timestamp(args.since)
    until = _timestamp(args.until) if args.until else dt.datetime.now(dt.timezone.utc)
    result = audit_samples(samples, since, until)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    partial = Path(f"{args.output}.partial")
    if args.output.exists() or partial.exists():
        raise FileExistsError(f"refusing to overwrite GPU idle audit: {args.output}")
    partial.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(partial, args.output)
    print(json.dumps({"status": result["status"], "violations": len(result["violations"])}, sort_keys=True))


if __name__ == "__main__":
    main()
