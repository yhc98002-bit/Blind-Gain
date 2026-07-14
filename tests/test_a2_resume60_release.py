from __future__ import annotations

from scripts.watch_a2_resume60_release import impossible, release_candidates, terminal_outcome


def test_release_prefers_any_fully_released_single_node() -> None:
    outcomes = {"a1_real": "complete", "a2b_noimage": "running", "a3_caption": "running"}
    assert release_candidates(outcomes) == ["an12"]

    outcomes = {"a1_real": "running", "a2b_noimage": "complete", "a3_caption": "complete"}
    assert release_candidates(outcomes) == ["an29"]


def test_partial_an29_release_never_launches_a2() -> None:
    outcomes = {"a1_real": "running", "a2b_noimage": "complete", "a3_caption": "running"}
    assert release_candidates(outcomes) == []
    assert not impossible(outcomes)


def test_queue_only_accepts_verified_completion() -> None:
    base = {"status": "complete", "exit_code": 0, "artifacts_exist": True, "end_time_utc": "now"}
    assert terminal_outcome(base) == "complete"
    assert terminal_outcome({**base, "artifacts_exist": False}) == "failed"


def test_queue_fails_only_when_both_node_release_paths_are_impossible() -> None:
    assert impossible({"a1_real": "failed", "a2b_noimage": "complete", "a3_caption": "failed"})
    assert not impossible({"a1_real": "failed", "a2b_noimage": "running", "a3_caption": "running"})
