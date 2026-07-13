from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts" / "launch_mech_pilot_arm.sh"


def test_mech_pilot_launcher_is_valid_shell() -> None:
    subprocess.run(["bash", "-n", str(LAUNCHER)], check=True)


def test_authorization_precedes_run_directory_ssh_and_checkpoint_creation() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    authorization = source.index("scripts/check_pilot_launch_authorization.py")
    run_directory = source.index('mkdir -p "${RUN_DIR}/logs"')
    first_ssh = source.index('ssh "${NODE}"')

    assert authorization < run_directory
    assert authorization < first_ssh
    assert '--checkpoint-path "${CHECKPOINT_PATH}"' in source
    assert 'if [[ -e "${CHECKPOINT_PATH}" ]]' in source


def test_launcher_enforces_single_node_tp1_and_checkpoint_guard() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")

    assert '--require-tp 1' in source
    assert 'BLIND_GAINS_STORAGE_GUARD_ENABLED=1' in source
    assert 'BLIND_GAINS_CHECKPOINT_TIER=S' in source
    assert 'BLIND_GAINS_CHECKPOINT_REQUIRED_BYTES=55000000000' in source
    assert 'BLIND_GAINS_STORAGE_GUARD_RETRY_SECONDS=300' in source
    assert 'scripts/launch_pilot_checkpoint_watch.sh' in source
    assert 'checkpoint_schedule: [20, 40, 60, 80, 100]' in source


def test_launcher_pins_preregistration_stack_and_a3_caption_store() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")

    assert 'git ls-files --error-unmatch "${PREREG}"' in source
    assert 'preregistration_sha256: $preregistration_hash' in source
    assert 'easyr1_worktree_patch_sha256: $easyr1_patch_hash' in source
    assert 'easyr1_logger_sha256: $logger_hash' in source
    assert 'easyr1_trainer_sha256: $trainer_hash' in source
    assert 'caption_store_sha256: (if $caption_store_hash' in source
    assert 'caption_store_files_sha256: (if $caption_files_hash' in source


def test_launcher_does_not_override_registered_training_budget() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    command_line = next(line for line in source.splitlines() if line.startswith('COMMAND="'))

    assert "trainer.max_steps" not in command_line
    assert "trainer.save_freq" not in command_line
    assert "trainer.val_freq" not in command_line


def test_recovery_oom_uses_expandable_segments_without_config_mutation() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    recovery = (ROOT / "scripts" / "launch_mech_pilot_recovery.sh").read_text(
        encoding="utf-8"
    )

    assert '"cuda_allocator_fragmentation_oom_before_first_checkpoint"' in source
    assert 'PYTORCH_CUDA_ALLOC_CONF_VALUE="expandable_segments:True"' in source
    assert "PYTORCH_CUDA_ALLOC_CONF='${PYTORCH_CUDA_ALLOC_CONF_VALUE}'" in source
    assert "pytorch_cuda_alloc_conf:" in source
    assert 'scientific_config_change: false' in source
    assert "[reason-code]" in recovery
    assert 'BLIND_GAINS_PILOT_RECOVERY_REASON="${RECOVERY_REASON}"' in recovery
