from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_l7_finalize_launcher_is_fail_closed_and_manifested() -> None:
    source = (ROOT / "scripts/launch_l7_v2_finalize.sh").read_text(encoding="utf-8")

    assert 'if [[ -e "${output}" ]]' in source
    assert '.job_type == "l7_blind_solvability_geo3k_v2_guarded_rescore"' in source
    assert ".guarded_rescore_stats.n_rows == 1889" in source
    assert ".guarded_rescore_stats.n_responses == 32113" in source
    assert ".guarded_rescore_stats.mathruler_error_count == 0" in source
    assert ".guarded_rescore_stats.native_r1v_shadow_invalid_count == 0" in source
    assert "source_runs: $source_runs" in source
    assert "scripts/run_manifest_job.py" in source
    assert "--audit-json-output reports/blind_solvability_geo3k_v2_audited.json" in source
