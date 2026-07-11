from __future__ import annotations

import json
import datetime as dt
from pathlib import Path

import pytest

from src.ops.storage_guard import (
    GIB,
    allocated_bytes_from_snapshot,
    append_guard_log,
    check_storage,
    evaluate_scratch_guard,
    evaluate_shared_guard,
)


def test_shared_guard_refuses_write_that_crosses_twenty_gib_floor(tmp_path: Path) -> None:
    quota = 500 * GIB
    result = check_storage(
        tier="S",
        path=tmp_path / "new-checkpoint",
        operation="checkpoint_save",
        required_bytes=8 * GIB,
        shared_quota_root=tmp_path,
        usage_probe=lambda _: quota - 27 * GIB,
    )

    assert result.status == "refused"
    assert result.free_bytes_after == 19 * GIB
    assert "quota headroom" in result.reason


def test_shared_guard_allows_exact_floor_but_not_one_byte_below(tmp_path: Path) -> None:
    exact = evaluate_shared_guard(
        path=tmp_path,
        operation="model_download",
        required_bytes=10,
        used_bytes=70,
        quota_bytes=100,
        floor_bytes=20,
    )
    below = evaluate_shared_guard(
        path=tmp_path,
        operation="model_download",
        required_bytes=11,
        used_bytes=70,
        quota_bytes=100,
        floor_bytes=20,
    )

    assert exact.allowed
    assert not below.allowed


def test_scratch_guard_refuses_write_that_crosses_forty_gib_floor(tmp_path: Path) -> None:
    result = check_storage(
        tier="T",
        path=tmp_path / "raw-state",
        operation="raw_checkpoint_relocation",
        required_bytes=6 * GIB,
        free_probe=lambda _: 45 * GIB,
        filesystem_probe=lambda _: "xfs",
    )

    assert result.status == "refused"
    assert result.free_bytes_after == 39 * GIB
    assert "free-space floor" in result.reason


def test_scratch_guard_rejects_large_tmpfs_even_when_space_is_abundant(tmp_path: Path) -> None:
    result = evaluate_scratch_guard(
        path=tmp_path,
        operation="checkpoint_save",
        required_bytes=1,
        free_bytes=500 * GIB,
        fs_type="tmpfs",
    )

    assert not result.allowed
    assert "memory-backed" in result.reason


def test_guard_rejects_negative_required_size(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="required_bytes"):
        evaluate_scratch_guard(
            path=tmp_path,
            operation="bad",
            required_bytes=-1,
            free_bytes=100,
            floor_bytes=10,
            fs_type="xfs",
        )


def test_guard_rejects_negative_free_space_probe(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="free_bytes"):
        evaluate_scratch_guard(
            path=tmp_path,
            operation="bad_probe",
            required_bytes=0,
            free_bytes=-1,
            floor_bytes=10,
            fs_type="xfs",
        )


def test_guard_log_is_append_only_jsonl(tmp_path: Path) -> None:
    log = tmp_path / "guard.jsonl"
    result = evaluate_scratch_guard(
        path=tmp_path,
        operation="dry_save",
        required_bytes=10,
        free_bytes=100,
        floor_bytes=20,
        fs_type="xfs",
        checked_at_utc="2026-07-11T00:00:00Z",
    )

    append_guard_log(log, result)
    append_guard_log(log, result)

    rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 2
    assert all(row["event"] == "storage_guard" for row in rows)


def test_quota_snapshot_fails_closed_when_stale(tmp_path: Path) -> None:
    snapshot = tmp_path / "usage.json"
    snapshot.write_text(
        json.dumps(
            {
                "status": "pass",
                "quota_root": str(tmp_path),
                "used_bytes": 10,
                "measured_at_utc": "2026-07-11T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="stale"):
        allocated_bytes_from_snapshot(
            snapshot,
            tmp_path,
            max_age_seconds=60,
            now=dt.datetime(2026, 7, 11, 1, 0, tzinfo=dt.timezone.utc),
        )


def test_quota_snapshot_rejects_different_root(tmp_path: Path) -> None:
    snapshot = tmp_path / "usage.json"
    snapshot.write_text(
        json.dumps(
            {
                "status": "pass",
                "quota_root": str(tmp_path / "other"),
                "used_bytes": 10,
                "measured_at_utc": "2026-07-11T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="root mismatch"):
        allocated_bytes_from_snapshot(
            snapshot,
            tmp_path,
            now=dt.datetime(2026, 7, 11, 0, 1, tzinfo=dt.timezone.utc),
        )
