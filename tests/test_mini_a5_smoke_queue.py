from __future__ import annotations

from scripts.run_mini_a5_smoke_queue import dependency_state, node_is_fully_free


def test_full_node_requires_every_gpu_below_memory_threshold() -> None:
    free = {index: {"memory_mib": 2, "utilization_pct": 0} for index in range(8)}
    assert node_is_fully_free(free)
    free[7]["memory_mib"] = 1024
    assert node_is_fully_free(free) is False


def test_dependency_fail_closed_and_m5_may_continue(tmp_path) -> None:
    paths = []
    for name, status in (("seed2", "complete"), ("m11", "complete"), ("m5", "running")):
        path = tmp_path / f"{name}.json"
        path.write_text(f'{{"status":"{status}"}}\n', encoding="utf-8")
        paths.append(path)
    state, statuses = dependency_state(*paths)
    assert state == "ready"
    assert statuses["m5"] == "running"
    paths[1].write_text('{"status":"fail"}\n', encoding="utf-8")
    assert dependency_state(*paths)[0] == "fail"


def test_adversarial_incomplete_priority_work_stays_waiting(tmp_path) -> None:
    paths = []
    for name, status in (("seed2", "running"), ("m11", "complete"), ("m5", "running")):
        path = tmp_path / f"{name}.json"
        path.write_text(f'{{"status":"{status}"}}\n', encoding="utf-8")
        paths.append(path)
    assert dependency_state(*paths)[0] == "waiting"
