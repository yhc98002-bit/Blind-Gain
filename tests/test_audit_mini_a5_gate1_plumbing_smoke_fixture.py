"""Adversarial fixtures (I10) for the Gate-1 plumbing-smoke audit.

Each fixture plants a run directory a naive audit would wave through
(nonzero exit, joint-branch evidence in a member-mode run, a second
optimizer step, a swapped config) and requires the audit to reject it; a
faithful one-step member-mode run tree is the positive control.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from scripts.audit_mini_a5_gate1_plumbing_smoke import (
    EXPECTED_CONFIG_HASHES,
    audit_single_gate1_run,
    build_audit,
)

REPO_SMOKE_CONFIGS = {
    "std": Path("configs/train/mini_a5_std_plumbing_smoke_v1.yaml"),
    "necessity": Path("configs/train/mini_a5_necessity_plumbing_smoke_v1.yaml"),
}
STEP1_ROW = {
    "step": 1,
    "actor": {"pg_loss": 0.01, "grad_norm": 0.2},
    "reward": {
        "overall": 0.5,
        "accuracy": 0.5,
        "member_accuracy": 0.5,
        "pair_joint_accuracy": 0.0,
    },
}


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _make_run(tmp_path: Path, mode: str, start: str, end: str) -> Path:
    run_dir = tmp_path / f"run_{mode}"
    (run_dir / "logs").mkdir(parents=True)
    config_path = run_dir / "effective_config.yaml"
    shutil.copyfile(REPO_SMOKE_CONFIGS[mode], config_path)
    log_path = run_dir / "logs" / "an29.log"
    log_path.write_text("step 1 complete\n", encoding="utf-8")
    overlay = run_dir / "easyr1_worktree.patch"
    overlay_bytes = b"fixture overlay diff\n"
    overlay.write_bytes(overlay_bytes)
    checkpoint = tmp_path / f"checkpoint_{mode}"
    (checkpoint / "global_step_1").mkdir(parents=True)
    (checkpoint / "global_step_1" / "model.safetensors").write_bytes(b"weights")
    (checkpoint / "experiment_log.jsonl").write_text(
        json.dumps(STEP1_ROW) + "\n", encoding="utf-8"
    )
    marker = run_dir / "marker.json"
    marker_payload = {
        "status": "registered",
        "registration_commit": "f" * 40,
        "smoke_optimizer_steps_authorized_per_mode": 1,
        "easyr1_worktree_diff_sha256": _sha256_bytes(overlay_bytes),
    }
    marker.write_text(json.dumps(marker_payload), encoding="utf-8")
    manifest = {
        "schema_version": "blind-gains.run-manifest.v1",
        "run_id": f"mini_a5_{mode}_plumbing_smoke_an29_fixture",
        "job_type": "m6_mini_a5_registered_plumbing_smoke",
        "smoke_mode": mode,
        "status": "complete",
        "exit_code": 0,
        "node": "an29",
        "gpu_ids": [0, 1, 2, 3, 4, 5, 6, 7],
        "tensor_parallel_width": 1,
        "replica_count": 8,
        "registration_commit": "f" * 40,
        "registration_marker": str(marker),
        "registration_marker_sha256": _sha256_bytes(marker.read_bytes()),
        "config_path": str(config_path),
        "config_hash": EXPECTED_CONFIG_HASHES[mode],
        "optimizer_steps_expected": 1,
        "main_m6_optimizer_steps_authorized": 0,
        "start_time_utc": start,
        "end_time_utc": end,
        "stdout_stderr_log": str(log_path),
        "checkpoint_path": str(checkpoint),
        "easyr1_revision": "dd71bbd252694f5f850213eec15795b6b88d9fea",
        "easyr1_worktree_patch": str(overlay),
        "easyr1_worktree_patch_sha256": _sha256_bytes(overlay_bytes),
    }
    manifest_path = run_dir / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def _rewrite(manifest_path: Path, **updates):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update(updates)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")


@pytest.fixture()
def run_pair(tmp_path: Path):
    std = _make_run(tmp_path, "std", "2026-08-07T00:00:00Z", "2026-08-07T00:20:00Z")
    necessity = _make_run(
        tmp_path, "necessity", "2026-08-07T00:25:00Z", "2026-08-07T00:45:00Z"
    )
    return std, necessity


def test_faithful_runs_pass(run_pair):
    std, necessity = run_pair
    single = audit_single_gate1_run(std, "std")
    assert single["errors"] == []
    assert single["status"] == "pass"
    combined = build_audit(std, necessity)
    assert combined["status"] == "pass"
    assert combined["main_optimizer_steps_authorized_by_this_audit"] == 0


def test_nonzero_exit_fails(run_pair):
    std, _ = run_pair
    _rewrite(std, exit_code=1, status="failed")
    result = audit_single_gate1_run(std, "std")
    assert result["status"] == "fail"
    assert not result["checks"]["manifest_complete_exit0"]


def test_joint_branch_evidence_in_member_mode_fails(run_pair):
    """A member-mode smoke must never emit CP advantage-audit markers."""
    std, _ = run_pair
    manifest = json.loads(std.read_text(encoding="utf-8"))
    log_path = Path(manifest["stdout_stderr_log"])
    log_path.write_text(
        'BLIND_GAINS_CP_ADVANTAGE_AUDIT {"row_count": 80}\n', encoding="utf-8"
    )
    result = audit_single_gate1_run(std, "std")
    assert result["status"] == "fail"
    assert not result["checks"]["member_mode_no_joint_branch_evidence"]


def test_second_optimizer_step_fails(run_pair):
    std, _ = run_pair
    manifest = json.loads(std.read_text(encoding="utf-8"))
    experiment_log = Path(manifest["checkpoint_path"]) / "experiment_log.jsonl"
    second = dict(STEP1_ROW, step=2)
    experiment_log.write_text(
        json.dumps(STEP1_ROW) + "\n" + json.dumps(second) + "\n", encoding="utf-8"
    )
    _rewrite(std, optimizer_steps_expected=2)
    result = audit_single_gate1_run(std, "std")
    assert result["status"] == "fail"
    assert not result["checks"]["one_optimizer_step_only"]


def test_swapped_config_fails(run_pair):
    """Naive: launch the necessity smoke with the std config -- the per-mode
    hash pin must catch the swap."""
    std, necessity = run_pair
    std_manifest = json.loads(std.read_text(encoding="utf-8"))
    necessity_manifest = json.loads(necessity.read_text(encoding="utf-8"))
    shutil.copyfile(std_manifest["config_path"], necessity_manifest["config_path"])
    result = audit_single_gate1_run(necessity, "necessity")
    assert result["status"] == "fail"
    assert not result["checks"]["effective_config_hash_exact"]


def test_fatal_log_signature_fails(run_pair):
    std, _ = run_pair
    manifest = json.loads(std.read_text(encoding="utf-8"))
    Path(manifest["stdout_stderr_log"]).write_text(
        "Traceback (most recent call last):\n", encoding="utf-8"
    )
    result = audit_single_gate1_run(std, "std")
    assert result["status"] == "fail"
    assert not result["checks"]["training_log_present_without_fatal_signature"]


def test_overlapping_runs_fail_combined(run_pair):
    std, necessity = run_pair
    _rewrite(
        necessity,
        start_time_utc="2026-08-07T00:10:00Z",
        end_time_utc="2026-08-07T00:30:00Z",
    )
    combined = build_audit(std, necessity)
    assert combined["status"] == "fail"
    assert not combined["checks"]["sequential_nonoverlapping_runs"]
