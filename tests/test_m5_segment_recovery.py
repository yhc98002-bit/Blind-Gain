from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.build_m5_segment_config import build_segment_config
from scripts.watch_m5_checkpoints import pending_m5_steps
from scripts.watch_m5_merged_relocation import pending_relocation_steps


ROOT = Path(__file__).resolve().parents[1]


def _base_config(path: Path, *, scheduler: str = "constant") -> None:
    path.write_text(
        yaml.safe_dump(
            {
                "data": {"seed": 1},
                "worker": {
                    "actor": {
                        "optim": {
                            "lr": 1e-6,
                            "lr_scheduler_type": scheduler,
                            "lr_warmup_ratio": 0.0,
                        }
                    },
                    "reward": {"reward_function": "native-r1v"},
                },
                "trainer": {
                    "max_steps": 400,
                    "load_checkpoint_path": "registered-step100",
                    "save_checkpoint_path": "registered-root",
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def test_m5_segment_changes_only_paths_and_operational_endpoint(tmp_path: Path) -> None:
    base = tmp_path / "base.yaml"
    _base_config(base)
    source = tmp_path / "global_step_200"
    output = tmp_path / "segment.yaml"
    audit = build_segment_config(
        base,
        output,
        load_checkpoint_path=source,
        save_checkpoint_path=tmp_path / "shared-root",
        segment_start_step=200,
    )
    result = yaml.safe_load(output.read_text(encoding="utf-8"))
    assert result["trainer"]["max_steps"] == 250
    assert result["trainer"]["load_checkpoint_path"] == str(source.resolve())
    assert result["worker"]["reward"] == {"reward_function": "native-r1v"}
    assert audit["segment_end_step"] == 250
    assert audit["registered_terminal_step"] == 400
    assert audit["scheduler_invariance"]["segment_end_does_not_change_lr_curve"] is True


def test_m5_segment_refuses_scheduler_that_depends_on_segment_end(tmp_path: Path) -> None:
    base = tmp_path / "base.yaml"
    _base_config(base, scheduler="cosine")
    with pytest.raises(ValueError, match="constant"):
        build_segment_config(
            base,
            tmp_path / "segment.yaml",
            load_checkpoint_path=tmp_path / "global_step_200",
            save_checkpoint_path=tmp_path / "root",
            segment_start_step=200,
        )


def test_m5_segment_refuses_mismatched_source_step(tmp_path: Path) -> None:
    base = tmp_path / "base.yaml"
    _base_config(base)
    with pytest.raises(ValueError, match="basename"):
        build_segment_config(
            base,
            tmp_path / "segment.yaml",
            load_checkpoint_path=tmp_path / "global_step_199",
            save_checkpoint_path=tmp_path / "root",
            segment_start_step=200,
        )


def test_segment_watchers_stop_at_the_declared_process_boundary() -> None:
    assert pending_m5_steps(200, 250) == (250,)
    assert pending_relocation_steps(200, 250) == (250,)
    assert pending_m5_steps(250, 300) == (300,)
    assert pending_relocation_steps(350, 400) == ()
    with pytest.raises(ValueError):
        pending_m5_steps(200, 400 + 50)


def test_m5_segment_launchers_parse_and_fail_closed() -> None:
    for name in (
        "launch_m5_step_restore.sh",
        "launch_m5_anchor_segment.sh",
        "launch_m5_checkpoint_watch.sh",
        "launch_m5_merged_relocation_watch.sh",
    ):
        subprocess.run(["bash", "-n", str(ROOT / "scripts" / name)], check=True)

    launcher = (ROOT / "scripts/launch_m5_anchor_segment.sh").read_text(encoding="utf-8")
    target_refusal = launcher.index("refusing existing M5 target checkpoint")
    remote_launch = launcher.index('ssh "${NODE}" "cd')
    assert target_refusal < remote_launch
    assert "M5 segment needs 650 GiB host memory" in launcher
    assert "M5 Ray preflight is older than 15 minutes" in launcher
    assert "trainer.max_steps is set to the segment end only" in launcher
    assert "terminal_no_extension:true" in launcher
    assert "performance_values_opened:false" in launcher
    assert "SIGKILL" not in launcher


def test_segment_watcher_launchers_forward_both_boundaries() -> None:
    for name in ("launch_m5_checkpoint_watch.sh", "launch_m5_merged_relocation_watch.sh"):
        source = (ROOT / "scripts" / name).read_text(encoding="utf-8")
        assert '.segment_end_step // .target_global_step' in source
        assert "--resume-after-step ${RESUME_AFTER}" in source
        assert "--stop-after-step ${STOP_AFTER}" in source
