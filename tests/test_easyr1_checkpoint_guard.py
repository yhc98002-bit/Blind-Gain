from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from src.ops.easyr1_checkpoint_guard import (
    guard_easyr1_checkpoint_save,
    wait_for_easyr1_checkpoint_storage,
)
from src.ops.storage_guard import GIB, StorageGuardRefusal


def test_anchor_path_is_untouched_when_pilot_guard_flag_is_absent(tmp_path: Path) -> None:
    called = False

    def fail_if_called(_: Path) -> int:
        nonlocal called
        called = True
        raise AssertionError("disabled guard must not probe storage")

    result = guard_easyr1_checkpoint_save(
        tmp_path / "anchor",
        60,
        environment={},
        free_probe=fail_if_called,
    )

    assert result is None
    assert not called


def test_enabled_pilot_guard_fails_loudly_without_expected_checkpoint_size(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="REQUIRED_BYTES"):
        guard_easyr1_checkpoint_save(
            tmp_path / "pilot",
            20,
            environment={
                "BLIND_GAINS_STORAGE_GUARD_ENABLED": "1",
                "BLIND_GAINS_CHECKPOINT_TIER": "T",
            },
        )


def test_enabled_pilot_guard_refuses_low_scratch_before_save(tmp_path: Path) -> None:
    log = tmp_path / "guard.jsonl"
    with pytest.raises(StorageGuardRefusal, match="free-space floor"):
        guard_easyr1_checkpoint_save(
            tmp_path / "pilot",
            20,
            environment={
                "BLIND_GAINS_STORAGE_GUARD_ENABLED": "1",
                "BLIND_GAINS_CHECKPOINT_TIER": "T",
                "BLIND_GAINS_CHECKPOINT_REQUIRED_BYTES": str(6 * GIB),
                "BLIND_GAINS_STORAGE_GUARD_LOG": str(log),
            },
            free_probe=lambda _: 45 * GIB,
            filesystem_probe=lambda _: "xfs",
        )

    assert '"status": "refused"' in log.read_text(encoding="utf-8")


def test_patch_places_guard_before_checkpoint_deletion_and_write() -> None:
    root = Path(__file__).resolve().parents[1]
    patch = (root / "docs" / "easyr1_storage_guard_patch.diff").read_text(encoding="utf-8")
    guard_offset = patch.index("wait_for_easyr1_checkpoint_storage(")
    save_offset = patch.index("if self.val_reward_score")
    assert guard_offset < save_offset


def test_retrying_guard_waits_after_refusal_and_rechecks_quota(tmp_path: Path) -> None:
    used_values = iter((476 * GIB, 470 * GIB))
    sleeps: list[float] = []
    result = wait_for_easyr1_checkpoint_storage(
        tmp_path / "pilot",
        20,
        environment={
            "BLIND_GAINS_STORAGE_GUARD_ENABLED": "1",
            "BLIND_GAINS_CHECKPOINT_TIER": "S",
            "BLIND_GAINS_CHECKPOINT_REQUIRED_BYTES": str(5 * GIB),
            "BLIND_GAINS_SHARED_QUOTA_ROOT": str(tmp_path),
            "BLIND_GAINS_SHARED_QUOTA_BYTES": str(500 * GIB),
            "BLIND_GAINS_STORAGE_GUARD_LOG": str(tmp_path / "guard.jsonl"),
            "BLIND_GAINS_STORAGE_GUARD_RETRY_SECONDS": "7",
            "BLIND_GAINS_STORAGE_GUARD_MAX_ATTEMPTS": "2",
        },
        usage_probe=lambda _: next(used_values),
        sleep=sleeps.append,
    )

    assert result is not None and result.allowed
    assert sleeps == [7.0]
    rows = (tmp_path / "guard.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(rows) == 2
    assert '"status": "refused"' in rows[0]
    assert '"status": "pass"' in rows[1]


def test_shared_checkpoint_guard_uses_quota_snapshot_not_recursive_du(
    tmp_path: Path,
) -> None:
    snapshot = tmp_path / "usage.json"
    snapshot.write_text(
        json.dumps(
            {
                "status": "pass",
                "quota_root": str(tmp_path.resolve()),
                "used_bytes": 476 * GIB,
                "measured_at_utc": dt.datetime.now(dt.timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(StorageGuardRefusal, match="quota headroom"):
        guard_easyr1_checkpoint_save(
            tmp_path / "pilot",
            20,
            environment={
                "BLIND_GAINS_STORAGE_GUARD_ENABLED": "1",
                "BLIND_GAINS_CHECKPOINT_TIER": "S",
                "BLIND_GAINS_CHECKPOINT_REQUIRED_BYTES": str(5 * GIB),
                "BLIND_GAINS_SHARED_QUOTA_ROOT": str(tmp_path),
                "BLIND_GAINS_SHARED_QUOTA_BYTES": str(500 * GIB),
                "BLIND_GAINS_SHARED_USAGE_SNAPSHOT": str(snapshot),
                "BLIND_GAINS_STORAGE_GUARD_LOG": str(tmp_path / "guard.jsonl"),
            },
        )


def test_stale_snapshot_refuses_then_retries_after_refresh(tmp_path: Path) -> None:
    snapshot = tmp_path / "usage.json"
    log = tmp_path / "guard.jsonl"
    environment = {
        "BLIND_GAINS_STORAGE_GUARD_ENABLED": "1",
        "BLIND_GAINS_CHECKPOINT_TIER": "S",
        "BLIND_GAINS_CHECKPOINT_REQUIRED_BYTES": str(5 * GIB),
        "BLIND_GAINS_SHARED_QUOTA_ROOT": str(tmp_path),
        "BLIND_GAINS_SHARED_QUOTA_BYTES": str(500 * GIB),
        "BLIND_GAINS_SHARED_USAGE_SNAPSHOT": str(snapshot),
        "BLIND_GAINS_SHARED_USAGE_SNAPSHOT_MAX_AGE_SECONDS": "60",
        "BLIND_GAINS_STORAGE_GUARD_LOG": str(log),
        "BLIND_GAINS_STORAGE_GUARD_RETRY_SECONDS": "7",
        "BLIND_GAINS_STORAGE_GUARD_MAX_ATTEMPTS": "2",
    }

    def write_snapshot(measured_at: dt.datetime) -> None:
        snapshot.write_text(
            json.dumps(
                {
                    "status": "pass",
                    "quota_root": str(tmp_path.resolve()),
                    "used_bytes": 100 * GIB,
                    "measured_at_utc": measured_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
            ),
            encoding="utf-8",
        )

    write_snapshot(dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=1))
    sleeps: list[float] = []

    def refresh_during_wait(seconds: float) -> None:
        sleeps.append(seconds)
        write_snapshot(dt.datetime.now(dt.timezone.utc))

    result = wait_for_easyr1_checkpoint_storage(
        tmp_path / "pilot",
        20,
        environment=environment,
        sleep=refresh_during_wait,
    )

    assert result is not None and result.allowed
    assert sleeps == [7.0]
    rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert [row["status"] for row in rows] == ["refused", "pass"]
    assert "snapshot is stale" in rows[0]["reason"]
