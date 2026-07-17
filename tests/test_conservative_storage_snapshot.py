from __future__ import annotations

import datetime as dt

import pytest

from scripts.build_conservative_storage_snapshot import (
    CONSERVATIVE_MEASUREMENT,
    EXACT_MEASUREMENT,
    build_snapshot,
)
from scripts.watch_m5_storage_snapshot import refresh_needed, snapshot_age_seconds


def exact_source() -> dict[str, object]:
    return {
        "status": "pass",
        "measurement": EXACT_MEASUREMENT,
        "quota_root": "/quota",
        "quota_bytes": 1_000,
        "used_bytes": 400,
        "measured_at_utc": "2026-07-17T00:00:00Z",
        "components": {"/quota/project": 400},
    }


def test_conservative_snapshot_accounts_for_reserve_write_and_floor() -> None:
    result = build_snapshot(
        exact_source(),
        source_sha256="a" * 64,
        reserve_bytes=300,
        required_bytes=100,
        floor_bytes=100,
        measured_at_utc="2026-07-17T01:00:00Z",
    )
    assert result["measurement"] == CONSERVATIVE_MEASUREMENT
    assert result["used_bytes"] == 700
    assert result["free_bytes"] == 300
    assert result["provenance"]["conservative_free_after_authorized_write_bytes"] == 200


def test_conservative_snapshot_cannot_be_chained() -> None:
    source = exact_source()
    source["measurement"] = CONSERVATIVE_MEASUREMENT
    with pytest.raises(ValueError, match="chaining is forbidden"):
        build_snapshot(
            source,
            source_sha256="b" * 64,
            reserve_bytes=100,
            required_bytes=10,
            floor_bytes=10,
            measured_at_utc="2026-07-17T01:00:00Z",
        )


def test_conservative_snapshot_refuses_an_unsafe_write() -> None:
    with pytest.raises(ValueError, match="cannot authorize"):
        build_snapshot(
            exact_source(),
            source_sha256="c" * 64,
            reserve_bytes=450,
            required_bytes=100,
            floor_bytes=100,
            measured_at_utc="2026-07-17T01:00:00Z",
        )


def test_freshness_watcher_rejects_future_and_refreshes_invalid_status() -> None:
    now = dt.datetime(2026, 7, 17, 12, 0, tzinfo=dt.timezone.utc)
    with pytest.raises(ValueError, match="future-dated"):
        snapshot_age_seconds(
            {"measured_at_utc": "2026-07-17T12:00:01Z"}, now=now
        )
    assert refresh_needed(
        {"status": "fail", "measured_at_utc": "2026-07-17T11:59:59Z"},
        now=now,
        refresh_age_seconds=60,
    )
    assert not refresh_needed(
        {"status": "pass", "measured_at_utc": "2026-07-17T11:59:30Z"},
        now=now,
        refresh_age_seconds=60,
    )
