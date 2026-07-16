from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_m5_restore_is_hash_audited_and_gpu_free() -> None:
    source = (ROOT / "scripts/launch_m5_anchor_restore.sh").read_text(encoding="utf-8")

    assert "registered_extensions_authorization_v4.json" in source
    assert "restore_easyr1_raw_checkpoint.py" in source
    assert "audit_easyr1_resume_checkpoint.py" in source
    assert 'job_type: "m5_anchor_step100_raw_restore"' in source
    assert 'gpu_ids: []' in source
    assert "RAW_STATE_RESTORED_FOR_RESUME.json" in source


def test_m5_restore_refuses_existing_marker() -> None:
    source = (ROOT / "scripts/launch_m5_anchor_restore.sh").read_text(encoding="utf-8")

    assert 'if [[ -e "${RESTORE_MARKER}" ]]' in source
    assert "Refusing to overwrite existing restore marker" in source
