#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import time
from pathlib import Path
from typing import Any, Callable

from scripts.measure_storage_usage import DEFAULT_ROOT, atomic_write, measure


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _stamp(now: dt.datetime) -> str:
    return now.strftime("%Y%m%dT%H%M%SZ")


def refresh_once(
    *,
    quota_root: Path,
    current_output: Path,
    history_dir: Path,
    workers: int,
    timeout_seconds: int,
    now: dt.datetime | None = None,
    measure_fn: Callable[..., dict[str, object]] = measure,
) -> tuple[Path, dict[str, object]]:
    measured_at = now or _utc_now()
    history_output = history_dir / f"storage_usage_snapshot_{_stamp(measured_at)}.json"
    if history_output.exists():
        raise FileExistsError(f"refusing to overwrite storage snapshot: {history_output}")
    payload = measure_fn(
        quota_root,
        workers=workers,
        timeout_seconds=timeout_seconds,
    )
    atomic_write(history_output, payload)
    atomic_write(current_output, payload)
    return history_output, payload


def _write_state(path: Path, payload: dict[str, Any]) -> None:
    atomic_write(path, payload)


def run_loop(args: argparse.Namespace) -> None:
    attempt = 0
    if args.initial_delay_seconds:
        _write_state(
            args.state,
            {
                "schema_version": "blind-gains.storage-snapshot-refresh.v1",
                "status": "initial_wait",
                "initial_delay_seconds": args.initial_delay_seconds,
                "updated_at_utc": _utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        )
        time.sleep(args.initial_delay_seconds)
    while True:
        attempt += 1
        started = _utc_now()
        _write_state(
            args.state,
            {
                "schema_version": "blind-gains.storage-snapshot-refresh.v1",
                "status": "measuring",
                "attempt": attempt,
                "started_at_utc": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        )
        try:
            history, payload = refresh_once(
                quota_root=args.quota_root,
                current_output=args.current_output,
                history_dir=args.history_dir,
                workers=args.workers,
                timeout_seconds=args.timeout_seconds,
                now=started,
            )
        except Exception as error:
            _write_state(
                args.state,
                {
                    "schema_version": "blind-gains.storage-snapshot-refresh.v1",
                    "status": "retry_wait",
                    "attempt": attempt,
                    "error_type": type(error).__name__,
                    "error": str(error),
                    "retry_seconds": args.retry_seconds,
                    "updated_at_utc": _utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                },
            )
            if args.once:
                raise
            time.sleep(args.retry_seconds)
            continue
        _write_state(
            args.state,
            {
                "schema_version": "blind-gains.storage-snapshot-refresh.v1",
                "status": "waiting" if not args.once else "complete",
                "attempt": attempt,
                "history_output": str(history),
                "current_output": str(args.current_output),
                "measured_at_utc": payload["measured_at_utc"],
                "used_bytes": payload["used_bytes"],
                "free_bytes": payload["free_bytes"],
                "next_refresh_seconds": None if args.once else args.interval_seconds,
                "updated_at_utc": _utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        )
        if args.once:
            return
        time.sleep(args.interval_seconds)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quota-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument(
        "--current-output",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "reports"
        / "storage_usage_snapshot.json",
    )
    parser.add_argument("--history-dir", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--interval-seconds", type=int, default=3 * 60 * 60)
    parser.add_argument("--retry-seconds", type=int, default=10 * 60)
    parser.add_argument("--initial-delay-seconds", type=int, default=0)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    if (
        args.interval_seconds <= 0
        or args.retry_seconds <= 0
        or args.initial_delay_seconds < 0
    ):
        raise ValueError(
            "refresh/retry intervals must be positive and initial delay nonnegative"
        )
    args.history_dir.mkdir(parents=True, exist_ok=True)
    args.state.parent.mkdir(parents=True, exist_ok=True)
    run_loop(args)


if __name__ == "__main__":
    main()
