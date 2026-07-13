from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts/launch_mech_a3_resume20.sh"


def test_resume_launcher_is_valid_shell() -> None:
    subprocess.run(["bash", "-n", str(LAUNCHER)], check=True)


def test_resume_launcher_is_fail_closed_and_uses_new_namespace() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    assert '"$(jq -r \'.status\' "${SOURCE_MANIFEST}")" == "fail"' in source
    assert "RAW_STATE_RESTORED_FOR_RESUME.json" in source
    assert "mech_a3_caption_resume20" in source
    assert '[[ ! -e "${SAVE_ROOT}" ]]' in source
    assert "--load-checkpoint-path" in source
    assert "excluded_uncheckpointed_source_steps: [21,22,23,24,25,26]" in source


def test_resume_launcher_routes_all_runtime_temp_to_dev_shm() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    assert 'RAY_ROOT="/dev/shm/' in source
    assert "TMPDIR='${JOB_TMP}' TMP='${JOB_TMP}' TEMP='${JOB_TMP}' RAY_TMPDIR='${RAY_ROOT}'" in source
    assert "scripts/probe_ray_tempdir.py" in source
    assert 'LOCK="/dev/shm/' in source
    assert 'LOCK="/tmp/' not in source


def test_resume_launcher_does_not_change_registered_budget() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    command = next(line for line in source.splitlines() if line.startswith('COMMAND="'))
    assert "max_steps" not in command
    assert "save_freq" not in command
    assert "val_freq" not in command
