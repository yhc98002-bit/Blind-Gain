from __future__ import annotations

from scripts.report_gpu_hours import summarize_gpu_hours


def _sample(minute: int, utilization: int, memory_mib: int) -> dict[str, object]:
    return {
        "ts": f"2026-07-11T00:{minute:02d}:00+00:00",
        "node": "an12",
        "gpu_index": 0,
        "util_gpu_pct": utilization,
        "memory_used_mib": memory_mib,
    }


def test_gpu_hours_integrates_observed_intervals_without_idle_gate() -> None:
    payload = summarize_gpu_hours(
        [_sample(0, 50, 2048), _sample(10, 100, 2048), _sample(20, 0, 2)]
    )

    node = payload["by_node"]["an12"]
    assert node["observed_gpu_hours"] == 1 / 3
    assert node["active_gpu_hours"] == 1 / 3
    assert node["occupied_gpu_hours"] == 1 / 3
    assert node["utilization_equivalent_gpu_hours"] == 0.25
    assert node["mean_utilization_pct_over_observed"] == 75.0
    assert payload["gate"] is False


def test_gpu_hours_omits_large_telemetry_gaps() -> None:
    records = [_sample(0, 100, 2048), _sample(10, 100, 2048)]
    records[1]["ts"] = "2026-07-11T01:00:00+00:00"

    payload = summarize_gpu_hours(records, max_gap_seconds=900)

    assert payload["by_node"]["an12"]["observed_gpu_hours"] == 0
    assert payload["by_node"]["an12"]["omitted_gap_count"] == 1
