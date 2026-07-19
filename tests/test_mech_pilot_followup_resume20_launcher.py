from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts/launch_mech_pilot_followup_resume20.sh"


def test_followup_resume20_launcher_is_valid_shell() -> None:
    subprocess.run(["bash", "-n", str(LAUNCHER)], check=True)


def test_followup_resume20_is_arm_seed_and_namespace_fail_closed() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    assert '"$(jq -r \'.status\' "${SOURCE_MANIFEST}")" == "fail"' in source
    assert '"$(jq -r \'.arm\' "${SOURCE_MANIFEST}")" == "${ARM}"' in source
    assert '"$(jq -r \'.seed\' "${SOURCE_MANIFEST}")" == "${SEED}"' in source
    assert 'ARM_RUN_NAME="${BASE_NAME}_resume20"' in source
    assert '[[ ! -e "${SAVE_ROOT}" ]]' in source
    assert "audit_easyr1_resume_checkpoint.py" in source


def test_followup_resume20_does_not_reuse_partial_post_checkpoint_steps() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    assert "source_log_prefix_through_step20.jsonl" in source
    assert "excluded_uncheckpointed_source_steps.json" in source
    assert "Only source metrics through global step 20" in source


def test_followup_resume20_avoids_compute_tmp_and_reserves_concurrent_saves() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    assert 'RAY_ROOT="/dev/shm/' in source
    assert "TMPDIR='${JOB_TMP}' TMP='${JOB_TMP}' TEMP='${JOB_TMP}' RAY_TMPDIR='${RAY_ROOT}'" in source
    assert "BLIND_GAINS_CHECKPOINT_REQUIRED_BYTES=110000000000" in source
