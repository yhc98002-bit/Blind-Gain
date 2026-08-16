#!/usr/bin/env python3
"""Waiter-side wedged-vs-dead classifier (dispatch 2026-08-16, infra 1b).

The 2026-08-12 incident: quota exhaustion wedged two live trainers (manifest
"running", ray workers resident at 0 % util, the run's own
``storage_guard.jsonl`` ticking "refused" every 300 s). The chain waiters ran
pure wall-clock deadlines, so both aborted a *live* pipeline ("deadline;
abort") and four downstream workstreams stalled silently for ~2.5 days.

This helper gives waiters an ACTIVE deadline instead. Each poll classifies
the watched run and accumulates deadline time only while the run is genuinely
running:

  complete / failed   -- terminal manifest states, waiter acts as before
  wedged              -- alive pids AND the run's storage guard is currently
                         refusing saves: VISIBLE in the waiter log, deadline
                         clock PAUSED (an alive trainer must never be
                         abandoned for being stalled by storage)
  dead                -- manifest still "running" but every recorded pid is
                         gone, confirmed on consecutive polls: the waiter
                         should stop loudly instead of idling to a deadline
  running / indeterminate -- clock ticks

Fail-closed direction: whenever liveness cannot be established (ssh failure,
no pid files yet, unreadable manifest) the run is treated as ALIVE and the
clock ticks — a waiter must never abort a live trainer on uncertainty.

Prints exactly one line:
    <class> active_seconds=<int> deadline_exhausted=<0|1>
"""
from __future__ import annotations

import argparse
import datetime as dt
import errno
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

LOCAL_NODES = {"login"}


def _parse_now(text: str | None) -> dt.datetime:
    if text is None:
        return dt.datetime.now(dt.timezone.utc)
    parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("--now must carry a timezone")
    return parsed


def _manifest_status(run_dir: Path) -> str | None:
    try:
        payload = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    status = payload.get("status")
    return status if isinstance(status, str) else None


def _manifest_node(run_dir: Path) -> str | None:
    try:
        payload = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    node = payload.get("node")
    return node if isinstance(node, str) else None


def _pid_alive_local(pid: int) -> str:
    try:
        os.kill(pid, 0)
    except OSError as error:
        if error.errno == errno.ESRCH:
            return "dead"
        if error.errno == errno.EPERM:
            return "alive"
        return "unknown"
    return "alive"


def _pid_alive(pid: int, node: str | None) -> str:
    local = node is None or node in LOCAL_NODES or node == socket.gethostname()
    if local:
        return _pid_alive_local(pid)
    proc = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=25", node, f"kill -0 {pid}"],
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        return "alive"
    if proc.returncode == 1:
        return "dead"
    return "unknown"


def _any_pid_alive(run_dir: Path, node: str | None) -> str:
    """"alive" | "dead" | "unknown" over every pids/*.pid; no pids -> unknown."""
    pid_files = sorted((run_dir / "pids").glob("*.pid")) if (run_dir / "pids").is_dir() else []
    states: list[str] = []
    for pid_file in pid_files:
        try:
            pid = int(pid_file.read_text(encoding="utf-8").split()[0])
        except (OSError, ValueError, IndexError):
            states.append("unknown")
            continue
        states.append(_pid_alive(pid, node))
    if not states:
        return "unknown"
    if "alive" in states or "unknown" in states:
        return "alive" if "alive" in states else "unknown"
    return "dead"


def _guard_is_refusing(guard_log: Path, now: dt.datetime, window_seconds: int) -> bool:
    try:
        lines = guard_log.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            return False
        if entry.get("status") != "refused":
            return False
        checked_text = entry.get("checked_at_utc")
        if not isinstance(checked_text, str):
            return False
        try:
            checked = dt.datetime.fromisoformat(checked_text.replace("Z", "+00:00"))
        except ValueError:
            return False
        return (now - checked).total_seconds() <= window_seconds
    return False


def classify(
    run_dir: Path,
    *,
    guard_log: Path,
    now: dt.datetime,
    wedge_window_seconds: int,
    consecutive_dead: int,
    dead_confirmations: int,
) -> tuple[str, int]:
    """Return (classification, new_consecutive_dead)."""
    status = _manifest_status(run_dir)
    if status == "complete":
        return "complete", 0
    if status in ("fail", "failed"):
        return "failed", 0
    if status is None:
        return "indeterminate", 0
    liveness = _any_pid_alive(run_dir, _manifest_node(run_dir))
    if liveness == "dead":
        seen = consecutive_dead + 1
        if seen >= dead_confirmations:
            return "dead", seen
        return "indeterminate", seen
    if liveness == "alive" and _guard_is_refusing(guard_log, now, wedge_window_seconds):
        return "wedged", 0
    return ("running" if liveness == "alive" else "indeterminate"), 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--deadline-active-seconds", type=int, required=True)
    parser.add_argument("--state-file", type=Path, required=True)
    parser.add_argument("--guard-log", type=Path, default=None)
    parser.add_argument("--wedge-window-seconds", type=int, default=900)
    parser.add_argument("--dead-confirmations", type=int, default=2)
    parser.add_argument("--now", type=str, default=None, help="ISO timestamp override (tests)")
    args = parser.parse_args()

    now = _parse_now(args.now)
    guard_log = args.guard_log or (args.run_dir / "storage_guard.jsonl")

    state = {"active_seconds": 0, "last_poll_utc": None, "consecutive_dead": 0}
    try:
        state.update(json.loads(args.state_file.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValueError):
        pass

    classification, consecutive_dead = classify(
        args.run_dir,
        guard_log=guard_log,
        now=now,
        wedge_window_seconds=args.wedge_window_seconds,
        consecutive_dead=int(state.get("consecutive_dead") or 0),
        dead_confirmations=args.dead_confirmations,
    )

    active_seconds = int(state.get("active_seconds") or 0)
    last_poll_text = state.get("last_poll_utc")
    if isinstance(last_poll_text, str) and classification in ("running", "indeterminate"):
        try:
            last_poll = dt.datetime.fromisoformat(last_poll_text.replace("Z", "+00:00"))
            delta = (now - last_poll).total_seconds()
            if delta > 0:
                active_seconds += int(delta)
        except ValueError:
            pass

    new_state = {
        "active_seconds": active_seconds,
        "last_poll_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "consecutive_dead": consecutive_dead,
        "last_classification": classification,
    }
    temporary = args.state_file.with_name(args.state_file.name + f".tmp.{os.getpid()}")
    temporary.write_text(json.dumps(new_state, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, args.state_file)

    exhausted = 1 if active_seconds > args.deadline_active_seconds else 0
    print(f"{classification} active_seconds={active_seconds} deadline_exhausted={exhausted}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
