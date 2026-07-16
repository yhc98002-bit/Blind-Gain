from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_launcher_is_guarded_immutable_and_manifested() -> None:
    source = (ROOT / "scripts" / "launch_mini_a5_corpus_v1.sh").read_text(
        encoding="utf-8"
    )
    assert "--tier S" in source
    assert "--required-bytes 3221225472" in source
    assert "refusing to overwrite immutable mini-A5 corpus" in source
    assert 'job_type: "m6_mini_a5_pair_corpus_generation"' in source
    assert "n_pairs_expected: 3000" in source
    assert "scientific_gate_decision: null" in source
    assert "run_manifest_job.py" in source
