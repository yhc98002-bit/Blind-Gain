"""I10 fixtures for the waiter wedged-vs-dead distinction (2026-08-16 infra 1b).

On 2026-08-13 both chain waiters aborted live, storage-wedged trainers with
"deadline; abort": the deadline was pure wall-clock and nothing distinguished
a stalled-but-alive trainer from a dead one. The pre-fix behavior fails
``test_wedged_time_does_not_consume_the_deadline`` (no such notion existed)
and ``test_waiter_scripts_use_active_deadline_helper`` (the scripts carried a
wall-clock ``DEADLINE=$((...))``).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HELPER = REPO / "scripts" / "chain_wait_helper.py"

T0 = "2026-08-16T00:00:00Z"
T0_PLUS_2H = "2026-08-16T02:00:00Z"
T0_PLUS_4H = "2026-08-16T04:00:00Z"


def _make_run(tmp_path: Path, *, status: str = "running", pid: int | None = None) -> Path:
    run_dir = tmp_path / "run"
    (run_dir / "pids").mkdir(parents=True)
    (run_dir / "run_manifest.json").write_text(
        json.dumps({"status": status, "node": "login"}), encoding="utf-8"
    )
    if pid is not None:
        (run_dir / "pids" / "login.pid").write_text(f"{pid}\n", encoding="utf-8")
    return run_dir


def _write_guard(run_dir: Path, *, status: str, checked_at_utc: str) -> None:
    (run_dir / "storage_guard.jsonl").write_text(
        json.dumps({"status": status, "checked_at_utc": checked_at_utc}) + "\n",
        encoding="utf-8",
    )


def _poll(run_dir: Path, state: Path, *, now: str, budget: int = 3600) -> str:
    proc = subprocess.run(
        [
            sys.executable,
            str(HELPER),
            str(run_dir),
            "--deadline-active-seconds",
            str(budget),
            "--state-file",
            str(state),
            "--now",
            now,
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO),
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def test_wedged_time_does_not_consume_the_deadline(tmp_path: Path) -> None:
    """Alive pids + guard refusing saves => WEDGED, clock paused: four hours
    of wedge against a one-hour budget must not exhaust the deadline."""
    run_dir = _make_run(tmp_path, pid=os.getpid())
    state = tmp_path / "state.json"

    _write_guard(run_dir, status="refused", checked_at_utc=T0)
    assert _poll(run_dir, state, now=T0) == "wedged active_seconds=0 deadline_exhausted=0"

    _write_guard(run_dir, status="refused", checked_at_utc=T0_PLUS_2H)
    assert (
        _poll(run_dir, state, now=T0_PLUS_2H)
        == "wedged active_seconds=0 deadline_exhausted=0"
    )

    _write_guard(run_dir, status="refused", checked_at_utc=T0_PLUS_4H)
    assert (
        _poll(run_dir, state, now=T0_PLUS_4H)
        == "wedged active_seconds=0 deadline_exhausted=0"
    )


def test_running_time_consumes_the_deadline(tmp_path: Path) -> None:
    run_dir = _make_run(tmp_path, pid=os.getpid())
    state = tmp_path / "state.json"
    _write_guard(run_dir, status="pass", checked_at_utc=T0)

    first = _poll(run_dir, state, now=T0)
    assert first.startswith("running active_seconds=0")

    second = _poll(run_dir, state, now=T0_PLUS_2H)
    assert second == "running active_seconds=7200 deadline_exhausted=1"


def test_dead_requires_consecutive_confirmations(tmp_path: Path) -> None:
    reaped = subprocess.Popen(["true"])
    reaped.wait()
    run_dir = _make_run(tmp_path, pid=reaped.pid)
    state = tmp_path / "state.json"

    assert _poll(run_dir, state, now=T0).startswith("indeterminate")
    assert _poll(run_dir, state, now=T0_PLUS_2H).startswith("dead")


def test_terminal_manifest_states_pass_through(tmp_path: Path) -> None:
    state = tmp_path / "state.json"
    complete_dir = _make_run(tmp_path, status="complete")
    assert _poll(complete_dir, state, now=T0).startswith("complete")

    failed_dir = tmp_path / "failed_run"
    (failed_dir / "pids").mkdir(parents=True)
    (failed_dir / "run_manifest.json").write_text(
        json.dumps({"status": "fail", "node": "login"}), encoding="utf-8"
    )
    assert _poll(failed_dir, tmp_path / "state2.json", now=T0).startswith("failed")


def test_no_pids_is_fail_closed_alive(tmp_path: Path) -> None:
    """Liveness that cannot be established must never read as dead."""
    run_dir = _make_run(tmp_path, pid=None)
    verdict = _poll(run_dir, tmp_path / "state.json", now=T0)
    assert verdict.startswith("indeterminate")


def test_waiter_scripts_use_active_deadline_helper() -> None:
    """The canonical waiters carry the active deadline, not the wall-clock
    one that abandoned live trainers on 2026-08-13 (pre-fix scripts fail)."""
    for name in ("seed2_an12_chain.sh", "a3_eval_chain.sh"):
        text = (REPO / "scripts" / name).read_text(encoding="utf-8")
        assert "chain_wait_helper.py" in text, f"{name} does not use the helper"
        assert "DEADLINE=$((" not in text, f"{name} still has a wall-clock deadline"
        assert "wedged" in text.lower() or "WEDGED" in text, f"{name} hides the wedged state"
