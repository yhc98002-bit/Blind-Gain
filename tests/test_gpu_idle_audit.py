from __future__ import annotations

import datetime as dt

from scripts.audit_gpu_idle import audit_samples


UTC = dt.timezone.utc


def _sample(node: str, gpu: int, minute: int, memory: int, utilization: int) -> dict:
    timestamp = dt.datetime(2026, 7, 10, tzinfo=UTC) + dt.timedelta(minutes=minute)
    return {
        "ts": timestamp.isoformat(),
        "node": node,
        "gpu_index": gpu,
        "memory_used_mib": memory,
        "util_gpu_pct": utilization,
    }


def _complete_samples(overrides: list[dict] | None = None) -> list[dict]:
    samples = [
        _sample(node, gpu, minute, 4096, 50)
        for node in ("an12", "an29")
        for gpu in range(8)
        for minute in range(0, 61, 5)
    ]
    return samples + (overrides or [])


def test_idle_audit_flags_more_than_thirty_minutes() -> None:
    overrides = [_sample("an12", 3, minute, 2, 0) for minute in range(10, 51, 5)]
    samples = [
        sample
        for sample in _complete_samples(overrides)
        if not (sample["node"] == "an12" and sample["gpu_index"] == 3 and 10 <= _minute(sample) <= 50)
    ] + overrides
    result = audit_samples(
        samples,
        dt.datetime(2026, 7, 10, tzinfo=UTC),
        dt.datetime(2026, 7, 10, 1, tzinfo=UTC),
    )
    violations = [item for item in result["violations"] if item["type"] == "idle_over_limit"]
    assert len(violations) == 1
    assert violations[0]["duration_minutes_between_samples"] == 40


def _minute(sample: dict) -> int:
    return dt.datetime.fromisoformat(sample["ts"]).minute


def test_memory_reservation_is_not_classified_as_idle() -> None:
    result = audit_samples(
        _complete_samples(),
        dt.datetime(2026, 7, 10, tzinfo=UTC),
        dt.datetime(2026, 7, 10, 1, tzinfo=UTC),
    )
    assert result["status"] is True
    assert result["violations"] == []
