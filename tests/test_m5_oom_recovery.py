from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from scripts.build_m5_recovery_config import build_recovery_config


ROOT = Path(__file__).resolve().parents[1]


def test_m5_recovery_config_changes_only_checkpoint_paths(tmp_path: Path) -> None:
    base = tmp_path / "base.yaml"
    base.write_text(
        "trainer:\n  max_steps: 400\n  load_checkpoint_path: old-load\n  save_checkpoint_path: old-save\nworker:\n  reward: native\n",
        encoding="utf-8",
    )
    output = tmp_path / "recovery.yaml"
    audit = build_recovery_config(
        base,
        output,
        load_checkpoint_path=tmp_path / "step150",
        save_checkpoint_path=tmp_path / "new-root",
    )
    result = yaml.safe_load(output.read_text(encoding="utf-8"))
    assert audit["only_checkpoint_paths_changed"] is True
    assert result["trainer"]["max_steps"] == 400
    assert result["worker"] == {"reward": "native"}
    assert result["trainer"]["load_checkpoint_path"].endswith("step150")
    assert result["trainer"]["save_checkpoint_path"].endswith("new-root")


def test_m5_step150_restore_is_hash_audited_and_refuses_overwrite() -> None:
    source = (ROOT / "scripts/launch_m5_step150_restore.sh").read_text(encoding="utf-8")
    assert "m5_host_memory_incident_v1.json" in source
    assert "restore_easyr1_raw_checkpoint.py" in source
    assert "audit_easyr1_resume_checkpoint.py" in source
    assert "--expected-step 150" in source
    assert "Refusing to overwrite existing step-150 restore marker" in source
    assert 'job_type:"m5_step150_raw_restore"' in source
    assert "performance_values_opened:false" in source


def test_m5_watchers_skip_the_already_archived_resume_step() -> None:
    checkpoint = (ROOT / "scripts/watch_m5_checkpoints.py").read_text(encoding="utf-8")
    relocation = (ROOT / "scripts/watch_m5_merged_relocation.py").read_text(encoding="utf-8")
    checkpoint_launcher = (ROOT / "scripts/launch_m5_checkpoint_watch.sh").read_text(encoding="utf-8")
    relocation_launcher = (ROOT / "scripts/launch_m5_merged_relocation_watch.sh").read_text(encoding="utf-8")
    assert "pending_m5_steps(args.resume_after_step, args.stop_after_step)" in checkpoint
    assert "pending_relocation_steps(args.resume_after_step, args.stop_after_step)" in relocation
    assert "--resume-after-step ${RESUME_AFTER}" in checkpoint_launcher
    assert "--resume-after-step ${RESUME_AFTER}" in relocation_launcher
    assert "--stop-after-step ${STOP_AFTER}" in checkpoint_launcher
    assert "--stop-after-step ${STOP_AFTER}" in relocation_launcher


def test_m5_recovery_shell_files_parse() -> None:
    for name in (
        "launch_m5_step150_restore.sh",
        "launch_m5_anchor_recovery150.sh",
        "launch_m5_checkpoint_watch.sh",
        "launch_m5_merged_relocation_watch.sh",
        "launch_m5_checkpoint_evaluation_queue.sh",
    ):
        subprocess.run(["bash", "-n", str(ROOT / "scripts" / name)], check=True)


def test_m5_recovery_launcher_is_fail_closed_and_preserves_terminal_rule() -> None:
    source = (ROOT / "scripts/launch_m5_anchor_recovery150.sh").read_text(encoding="utf-8")
    assert "build_m5_recovery_config.py" in source
    assert "m5_host_memory_incident_v1.json" in source
    assert 'resumed_from_global_step:150,target_global_step:400' in source
    assert 'terminal_step:400,terminal_no_extension:true' in source
    assert 'checkpoint_schedule:[200,250,300,350,400]' in source
    assert "another project EasyR1 trainer is active" in source
    assert "M5 recovery needs 650 GiB host memory" in source
    assert '(.expected_step==150) and (.world_size==4)' in source
    assert ".expected_world_size" not in source
    assert '[[ ! -e "${SAVE_ROOT}" ]]' in source
    assert "launch_m5_checkpoint_evaluation_queue.sh" in source
    assert "M5 Ray preflight is older than 15 minutes" in source
    assert "M5 recovery did not reach four-GPU startup readiness in 10 minutes" in source
    assert source.index("M5 Ray preflight manifest identity is invalid") < source.index(
        'mkdir -p "${RUN_DIR}/logs"'
    )
    assert source.index("step-150 raw state is not restored") < source.index(
        'mkdir -p "${RUN_DIR}/logs"'
    )
