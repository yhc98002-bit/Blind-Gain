"""Adversarial fixtures (I10) for the Gate-1 completion acceptance audit.

A planted fixture repo satisfies all nine §9 acceptance conditions AND carries
poisoned sealed files (`experiment_log.jsonl`, `generations.log`,
`predictions.jsonl` in the run dir, the checkpoint root, and inside a
`global_step_*` dir) whose *parse* would crash. The new audit must PASS it —
proof it never opens a sealed file — while the predecessor
(`scripts/audit_mini_a5_acceptance.py`) crashes parsing the poisoned
`experiment_log.jsonl`: the adversarial fixture its predecessor fails.

Every acceptance condition is then violated one at a time and the audit must
refuse (verdict FAIL or a fail-closed Refusal that writes nothing).
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

import scripts.audit_mini_a5_acceptance as predecessor
from scripts.audit_mini_a5_gate1_acceptance import (
    ARM_CONFIGS,
    ARM_TRAIN_DATA,
    DATA_HASH_COMMON_INPUTS,
    DEFAULT_CKPTS,
    DEFAULT_RUNS,
    EXPECTED_MODEL_REVISION,
    MARKER_PATH,
    REGISTRATION_DOC,
    REQUIRED_FIXTURE_TESTS,
    RETENTION_LEDGER,
    TEMPLATE_CONFIG,
    Refusal,
    SealingViolation,
    composite_data_hash,
    read_json,
    read_text,
    run_audit,
)
from src.fliptrack.schema import sha256_file

REPO_CHECKER = Path("scripts/check_mini_a5_matched_diff.py")
UTC = "2026-08-08T00:00:00Z"
POISON_JSONL = b'{"step": 120, "reward": POISONED-NOT-JSON\n'


def _config(root: Path, mode: str | None) -> dict:
    """Member template config; per-arm configs differ in exactly the 3 keys."""
    if mode is None:
        train = "data/mini_a5_member_train_v1/train.parquet"
        name = "mini_a5_same_data_seed1"
        save = "checkpoints/mini_a5/mini_a5_same_data_seed1"
    else:
        train = ARM_TRAIN_DATA[mode]
        name = f"mini_a5_{mode}_seed1"
        save = f"checkpoints/mini_a5/mini_a5_{mode}_seed1"
    return {
        "data": {
            "train_files": train,
            "val_files": "data/mini_a5_plumbing_val_v1.jsonl",
            "pair_group_mode": "member",
        },
        "algorithm": {"adv_estimator": "grpo"},
        "worker": {
            "reward": {
                "reward_function": f"{root}/src/rewards/cp_grpo_reward.py:compute_member_score",
            },
        },
        "trainer": {
            "experiment_name": name,
            "save_checkpoint_path": save,
            "max_steps": 120,
            "save_freq": 20,
        },
    }


def _corpus_report(parquet_sha: str, audit_key: str, checks: dict) -> dict:
    return {
        "schema_version": "fixture-corpus-build.v1",
        "output_sha256": {"train.parquet": parquet_sha, "train.jsonl": "aa" * 32},
        "source_sha256": {"train.parquet": "bb" * 32, "train.jsonl": "cc" * 32},
        audit_key: {"checks": checks, "errors": []},
    }


def build_repo(tmp_path: Path) -> SimpleNamespace:
    root = tmp_path / "repo"
    for rel in ("configs/train", "data", "docs", "reports", "scripts",
                "src/train", "src/rewards", "tests", "experiments/runs",
                "checkpoints/mini_a5"):
        (root / rel).mkdir(parents=True, exist_ok=True)

    # Registered inputs of the launcher's composite data hash.
    (root / ARM_TRAIN_DATA["std"]).parent.mkdir(parents=True, exist_ok=True)
    (root / ARM_TRAIN_DATA["necessity"]).parent.mkdir(parents=True, exist_ok=True)
    (root / ARM_TRAIN_DATA["std"]).write_bytes(b"std-corpus-parquet-v1\n")
    (root / ARM_TRAIN_DATA["necessity"]).write_bytes(b"necessity-corpus-parquet-v1\n")
    for rel in DATA_HASH_COMMON_INPUTS:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_bytes(f"fixture:{rel}\n".encode())

    (root / REGISTRATION_DOC).write_text("# fixture Gate-1 registration\n", encoding="utf-8")
    (root / RETENTION_LEDGER).write_text("# fixture retention ledger\n", encoding="utf-8")
    shutil.copyfile(REPO_CHECKER, root / "scripts/check_mini_a5_matched_diff.py")
    for rel in REQUIRED_FIXTURE_TESTS:
        (root / rel).write_text("", encoding="utf-8")

    (root / TEMPLATE_CONFIG).write_text(yaml.safe_dump(_config(root, None)), encoding="utf-8")
    for mode in ("std", "necessity"):
        (root / ARM_CONFIGS[mode]).write_text(
            yaml.safe_dump(_config(root, mode)), encoding="utf-8")

    std_checks = {
        "row_for_row_identity_with_member_a": True,
        "synthetic_uids_disjoint_from_real_uids": True,
        "adjacent_pseudo_pairs": True,
        "seven_column_schema": True,
        "status_pass": True,
    }
    nec_checks = {
        "slots_byte_identical_to_source": True,
        "empirical_draw_frequency_consistent": True,
        "draw_reproducible_from_build_seed": True,
        "adjacent_synthetic_pseudo_pairs": True,
        "seven_column_schema": True,
        "status_pass": True,
    }
    std_report_path = root / "reports/mini_a5_std_corpus_build_v1.json"
    nec_report_path = root / "reports/mini_a5_necessity_corpus_build_v1.json"
    std_report_path.write_text(json.dumps(_corpus_report(
        sha256_file(root / ARM_TRAIN_DATA["std"]), "projection_audit", std_checks),
        indent=2, sort_keys=True) + "\n", encoding="utf-8")
    nec_report_path.write_text(json.dumps(_corpus_report(
        sha256_file(root / ARM_TRAIN_DATA["necessity"]), "resample_audit", nec_checks),
        indent=2, sort_keys=True) + "\n", encoding="utf-8")

    runs = dict(DEFAULT_RUNS)
    ckpts = dict(DEFAULT_CKPTS)
    patch_bytes = b"diff --git fixture easyr1 overlay\n"

    for mode in ("std", "necessity"):
        run_dir = root / runs[mode]
        (run_dir / "logs").mkdir(parents=True)
        shutil.copyfile(root / ARM_CONFIGS[mode], run_dir / "effective_config.yaml")
        (run_dir / "easyr1_worktree.patch").write_bytes(patch_bytes)
        (run_dir / "logs" / "an29.log").write_text(
            "launch ok on an29\n"
            '(Runner pid=1)     "pair_group_mode": "member"\n'
            "step 120 complete without incident\n",
            encoding="utf-8")
        (run_dir / "predictions.jsonl").write_bytes(POISON_JSONL)

        ckpt = root / ckpts[mode]
        for step in range(20, 121, 20):
            actor = ckpt / f"global_step_{step}" / "actor"
            actor.mkdir(parents=True)
            (actor / "model.safetensors").write_bytes(f"weights-{mode}-{step}".encode())
            (ckpt / f"global_step_{step}" / "dataloader.pt").write_bytes(b"dl")
        (ckpt / "global_step_120" / "predictions.jsonl").write_bytes(POISON_JSONL)
        (ckpt / "checkpoint_tracker.json").write_text(json.dumps({
            "best_global_step": 20,
            "best_val_reward_score": 0.0,
            "last_global_step": 120,
            "last_actor_path": str(ckpt / "global_step_120" / "actor"),
        }), encoding="utf-8")
        # Poisoned sealed endpoint-bearing files: parsing any of them crashes.
        (ckpt / "experiment_log.jsonl").write_bytes(POISON_JSONL)
        (ckpt / "generations.log").write_bytes(b"\x00\xffPOISONED-GENERATIONS")

    marker = {
        "schema_version": "blind-gains.mini-a5-gate1-completion-registration-marker.v1",
        "status": "registered",
        "arms_authorized": ["std", "necessity"],
        "registration_commit": "fixture0commit",
        "registration_document": REGISTRATION_DOC,
        "registration_document_sha256": sha256_file(root / REGISTRATION_DOC),
        "main_optimizer_steps_authorized_per_arm": 120,
        "easyr1_revision": "fixture-easyr1-rev",
        "easyr1_worktree_diff_sha256": sha256_file(
            root / runs["std"] / "easyr1_worktree.patch"),
        "main_config_sha256": {m: sha256_file(root / ARM_CONFIGS[m]) for m in ("std", "necessity")},
        "train_corpus_sha256": {m: sha256_file(root / ARM_TRAIN_DATA[m]) for m in ("std", "necessity")},
        "artifact_sha256": {
            "matched_diff_checker": sha256_file(root / "scripts/check_mini_a5_matched_diff.py"),
            "member_config": sha256_file(root / TEMPLATE_CONFIG),
            "std_build_report": sha256_file(std_report_path),
            "necessity_build_report": sha256_file(nec_report_path),
        },
        "checks": {
            "std_projection_audit_passed": True,
            "necessity_resample_audit_passed": True,
            "necessity_draw_frequency_audit_passed": True,
            "matched_difference_audit_passed": True,
        },
    }
    marker_path = root / MARKER_PATH
    marker_path.write_text(json.dumps(marker, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    marker_sha = sha256_file(marker_path)

    for mode in ("std", "necessity"):
        run_rel = runs[mode]
        run_dir = root / run_rel
        ckpt = root / ckpts[mode]
        manifest = {
            "schema_version": "blind-gains.run-manifest.v1",
            "run_id": Path(run_rel).name,
            "job_type": "m6_mini_a5_registered_main",
            "main_mode": mode,
            "status": "complete",
            "node": "an29",
            "gpu_allocation": "0,1,2,3,4,5,6,7",
            "gpu_ids": list(range(8)),
            "tensor_parallel_width": 1,
            "replica_count": 8,
            "placement_policy_version": "pi-2026-07-11",
            "placement_justification": "fixture: one arm on one fully free 8-GPU node",
            "git_hash": "f" * 40,
            "registration_commit": "fixture0commit",
            "registration_marker": MARKER_PATH,
            "registration_marker_sha256": marker_sha,
            "config_path": f"{run_rel}/effective_config.yaml",
            "config_hash": sha256_file(run_dir / "effective_config.yaml"),
            "data_manifest": ARM_TRAIN_DATA[mode],
            "data_manifest_hash": composite_data_hash(root, mode),
            "model_revision": EXPECTED_MODEL_REVISION,
            "seed": 20260716,
            "optimizer_steps_expected": 120,
            "command": ("PYTHONPATH=fixture python -u -m verl.trainer.main "
                        f"config={root}/{run_rel}/effective_config.yaml"),
            "start_time_utc": "2026-08-07T01:30:34Z",
            "end_time_utc": "2026-08-07T22:14:42Z",
            "exit_code": 0,
            "stdout_stderr_log": f"{run_rel}/logs/an29.log",
            "checkpoint_path": str(ckpt),
            "easyr1_revision": "fixture-easyr1-rev",
            "easyr1_worktree_patch": f"{run_rel}/easyr1_worktree.patch",
            "easyr1_worktree_patch_sha256": sha256_file(run_dir / "easyr1_worktree.patch"),
            "expected_artifacts": [
                f"{run_rel}/effective_config.yaml",
                f"{run_rel}/easyr1_worktree.patch",
                str(ckpt / "global_step_120"),
                str(ckpt / "experiment_log.jsonl"),
            ],
            "scientific_gate_decision": None,
            "deviations": [],
        }
        (run_dir / "run_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return SimpleNamespace(
        root=root,
        runs=runs,
        ckpts=ckpts,
        out_json=root / "reports/mini_a5_gate1_acceptance_audit_v1.json",
        out_md=root / "reports/mini_a5_gate1_acceptance_audit_v1.md",
    )


def _audit(fx, out_suffix: str = "") -> dict:
    out_json = fx.out_json if not out_suffix else fx.out_json.with_name(
        fx.out_json.stem + out_suffix + ".json")
    out_md = fx.out_md if not out_suffix else fx.out_md.with_name(
        fx.out_md.stem + out_suffix + ".md")
    return run_audit(
        root=fx.root, runs=fx.runs, ckpts=fx.ckpts,
        out_json=out_json, out_md=out_md, utc_override=UTC)


def _edit_manifest(fx, mode: str, **updates) -> None:
    path = fx.root / fx.runs[mode] / "run_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest.update(updates)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_planted_pass_is_deterministic_and_never_opens_sealed_files(tmp_path):
    fx = build_repo(tmp_path)
    report = _audit(fx)
    assert report["verdict"] == "PASS"
    assert report["failures"] == []
    assert report["schema_version"] == "blind-gains.mini-a5-gate1-acceptance-audit.v1"
    assert fx.out_json.is_file() and fx.out_md.is_file()
    # Full hash inventory recorded for every saved checkpoint of both arms.
    for mode in ("std", "necessity"):
        inventory = report["arms"][mode]["checkpoint_inventory"]
        steps = [k for k in inventory if k.startswith("global_step_")]
        assert len(steps) == 6
        assert all(inventory[k]["n_files"] >= 1 for k in steps)
    # The poisoned predictions file inside global_step_120 was hashed (bytes
    # only), never parsed — parsing it would have raised.
    step120 = report["arms"]["std"]["checkpoint_inventory"]["global_step_120"]
    assert "predictions.jsonl" in step120["files"]
    # Determinism: identical bytes on a second run with the same pinned UTC.
    report2 = _audit(fx, out_suffix="_replay")
    assert report2 == report
    assert fx.out_json.read_bytes() == fx.out_json.with_name(
        fx.out_json.stem + "_replay.json").read_bytes()
    assert fx.out_md.read_bytes() == fx.out_md.with_name(
        fx.out_md.stem + "_replay.md").read_bytes()


def test_main_exit_codes(tmp_path, monkeypatch):
    from scripts.audit_mini_a5_gate1_acceptance import main
    fx = build_repo(tmp_path)
    argv = ["audit", "--root", str(fx.root), "--utc-override", UTC]
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 0
    # FAIL path exits 1 (fresh fixture, one violated condition).
    fx2 = build_repo(tmp_path / "second")
    _edit_manifest(fx2, "std", exit_code=3, status="failed")
    monkeypatch.setattr(sys, "argv", ["audit", "--root", str(fx2.root),
                                      "--utc-override", UTC])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 1


def test_sealing_guard_refuses_sealed_basenames(tmp_path):
    fx = build_repo(tmp_path)
    with pytest.raises(SealingViolation):
        read_json(fx.root / fx.ckpts["std"] / "experiment_log.jsonl")
    with pytest.raises(SealingViolation):
        read_text(fx.root / fx.runs["std"] / "predictions.jsonl")
    with pytest.raises(SealingViolation):
        read_text(fx.root / fx.ckpts["std"] / "generations.log")


def test_predecessor_fails_the_sealed_fixture_new_audit_passes(tmp_path, monkeypatch):
    """I10: the predecessor audit fails this adversarial fixture.

    scripts/audit_mini_a5_acceptance.py takes its step count by parsing the
    sealed checkpoints' experiment_log.jsonl; on the poisoned fixture it
    crashes before writing anything. The Gate-1 audit passes the same tree.
    """
    fx = build_repo(tmp_path)
    monkeypatch.setattr(predecessor, "ROOT", fx.root)
    monkeypatch.setattr(predecessor, "ARMS", {
        "cp": {"run": fx.runs["std"], "ckpt": fx.ckpts["std"]},
        "member": {"run": None, "ckpt": fx.ckpts["necessity"]},
    })
    monkeypatch.setattr(sys, "argv", [
        "audit_mini_a5_acceptance.py", "--member-run", fx.runs["necessity"]])
    with pytest.raises(json.JSONDecodeError):
        predecessor.main()
    assert not (fx.root / "reports/mini_a5_acceptance_audit_v1.json").exists()
    assert _audit(fx)["verdict"] == "PASS"


def _violate_c1_exit(fx):
    _edit_manifest(fx, "std", exit_code=3, status="failed")


def _violate_c1_steps(fx):
    tracker = fx.root / fx.ckpts["necessity"] / "checkpoint_tracker.json"
    payload = json.loads(tracker.read_text(encoding="utf-8"))
    payload["last_global_step"] = 100
    tracker.write_text(json.dumps(payload), encoding="utf-8")


def _violate_c2_config_drift(fx):
    path = fx.root / fx.runs["std"] / "effective_config.yaml"
    path.write_text(path.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")


def _violate_c2_marker_tamper(fx):
    marker = json.loads((fx.root / MARKER_PATH).read_text(encoding="utf-8"))
    marker["main_optimizer_steps_authorized_per_arm"] = 100
    (fx.root / MARKER_PATH).write_text(
        json.dumps(marker, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _violate_c3_joint_branch(fx):
    log = fx.root / fx.runs["necessity"] / "logs" / "an29.log"
    with log.open("a", encoding="utf-8") as handle:
        handle.write('(Runner pid=9)     "pair_group_mode": "joint"\n')


def _violate_c3_cp_marker(fx):
    log = fx.root / fx.runs["std"] / "logs" / "an29.log"
    with log.open("a", encoding="utf-8") as handle:
        handle.write("BLIND_GAINS_CP_ADVANTAGE_AUDIT {\"groups\": 2}\n")


def _violate_c4_traceback(fx):
    log = fx.root / fx.runs["std"] / "logs" / "an29.log"
    with log.open("a", encoding="utf-8") as handle:
        handle.write("Traceback (most recent call last):\n")


def _violate_c4_nan(fx):
    log = fx.root / fx.runs["necessity"] / "logs" / "an29.log"
    with log.open("a", encoding="utf-8") as handle:
        handle.write("grad norm became nan at step 7\n")


def _violate_c5_missing_step(fx):
    shutil.rmtree(fx.root / fx.ckpts["std"] / "global_step_60")


def _violate_c5_missing_ledger(fx):
    (fx.root / RETENTION_LEDGER).unlink()


def _violate_c6_readout_exists(fx):
    (fx.root / "reports/mini_a5_gate1_endpoint_readout_v1.json").write_text(
        "{}", encoding="utf-8")


def _violate_c7_failed_projection(fx):
    path = fx.root / "reports/mini_a5_std_corpus_build_v1.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["projection_audit"]["checks"]["row_for_row_identity_with_member_a"] = False
    payload["projection_audit"]["checks"]["status_pass"] = False
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _violate_c8_extra_diff(fx):
    config = yaml.safe_load((fx.root / ARM_CONFIGS["std"]).read_text(encoding="utf-8"))
    config["trainer"]["save_freq"] = 40
    text = yaml.safe_dump(config)
    (fx.root / ARM_CONFIGS["std"]).write_text(text, encoding="utf-8")
    (fx.root / fx.runs["std"] / "effective_config.yaml").write_text(text, encoding="utf-8")


def _violate_c9_missing_fixture_test(fx):
    (fx.root / "tests/test_check_mini_a5_matched_diff_fixture.py").unlink()


def _violate_c9_output_identical_to_source(fx):
    path = fx.root / "reports/mini_a5_necessity_corpus_build_v1.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["output_sha256"]["train.parquet"] = payload["source_sha256"]["train.parquet"]
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@pytest.mark.parametrize("mutate, expected", [
    (_violate_c1_exit, "C1/std"),
    (_violate_c1_steps, "C1/necessity"),
    (_violate_c2_config_drift, "C2"),
    (_violate_c2_marker_tamper, "C2"),
    (_violate_c3_joint_branch, "C3/necessity"),
    (_violate_c3_cp_marker, "C3/std"),
    (_violate_c4_traceback, "C4/std"),
    (_violate_c4_nan, "C4/necessity"),
    (_violate_c5_missing_step, "C5/std"),
    (_violate_c5_missing_ledger, "C5"),
    (_violate_c6_readout_exists, "C6"),
    (_violate_c7_failed_projection, "C7/std"),
    (_violate_c8_extra_diff, "C8"),
    (_violate_c9_missing_fixture_test, "C9"),
    (_violate_c9_output_identical_to_source, "C9"),
], ids=lambda value: getattr(value, "__name__", str(value)))
def test_each_condition_violated_is_refused(tmp_path, mutate, expected):
    fx = build_repo(tmp_path)
    mutate(fx)
    report = _audit(fx)
    assert report["verdict"] == "FAIL"
    assert any(failure.startswith(expected) for failure in report["failures"]), (
        expected, report["failures"])


def test_running_arm_refused_without_writing_any_report(tmp_path):
    fx = build_repo(tmp_path)
    _edit_manifest(fx, "necessity", status="running", end_time_utc=None, exit_code=None)
    with pytest.raises(Refusal, match="partial audits"):
        _audit(fx)
    assert not fx.out_json.exists()
    assert not fx.out_md.exists()


def test_missing_run_dir_refused_without_writing(tmp_path):
    fx = build_repo(tmp_path)
    shutil.rmtree(fx.root / fx.runs["std"])
    with pytest.raises(Refusal, match="run dir missing"):
        _audit(fx)
    assert not fx.out_json.exists()


def test_existing_report_never_overwritten(tmp_path):
    fx = build_repo(tmp_path)
    fx.out_json.write_text("sentinel", encoding="utf-8")
    with pytest.raises(Refusal, match="never overwritten"):
        _audit(fx)
    assert fx.out_json.read_text(encoding="utf-8") == "sentinel"
