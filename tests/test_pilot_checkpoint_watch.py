from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.watch_anchor_checkpoints import valid_evaluation_marker
from scripts.watch_pilot_checkpoints import (
    GEO3K_MARKER_SCHEMA_VERSION,
    PILOT_STEPS,
    execution_plan,
    pilot_evaluation_barriers_ready,
    relocation_plan,
)


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


def test_step60_relocation_requires_r19_and_geo3k_audit_markers(
    tmp_path: Path,
) -> None:
    actor = tmp_path / "checkpoints/pilot/run/global_step_60/actor"
    merged = actor / "huggingface"
    merged.mkdir(parents=True)
    index = merged / "model.safetensors.index.json"
    index.write_text("{}\n", encoding="utf-8")
    r19_marker = tmp_path / "r19.json"
    r19_marker.write_text(
        json.dumps(
            {
                "schema_version": "blind-gains.pilot-step-eval-marker.v1",
                "status": "complete",
                "global_step": 60,
                "checkpoint_path": str(merged),
                "checkpoint_index_sha256": _sha256(index),
                "evaluation_run": "experiments/runs/r19",
                "evaluation_output_sha256": "a" * 64,
            }
        ),
        encoding="utf-8",
    )
    geo3k_marker = tmp_path / "geo3k.json"

    # This is the production race: R19 completed while Geometry3K had not.
    assert not pilot_evaluation_barriers_ready(
        r19_marker,
        geo3k_marker,
        step=60,
        actor_dir=actor,
        root=tmp_path,
    )

    evaluation = tmp_path / "experiments/runs/geo3k"
    evaluation.mkdir(parents=True)
    evaluation_manifest = evaluation / "run_manifest.json"
    evaluation_manifest.write_text('{"status":"complete"}\n', encoding="utf-8")
    audit_run = tmp_path / "experiments/runs/geo3k_audit"
    audit_run.mkdir(parents=True)
    audit = audit_run / "audit.json"
    audit.write_text('{"status":"pass"}\n', encoding="utf-8")
    geo3k_marker.write_text(
        json.dumps(
            {
                "schema_version": GEO3K_MARKER_SCHEMA_VERSION,
                "status": "complete",
                "global_step": 60,
                "checkpoint_path": str(merged),
                "checkpoint_index_sha256": _sha256(index),
                "evaluation_run": str(evaluation.relative_to(tmp_path)),
                "evaluation_manifest_sha256": _sha256(evaluation_manifest),
                "evaluation_output_sha256": "b" * 64,
                "audit_run": str(audit_run.relative_to(tmp_path)),
                "audit_sha256": _sha256(audit),
                "row_count": 601,
                "performance_values_opened": False,
            }
        ),
        encoding="utf-8",
    )

    assert pilot_evaluation_barriers_ready(
        r19_marker,
        geo3k_marker,
        step=60,
        actor_dir=actor,
        root=tmp_path,
    )
    audit.write_text('{"status":"changed"}\n', encoding="utf-8")
    assert not pilot_evaluation_barriers_ready(
        r19_marker,
        geo3k_marker,
        step=60,
        actor_dir=actor,
        root=tmp_path,
    )
