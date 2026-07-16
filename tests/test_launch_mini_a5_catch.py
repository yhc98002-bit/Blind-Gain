from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_launcher_is_guarded_immutable_committed_and_twice_manifested() -> None:
    source = (ROOT / "scripts" / "launch_mini_a5_catch_v1.sh").read_text(
        encoding="utf-8"
    )
    assert "--tier S" in source
    assert "--required-bytes 1073741824" in source
    assert "refusing to overwrite immutable mini-A5 catch artifact" in source
    assert "git diff --quiet" in source
    assert 'job_type: "m6_mini_a5_catch_generation"' in source
    assert 'job_type: "m6_mini_a5_catch_independent_audit"' in source
    assert "n_pairs_expected: 300" in source
    assert source.count("run_manifest_job.py") == 2
    assert "scientific_gate_decision: null" in source
