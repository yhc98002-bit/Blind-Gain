from __future__ import annotations

import json
from pathlib import Path

import yaml

from scripts.audit_mini_a5_plumbing_smoke import audit_single_run, parse_cp_markers
from src.fliptrack.schema import sha256_file


ROOT = Path(__file__).resolve().parents[1]


def _fixture(tmp_path: Path, mode: str) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    source_config = ROOT / f"configs/train/mini_a5_{'cp' if mode == 'cp' else 'member'}_plumbing_smoke_v1.yaml"
    config = yaml.safe_load(source_config.read_text(encoding="utf-8"))
    config_path = tmp_path / f"{mode}.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    # The runtime auditor binds byte-exact registered configs.
    config_path.write_bytes(source_config.read_bytes())
    checkpoint = tmp_path / f"{mode}-checkpoint"
    step = checkpoint / "global_step_1"
    step.mkdir(parents=True)
    (step / "model.pt").write_bytes(b"model")
    experiment = {
        "step": 1,
        "actor": {"pg_loss": 0.1, "grad_norm": 0.2},
        "reward": {
            "overall": 0.2,
            "accuracy": 0.3,
            "member_accuracy": 0.3,
            "pair_joint_accuracy": 0.2 if mode == "cp" else 0.0,
        },
    }
    (checkpoint / "experiment_log.jsonl").write_text(
        json.dumps(experiment) + "\n", encoding="utf-8"
    )
    log = tmp_path / f"{mode}.log"
    marker = {
        "row_count": 80,
        "pair_count": 8,
        "rollout_counts": [5],
        "advantages_finite": True,
    }
    log.write_text(
        ("BLIND_GAINS_CP_ADVANTAGE_AUDIT " + json.dumps(marker) + "\n")
        if mode == "cp"
        else "member advantage path\n",
        encoding="utf-8",
    )
    registration = {
        "status": "registered",
        "registration_commit": "a" * 40,
        "main_optimizer_steps_authorized": 0,
        "easyr1_worktree_diff_sha256": sha256_file(log),
    }
    registration_path = tmp_path / "registration.json"
    registration_path.write_text(json.dumps(registration), encoding="utf-8")
    overlay = tmp_path / "overlay.diff"
    overlay.write_bytes(log.read_bytes())
    manifest = {
        "status": "complete",
        "exit_code": 0,
        "job_type": "m6_mini_a5_registered_plumbing_smoke",
        "smoke_mode": mode,
        "optimizer_steps_expected": 1,
        "main_m6_optimizer_steps_authorized": 0,
        "gpu_ids": list(range(8)),
        "tensor_parallel_width": 1,
        "replica_count": 8,
        "config_path": str(config_path),
        "config_hash": sha256_file(config_path),
        "registration_marker": str(registration_path),
        "registration_marker_sha256": sha256_file(registration_path),
        "registration_commit": "a" * 40,
        "easyr1_revision": "dd71bbd252694f5f850213eec15795b6b88d9fea",
        "easyr1_worktree_patch": str(overlay),
        "easyr1_worktree_patch_sha256": sha256_file(overlay),
        "stdout_stderr_log": str(log),
        "checkpoint_path": str(checkpoint),
        "node": "an12",
        "start_time_utc": "2026-07-16T00:00:00Z",
        "end_time_utc": "2026-07-16T00:01:00Z",
    }
    manifest_path = tmp_path / f"{mode}-manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def test_cp_and_member_runtime_fixtures_pass(tmp_path: Path) -> None:
    assert audit_single_run(_fixture(tmp_path / "cp", "cp"), "cp")["status"] == "pass"
    assert (
        audit_single_run(_fixture(tmp_path / "member", "member"), "member")["status"]
        == "pass"
    )


def test_adversarial_missing_cp_branch_marker_fails(tmp_path: Path) -> None:
    manifest_path = _fixture(tmp_path, "cp")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    Path(manifest["stdout_stderr_log"]).write_text("ordinary log\n", encoding="utf-8")
    result = audit_single_run(manifest_path, "cp")
    assert result["status"] == "fail"
    assert result["checks"]["runtime_advantage_branch_evidence_exact"] is False


def test_adversarial_nan_actor_metric_fails(tmp_path: Path) -> None:
    manifest_path = _fixture(tmp_path, "member")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    experiment = Path(manifest["checkpoint_path"]) / "experiment_log.jsonl"
    row = json.loads(experiment.read_text(encoding="utf-8"))
    row["actor"]["grad_norm"] = float("nan")
    experiment.write_text(json.dumps(row) + "\n", encoding="utf-8")
    result = audit_single_run(manifest_path, "member")
    assert result["status"] == "fail"
    assert result["checks"]["one_finite_actor_reward_training_row"] is False


def test_malformed_runtime_marker_is_reported() -> None:
    markers, errors = parse_cp_markers("BLIND_GAINS_CP_ADVANTAGE_AUDIT not-json")
    assert markers == []
    assert errors
