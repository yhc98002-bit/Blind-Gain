from __future__ import annotations

import datetime as dt
import json
from argparse import Namespace
from pathlib import Path

import pytest

from scripts.run_storage_snapshot_refresh_loop import refresh_once, run_loop


def test_refresh_once_publishes_matching_current_and_immutable_history(
    tmp_path: Path,
) -> None:
    now = dt.datetime(2026, 7, 13, 10, 0, tzinfo=dt.timezone.utc)

    def fake_measure(root: Path, *, workers: int, timeout_seconds: int):
        assert root == tmp_path
        assert workers == 3
        assert timeout_seconds == 17
        return {
            "status": "pass",
            "quota_root": str(root),
            "used_bytes": 12,
            "free_bytes": 88,
            "measured_at_utc": "2026-07-13T10:00:00Z",
        }

    history, payload = refresh_once(
        quota_root=tmp_path,
        current_output=tmp_path / "current.json",
        history_dir=tmp_path / "history",
        workers=3,
        timeout_seconds=17,
        now=now,
        measure_fn=fake_measure,
    )

    assert history.name == "storage_usage_snapshot_20260713T100000Z.json"
    assert json.loads(history.read_text()) == payload
    assert json.loads((tmp_path / "current.json").read_text()) == payload

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        refresh_once(
            quota_root=tmp_path,
            current_output=tmp_path / "current.json",
            history_dir=tmp_path / "history",
            workers=3,
            timeout_seconds=17,
            now=now,
            measure_fn=fake_measure,
        )


def test_refresh_loop_waits_before_first_measurement(tmp_path: Path, monkeypatch) -> None:
    sleeps: list[int] = []

    def stop_after_delay(seconds: int) -> None:
        sleeps.append(seconds)
        raise RuntimeError("stop before measurement")

    monkeypatch.setattr("scripts.run_storage_snapshot_refresh_loop.time.sleep", stop_after_delay)
    args = Namespace(
        initial_delay_seconds=23,
        state=tmp_path / "state.json",
    )

    with pytest.raises(RuntimeError, match="stop before measurement"):
        run_loop(args)

    assert sleeps == [23]
    state = json.loads(args.state.read_text(encoding="utf-8"))
    assert state["status"] == "initial_wait"
    assert state["initial_delay_seconds"] == 23
