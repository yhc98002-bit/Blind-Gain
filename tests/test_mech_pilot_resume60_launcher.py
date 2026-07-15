from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts" / "launch_mech_pilot_resume60.sh"


def test_resume60_launcher_is_valid_shell() -> None:
    subprocess.run(["bash", "-n", str(LAUNCHER)], check=True)


def test_resume60_launcher_is_fail_closed_and_hash_audited() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    assert '"$(jq -r \'.status\' "${SOURCE_MANIFEST}")" == "fail"' in source
    assert "audit_easyr1_resume_checkpoint.py" in source
    assert "--expected-step \"${SOURCE_STEP}\"" in source
    assert "--expected-image-condition \"${IMAGE_CONDITION}\"" in source
    assert '[[ ! -e "${SAVE_ROOT}" ]]' in source
    assert "resume_from_step60_after_ray_host_memory_pressure" in source


def test_resume60_launcher_enforces_one_pilot_and_host_memory_floor() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    assert "pgrep -af '[p]ython.*verl.trainer.main'" in source
    assert "MIN_MEM_AVAILABLE_KIB=$((650 * 1024 * 1024))" in source
    assert "host_memory_preflight" in source
    assert "one pilot trainer per node" in source
    assert '"${NODE}" == "an21"' in source


def test_resume60_launcher_keeps_registered_budget_unchanged() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    command = next(line for line in source.splitlines() if line.startswith('COMMAND="'))
    assert "max_steps" not in command
    assert "save_freq" not in command
    assert "val_freq" not in command


def test_resume60_retry_requires_release_evidence_and_a_new_namespace() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    assert "BLIND_GAINS_RESUME60_SUFFIX" in source
    assert "BLIND_GAINS_RESUME60_PREVIOUS_ATTEMPT" in source
    assert "retry suffix requires the previous interrupted attempt" in source
    assert "compute_allocation_released_before_checkpoint" in source
    assert 'ARM_RUN_NAME="${BASE_NAME}_resume60_${RETRY_SUFFIX}"' in source
    assert "supersedes_interrupted_run" in source
    assert "previous attempt contains a durable checkpoint" in source
