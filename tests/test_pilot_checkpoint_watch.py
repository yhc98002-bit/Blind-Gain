from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.watch_anchor_checkpoints import valid_evaluation_marker
from scripts.watch_pilot_checkpoints import PILOT_STEPS, execution_plan, relocation_plan


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_pilot_plan_retains_only_final_merged_checkpoint_on_shared() -> None:
    plan = relocation_plan()

    assert tuple(plan) == PILOT_STEPS
    assert plan[20] == plan[40] == plan[80] == "relocate_after_merge"
    assert plan[60] == "relocate_after_registered_evaluation"
    assert plan[100] == "retain_final_on_shared"


def test_step60_evaluation_wait_does_not_block_later_checkpoint_retention() -> None:
    plan = execution_plan()

    assert plan == (
        (20, "relocate_after_merge"),
        (40, "relocate_after_merge"),
        (60, "retain_for_registered_evaluation"),
        (80, "relocate_after_merge"),
        (100, "retain_final_on_shared"),
        (60, "relocate_after_registered_evaluation"),
    )
    assert plan.index((80, "relocate_after_merge")) < plan.index(
        (60, "relocate_after_registered_evaluation")
    )


def test_step60_marker_binds_evaluation_to_exact_merged_checkpoint(tmp_path: Path) -> None:
    actor = tmp_path / "global_step_60" / "actor"
    merged = actor / "huggingface"
    merged.mkdir(parents=True)
    index = merged / "model.safetensors.index.json"
    index.write_text('{"weight_map":{"x":"model.safetensors"}}\n', encoding="utf-8")
    marker = tmp_path / "step60.json"
    marker.write_text(
        json.dumps(
            {
                "schema_version": "blind-gains.pilot-step-eval-marker.v1",
                "status": "complete",
                "global_step": 60,
                "checkpoint_path": str(merged),
                "checkpoint_index_sha256": _sha256(index),
                "evaluation_run": "experiments/runs/eval",
                "evaluation_output_sha256": "a" * 64,
            }
        ),
        encoding="utf-8",
    )

    assert valid_evaluation_marker(marker, step=60, actor_dir=actor)
    index.write_text('{"weight_map":{"changed":"model.safetensors"}}\n', encoding="utf-8")
    assert not valid_evaluation_marker(marker, step=60, actor_dir=actor)


def test_step60_marker_rejects_success_claim_without_evaluation_hash(tmp_path: Path) -> None:
    actor = tmp_path / "global_step_60" / "actor"
    merged = actor / "huggingface"
    merged.mkdir(parents=True)
    index = merged / "model.safetensors.index.json"
    index.write_text("{}\n", encoding="utf-8")
    marker = tmp_path / "step60.json"
    marker.write_text(
        json.dumps(
            {
                "schema_version": "blind-gains.pilot-step-eval-marker.v1",
                "status": "complete",
                "global_step": 60,
                "checkpoint_path": str(merged),
                "checkpoint_index_sha256": _sha256(index),
                "evaluation_run": "experiments/runs/eval",
                "evaluation_output_sha256": None,
            }
        ),
        encoding="utf-8",
    )

    assert not valid_evaluation_marker(marker, step=60, actor_dir=actor)
