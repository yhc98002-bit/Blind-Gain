from __future__ import annotations

import json
import subprocess
from pathlib import Path

from scripts.watch_m5_merged_relocation import valid_evaluation_marker


ROOT = Path(__file__).resolve().parents[1]


def test_m5_launchers_are_valid_shell() -> None:
    for name in (
        "launch_m5_anchor_longhorizon.sh",
        "launch_m5_checkpoint_watch.sh",
        "launch_m5_merged_relocation_watch.sh",
        "launch_m5_longhorizon_queue.sh",
    ):
        subprocess.run(["bash", "-n", str(ROOT / "scripts" / name)], check=True)


def test_longhorizon_fails_closed_before_namespace_or_ssh_launch() -> None:
    source = (ROOT / "scripts/launch_m5_anchor_longhorizon.sh").read_text(encoding="utf-8")
    integrity = source.index('jq -e \'(.schema_version=="blind-gains.m5-restore-resume-integrity.v1")')
    namespace = source.index('[[ ! -e "${SAVE_ROOT}" ]]')
    run_dir = source.index('mkdir -p "${RUN_DIR}/logs"')
    remote_launch = source.index('ssh "${NODE}" "cd')

    assert integrity < namespace < run_dir < remote_launch
    assert 'SOURCE_ID="anchor_a0_recipe_3b_geo3k_20260709T224852Z"' in source
    assert "m5_anchor_resume_integrity_step101/global_step_101" not in source
    assert 'target_global_step:400' in source
    assert 'terminal_no_extension:true' in source
    assert 'tensor_parallel_width:2,replica_count:2' in source


def test_m5_merge_retention_is_independent_of_evaluation_and_relocation() -> None:
    merge_source = (ROOT / "scripts/watch_m5_checkpoints.py").read_text(encoding="utf-8")
    relocation_source = (ROOT / "scripts/watch_m5_merged_relocation.py").read_text(encoding="utf-8")

    assert "relocate_merged_output=False" in merge_source
    assert "valid_evaluation_marker" not in merge_source
    assert "relocate_merged(" in relocation_source
    assert "wait_for_evaluation(" in relocation_source
    assert "INTERMEDIATE_STEPS = (150, 200, 250, 300, 350)" in relocation_source
    assert "400" not in relocation_source.split("INTERMEDIATE_STEPS =", 1)[1].splitlines()[0]


def test_m5_eval_marker_rejects_wrong_checkpoint_hash(tmp_path: Path) -> None:
    actor = tmp_path / "global_step_150" / "actor"
    merged = actor / "huggingface"
    merged.mkdir(parents=True)
    index = merged / "model.safetensors.index.json"
    index.write_text('{"weight_map":{"x":"model.safetensors"}}\n', encoding="utf-8")
    marker = tmp_path / "marker.json"
    marker.write_text(
        json.dumps(
            {
                "schema_version": "blind-gains.m5-step-eval-marker.v1",
                "status": "complete",
                "global_step": 150,
                "checkpoint_path": str(merged),
                "checkpoint_index_sha256": "0" * 64,
                "geo3k_status": "complete",
                "r19_status": "complete",
            }
        ),
        encoding="utf-8",
    )

    assert valid_evaluation_marker(marker, step=150, actor_dir=actor) is False


def test_m5_queue_never_sends_signals_or_preempts() -> None:
    source = (ROOT / "scripts/run_m5_longhorizon_queue.py").read_text(encoding="utf-8")

    assert "os.kill" not in source
    assert "kill -9" not in source
    assert "memory <= 1024" in source
    assert "streaks[node][gpu] >= 2" in source
    assert "project_trainer_active" in source
