#!/usr/bin/env python3
"""Acceptance audit for the Mini-A5 Gate-1 completion arms (std / necessity).

`docs/registered_mini_a5_gate1_completion_v1.md` §9 lists nine acceptance
conditions over the two Gate-1 completion arms, and §8 seals both arms: "no
prediction, metric, or accuracy file from arm 1 or arm 3 is opened before
**both** arms complete and the acceptance audit below passes". §9 condition 6
requires "an independent versioned report [that] records every check before
any endpoint value is read".

This script is that audit. It reads NO endpoint value: every content read is
routed through a sealing guard that refuses any prediction/metric/accuracy
basename — including `experiment_log.jsonl` and `generations.log`, which the
predecessor audit (`scripts/audit_mini_a5_acceptance.py`) parsed for its step
count. Optimizer-step evidence comes from `run_manifest.json`,
`checkpoint_tracker.json`, and the `global_step_*` directory inventory
instead; checkpoint files are hashed byte-wise only (never parsed).

Fail-closed refusals that write NOTHING (so the versioned report path is never
burned prematurely): missing run dir or manifest, unparseable manifest, an arm
still running (partial audits prohibited), or a pre-existing output (existing
reports are never overwritten). Every other defect is recorded as a named
check failure; verdict is PASS only if every check passes; exit code 1
otherwise.

Adversarial fixture (I10): tests/test_audit_mini_a5_gate1_acceptance_fixture.py.
The predecessor fails that fixture (it crashes parsing the poisoned, sealed
`experiment_log.jsonl`); this audit passes it without ever opening the file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from scripts.check_mini_a5_matched_diff import check as matched_diff_check
from scripts.check_mini_a5_matched_diff import flatten
from src.fliptrack.schema import sha256_file

SCHEMA_VERSION = "blind-gains.mini-a5-gate1-acceptance-audit.v1"
REGISTRATION_DOC = "docs/registered_mini_a5_gate1_completion_v1.md"
MARKER_PATH = "reports/mini_a5_gate1_completion_registration_marker_v1.json"
TEMPLATE_CONFIG = "configs/train/mini_a5_same_data_3b_v1.yaml"
MATCHED_DIFF_CHECKER = "scripts/check_mini_a5_matched_diff.py"
RETENTION_LEDGER = "reports/mini_a5_raw_checkpoint_retention.md"
ENDPOINT_READOUT_GLOB = "mini_a5_gate1_endpoint_readout*"
ARMS = ("std", "necessity")
DEFAULT_RUNS = {
    "std": "experiments/runs/mini_a5_std_main_an29_20260807T013033Z",
    "necessity": "experiments/runs/mini_a5_necessity_main_an29_20260807T222122Z",
}
DEFAULT_CKPTS = {
    "std": "checkpoints/mini_a5/mini_a5_std_seed1",
    "necessity": "checkpoints/mini_a5/mini_a5_necessity_seed1",
}
ARM_CONFIGS = {
    "std": "configs/train/mini_a5_std_3b_v1.yaml",
    "necessity": "configs/train/mini_a5_necessity_3b_v1.yaml",
}
ARM_TRAIN_DATA = {
    "std": "data/mini_a5_std_train_v1/train.parquet",
    "necessity": "data/mini_a5_necessity_train_v1/train.parquet",
}
# Inputs of the launcher's composite DATA_HASH (scripts/launch_mini_a5_main.sh):
# sha256sum of train data + these, sorted by path, then sha256 of that listing.
DATA_HASH_COMMON_INPUTS = (
    "data/mini_a5_plumbing_val_v1.jsonl",
    "data/mini_a5_fixed_subsets_v1_manifest.json",
    "docs/easyr1_mini_a5_pair_grouping_patch.diff",
    "src/train/cp_grouping.py",
    "src/rewards/cp_grpo_reward.py",
)
CORPUS_BUILD_REPORTS = {
    "std": ("reports/mini_a5_std_corpus_build_v1.json", "projection_audit", "std_build_report"),
    "necessity": ("reports/mini_a5_necessity_corpus_build_v1.json", "resample_audit", "necessity_build_report"),
}
MARKER_CORPUS_CHECKS = {
    "std": ("std_projection_audit_passed",),
    "necessity": ("necessity_resample_audit_passed", "necessity_draw_frequency_audit_passed"),
}
EXPECTED_MODEL_REVISION = (
    "ModelScope Qwen/Qwen2.5-VL-3B-Instruct master; tree "
    "84c656fb6d6a5f4ef3ccbf47c3880c3a3d22c63eb8736a88fa7a0ddb542e3568"
)
EXPECTED_STEPS = 120
EXPECTED_SEED = 20260716
EXPECTED_PLACEMENT_POLICY = "pi-2026-07-11"
EXPECTED_GPU_IDS = list(range(8))
EXPECTED_REWARD_SUFFIX = "src/rewards/cp_grpo_reward.py:compute_member_score"
CP_MARKER = "BLIND_GAINS_CP_ADVANTAGE_AUDIT"
JOINT_RE = re.compile(r"pair_group_mode[^\n]{0,120}joint", re.IGNORECASE)
MEMBER_ECHO_RE = re.compile(r"pair_group_mode\"?\s*[:=]\s*\"?member")
FATAL_LOG_PATTERNS = (
    (re.compile(r"\bnan\b", re.IGNORECASE), "NaN"),
    (re.compile(r"Traceback \(most recent call last\)"), "traceback"),
    (re.compile(r"CUDA out of memory|OutOfMemoryError"), "OOM"),
    (re.compile(r"ncclSystemError|ncclInternalError|ncclUnhandledCudaError"), "fatal NCCL"),
)
# Sealing guard (§8): any basename matching this is never opened by this audit.
SEALED_BASENAME_RE = re.compile(
    r"prediction|\bpreds\b|metric|accuracy|experiment_log|generations|endpoint_readout|answers",
    re.IGNORECASE,
)
SEALED_NOTE = (
    "No endpoint prediction/metric/accuracy value is read or reported by this "
    "audit; sealed basenames (experiment_log.jsonl, generations.log, "
    "predictions/metrics/accuracy files) are refused by a guard on every "
    "content read. Step counts come from run_manifest.json, "
    "checkpoint_tracker.json, and the global_step_* inventory."
)
# §9 condition 9: every new Gate-1 builder/audit ships an adversarial fixture.
REQUIRED_FIXTURE_TESTS = (
    "tests/test_build_mini_a5_std_corpus_fixture.py",
    "tests/test_build_mini_a5_necessity_corpus_fixture.py",
    "tests/test_build_mini_a5_gate1_marker_fixture.py",
    "tests/test_build_mini_a5_gate1_smoke_inputs_fixture.py",
    "tests/test_audit_mini_a5_gate1_plumbing_smoke_fixture.py",
    "tests/test_summarize_mini_a5_gate1_step0_fixture.py",
    "tests/test_build_mini_a5_gate1_endpoint_readout_fixture.py",
    "tests/test_check_mini_a5_matched_diff_fixture.py",
    "tests/test_audit_mini_a5_gate1_acceptance_fixture.py",
)


class Refusal(RuntimeError):
    """Fail-closed precondition failure: the audit refuses and writes nothing."""


class SealingViolation(RuntimeError):
    """The audit was asked to open a sealed (endpoint-bearing) file."""


def _assert_not_sealed(path: Path) -> Path:
    if SEALED_BASENAME_RE.search(path.name):
        raise SealingViolation(f"refusing to open sealed file: {path}")
    return path


def read_text(path: Path) -> str:
    return _assert_not_sealed(path).read_text(encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(read_text(path))


def read_yaml(path: Path) -> Any:
    return yaml.safe_load(read_text(path))


def composite_data_hash(root: Path, mode: str) -> str:
    """Recompute the launcher's DATA_HASH exactly (sorted sha256sum listing)."""
    rels = [ARM_TRAIN_DATA[mode], *DATA_HASH_COMMON_INPUTS, ARM_CONFIGS[mode]]
    lines = [f"{sha256_file(root / rel)}  {rel}" for rel in rels]
    text = "\n".join(sorted(lines, key=lambda line: line.split("  ", 1)[1])) + "\n"
    return hashlib.sha256(text.encode("ascii")).hexdigest()


def _flat_leaves_ending(config: dict, suffix: str) -> dict[str, Any]:
    flat = flatten(config)
    return {k: v for k, v in flat.items() if k == suffix or k.endswith("." + suffix)}


def _scan_logs(logs_dir: Path) -> dict[str, Any] | None:
    """One pass over every file under logs/: fatal signatures + grouping events.

    Sealed basenames are skipped (recorded), never opened.
    """
    if not logs_dir.is_dir():
        return None
    fatal = {label: 0 for _, label in FATAL_LOG_PATTERNS}
    result: dict[str, Any] = {
        "files_scanned": [],
        "sealed_files_skipped": [],
        "fatal": fatal,
        "cp_advantage_marker_hits": 0,
        "joint_branch_hits": 0,
        "member_echo_hits": 0,
    }
    for candidate in sorted(p for p in logs_dir.rglob("*") if p.is_file()):
        if SEALED_BASENAME_RE.search(candidate.name):
            result["sealed_files_skipped"].append(str(candidate.name))
            continue
        result["files_scanned"].append(str(candidate.relative_to(logs_dir)))
        with candidate.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                for pattern, label in FATAL_LOG_PATTERNS:
                    if pattern.search(line):
                        fatal[label] += 1
                if CP_MARKER in line:
                    result["cp_advantage_marker_hits"] += 1
                if JOINT_RE.search(line):
                    result["joint_branch_hits"] += 1
                if MEMBER_ECHO_RE.search(line):
                    result["member_echo_hits"] += 1
    return result


def _checkpoint_inventory(step_dir: Path) -> dict[str, Any]:
    files = sorted(p for p in step_dir.rglob("*") if p.is_file())
    return {
        "files": {
            str(p.relative_to(step_dir)): {
                "sha256": sha256_file(p),
                "bytes": p.stat().st_size,
            }
            for p in files
        },
        "n_files": len(files),
        "total_bytes": sum(p.stat().st_size for p in files),
    }


def _preflight(root: Path, runs: dict[str, str], out_json: Path, out_md: Path) -> dict[str, dict]:
    for out in (out_json, out_md):
        if out.exists():
            raise Refusal(f"output already exists and is never overwritten: {out}")
    manifests: dict[str, dict] = {}
    for arm in ARMS:
        run_dir = root / runs[arm]
        if not run_dir.is_dir():
            raise Refusal(f"{arm}: run dir missing: {run_dir}")
        manifest_path = run_dir / "run_manifest.json"
        if not manifest_path.is_file():
            raise Refusal(f"{arm}: run_manifest.json missing in {run_dir}")
        try:
            manifest = read_json(manifest_path)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise Refusal(f"{arm}: run_manifest.json unparseable: {exc}") from exc
        if not isinstance(manifest, dict) or "status" not in manifest:
            raise Refusal(f"{arm}: run_manifest.json has no status field")
        if manifest.get("status") == "running" or manifest.get("end_time_utc") in (None, ""):
            raise Refusal(
                f"{arm}: arm not finished (status={manifest.get('status')!r}, "
                f"end_time_utc={manifest.get('end_time_utc')!r}); partial audits "
                "are prohibited — no report written"
            )
        manifests[arm] = manifest
    return manifests


def run_audit(
    root: Path,
    runs: dict[str, str],
    ckpts: dict[str, str],
    out_json: Path,
    out_md: Path,
    utc_override: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    manifests = _preflight(root, runs, out_json, out_md)
    generated_at = utc_override or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "registration": REGISTRATION_DOC,
        "registration_marker": MARKER_PATH,
        "generated_at_utc": generated_at,
        "note": SEALED_NOTE,
        "arms": {arm: {"run": runs[arm], "checkpoint": ckpts[arm]} for arm in ARMS},
        "conditions": {},
    }
    failures: list[str] = []

    def fail(msg: str) -> None:
        failures.append(msg)

    marker_file = root / MARKER_PATH
    marker: dict[str, Any] | None = None
    marker_sha: str | None = None
    if marker_file.is_file():
        marker_sha = sha256_file(marker_file)
        try:
            marker = read_json(marker_file)
        except json.JSONDecodeError:
            marker = None

    log_scans = {arm: _scan_logs(root / runs[arm] / "logs") for arm in ARMS}
    effective_configs: dict[str, Any] = {}
    for arm in ARMS:
        cfg_path = root / runs[arm] / "effective_config.yaml"
        effective_configs[arm] = read_yaml(cfg_path) if cfg_path.is_file() else None

    # --- condition 1: exit code 0 and exactly 120 optimizer steps ------------
    c1: dict[str, Any] = {"note": (
        "Step evidence: run_manifest.json + checkpoint_tracker.json + "
        "global_step_* dirs. experiment_log.jsonl is sealed and never opened."
    )}
    for arm in ARMS:
        m = manifests[arm]
        ck = root / ckpts[arm]
        entry: dict[str, Any] = {
            "status": m.get("status"),
            "exit_code": m.get("exit_code"),
            "optimizer_steps_expected": m.get("optimizer_steps_expected"),
            "main_mode": m.get("main_mode"),
        }
        problems: list[str] = []
        if m.get("status") != "complete":
            problems.append(f"status={m.get('status')!r}")
        if m.get("exit_code") != 0:
            problems.append(f"exit_code={m.get('exit_code')!r}")
        if m.get("optimizer_steps_expected") != EXPECTED_STEPS:
            problems.append(f"optimizer_steps_expected={m.get('optimizer_steps_expected')!r}")
        if m.get("main_mode") != arm:
            problems.append(f"main_mode={m.get('main_mode')!r} != {arm}")
        if m.get("run_id") != Path(runs[arm]).name:
            problems.append(f"run_id={m.get('run_id')!r} != run dir name")
        if "artifacts_exist" in m and m["artifacts_exist"] is not True:
            problems.append(f"artifacts_exist={m['artifacts_exist']!r}")
        missing_artifacts = []
        for rel in m.get("expected_artifacts", []) or []:
            p = Path(rel)
            if not p.is_absolute():
                p = root / rel
            if not p.exists():
                missing_artifacts.append(rel)
        if missing_artifacts:
            problems.append(f"expected_artifacts missing: {missing_artifacts}")
        entry["expected_artifacts_missing"] = missing_artifacts
        steps = sorted(
            int(p.name.split("_")[-1])
            for p in ck.glob("global_step_*")
            if p.is_dir() and p.name.split("_")[-1].isdigit()
        ) if ck.is_dir() else []
        entry["global_steps_saved"] = steps
        if not steps or max(steps) != EXPECTED_STEPS or EXPECTED_STEPS not in steps:
            problems.append(f"global_step_{EXPECTED_STEPS} evidence missing (saved={steps})")
        tracker_path = ck / "checkpoint_tracker.json"
        if tracker_path.is_file():
            try:
                tracker = read_json(tracker_path)
                entry["tracker_last_global_step"] = tracker.get("last_global_step")
                if tracker.get("last_global_step") != EXPECTED_STEPS:
                    problems.append(
                        f"checkpoint_tracker last_global_step={tracker.get('last_global_step')!r}")
            except json.JSONDecodeError:
                problems.append("checkpoint_tracker.json unparseable")
        else:
            problems.append("checkpoint_tracker.json missing")
        entry["ok"] = not problems
        c1[arm] = entry
        for problem in problems:
            fail(f"C1/{arm}: {problem}")
    report["conditions"]["1_exit0_and_120_steps"] = c1

    # --- condition 2: hashes match this registration and its marker ----------
    c2: dict[str, Any] = {"marker_present": marker_file.is_file(), "marker_sha256": marker_sha}
    if marker is None:
        fail("C2: registration marker missing or unparseable")
        c2["ok"] = False
    else:
        problems = []
        if marker.get("status") != "registered":
            problems.append(f"marker status={marker.get('status')!r}")
        if sorted(marker.get("arms_authorized", [])) != sorted(ARMS):
            problems.append(f"arms_authorized={marker.get('arms_authorized')!r}")
        if marker.get("main_optimizer_steps_authorized_per_arm") != EXPECTED_STEPS:
            problems.append("marker does not authorize exactly 120 steps per arm")
        if marker.get("registration_document") != REGISTRATION_DOC:
            problems.append(f"marker registration_document={marker.get('registration_document')!r}")
        doc = root / REGISTRATION_DOC
        if not doc.is_file():
            problems.append("registration document missing")
        elif sha256_file(doc) != marker.get("registration_document_sha256"):
            problems.append("registration document sha256 drift vs marker")
        for arm in ARMS:
            m = manifests[arm]
            tag = f"{arm}: "
            if m.get("registration_marker") != MARKER_PATH:
                problems.append(tag + f"manifest registration_marker={m.get('registration_marker')!r}")
            if m.get("registration_marker_sha256") != marker_sha:
                problems.append(tag + "manifest marker sha256 != marker file sha256")
            if m.get("registration_commit") != marker.get("registration_commit"):
                problems.append(tag + "registration_commit mismatch vs marker")
            eff = root / runs[arm] / "effective_config.yaml"
            if not eff.is_file():
                problems.append(tag + "effective_config.yaml missing")
            else:
                eff_sha = sha256_file(eff)
                if eff_sha != m.get("config_hash"):
                    problems.append(tag + "effective config sha256 != manifest config_hash")
                if eff_sha != (marker.get("main_config_sha256") or {}).get(arm):
                    problems.append(tag + "effective config sha256 != marker main_config_sha256")
                reg_cfg = root / ARM_CONFIGS[arm]
                if not reg_cfg.is_file() or sha256_file(reg_cfg) != eff_sha:
                    problems.append(tag + f"registered config {ARM_CONFIGS[arm]} missing or != effective config")
            if m.get("config_path") != f"{runs[arm]}/effective_config.yaml":
                problems.append(tag + f"manifest config_path={m.get('config_path')!r}")
            if m.get("data_manifest") != ARM_TRAIN_DATA[arm]:
                problems.append(tag + f"manifest data_manifest={m.get('data_manifest')!r}")
            train = root / ARM_TRAIN_DATA[arm]
            if not train.is_file():
                problems.append(tag + "train corpus missing")
            elif sha256_file(train) != (marker.get("train_corpus_sha256") or {}).get(arm):
                problems.append(tag + "train corpus sha256 != marker train_corpus_sha256")
            try:
                if composite_data_hash(root, arm) != m.get("data_manifest_hash"):
                    problems.append(tag + "recomputed composite data hash != manifest data_manifest_hash")
            except FileNotFoundError as exc:
                problems.append(tag + f"data-hash input missing: {exc}")
            if m.get("model_revision") != EXPECTED_MODEL_REVISION:
                problems.append(tag + f"model_revision={m.get('model_revision')!r}")
            if m.get("easyr1_revision") != marker.get("easyr1_revision"):
                problems.append(tag + "easyr1_revision mismatch vs marker")
            patch = root / runs[arm] / "easyr1_worktree.patch"
            if not patch.is_file():
                problems.append(tag + "easyr1_worktree.patch missing")
            else:
                patch_sha = sha256_file(patch)
                if patch_sha != m.get("easyr1_worktree_patch_sha256"):
                    problems.append(tag + "patch sha256 != manifest easyr1_worktree_patch_sha256")
                if patch_sha != marker.get("easyr1_worktree_diff_sha256"):
                    problems.append(tag + "patch sha256 != marker easyr1_worktree_diff_sha256")
            if m.get("seed") != EXPECTED_SEED:
                problems.append(tag + f"seed={m.get('seed')!r}")
            if m.get("placement_policy_version") != EXPECTED_PLACEMENT_POLICY:
                problems.append(tag + f"placement_policy_version={m.get('placement_policy_version')!r}")
            if m.get("gpu_ids") != EXPECTED_GPU_IDS:
                problems.append(tag + f"gpu_ids={m.get('gpu_ids')!r}")
            if m.get("tensor_parallel_width") != 1 or m.get("replica_count") != 8:
                problems.append(tag + "placement geometry != single-node 8xTP1")
            if not str(m.get("node", "")).startswith("an"):
                problems.append(tag + f"node={m.get('node')!r} not a compute node")
            command = str(m.get("command", ""))
            if "verl.trainer.main" not in command or not command.rstrip().endswith(
                    f"{runs[arm]}/effective_config.yaml"):
                problems.append(tag + "manifest command is not the registered trainer command")
        c2["problems"] = problems
        c2["ok"] = not problems
        for problem in problems:
            fail(f"C2: {problem}")
    report["conditions"]["2_hashes_match_registration"] = c2

    # --- condition 3: member-mode discipline, never the joint branch ---------
    c3: dict[str, Any] = {"note": (
        "Member mode == per-source-prompt grouping. Machine evidence: the "
        "effective config resolves pair_group_mode=member and the member "
        "reward callback; the executed trainer echoes pair_group_mode member "
        "in its logs; zero joint-branch or CP advantage-audit markers appear "
        "in either arm's logs."
    )}
    for arm in ARMS:
        entry = {}
        problems = []
        cfg = effective_configs[arm]
        if not isinstance(cfg, dict):
            problems.append("effective config missing or unparseable")
        else:
            modes = _flat_leaves_ending(cfg, "pair_group_mode")
            entry["pair_group_mode"] = modes
            if not modes or any(v != "member" for v in modes.values()):
                problems.append(f"pair_group_mode leaves={modes!r} (expected all 'member')")
            rewards = _flat_leaves_ending(cfg, "reward_function")
            entry["reward_function"] = rewards
            if not rewards or any(not str(v).endswith(EXPECTED_REWARD_SUFFIX) for v in rewards.values()):
                problems.append(f"reward_function leaves={rewards!r} (expected *{EXPECTED_REWARD_SUFFIX})")
            max_steps = _flat_leaves_ending(cfg, "max_steps")
            if not max_steps or any(v != EXPECTED_STEPS for v in max_steps.values()):
                problems.append(f"max_steps leaves={max_steps!r} (expected {EXPECTED_STEPS})")
        scan = log_scans[arm]
        if scan is None:
            problems.append("logs dir missing")
        else:
            entry["cp_advantage_marker_hits"] = scan["cp_advantage_marker_hits"]
            entry["joint_branch_hits"] = scan["joint_branch_hits"]
            entry["member_echo_hits"] = scan["member_echo_hits"]
            if scan["cp_advantage_marker_hits"] != 0:
                problems.append(f"CP advantage-audit marker seen {scan['cp_advantage_marker_hits']}x")
            if scan["joint_branch_hits"] != 0:
                problems.append(f"joint-branch evidence seen {scan['joint_branch_hits']}x")
            if scan["member_echo_hits"] < 1:
                problems.append("no member pair_group_mode echo in logs")
        entry["ok"] = not problems
        c3[arm] = entry
        for problem in problems:
            fail(f"C3/{arm}: {problem}")
    report["conditions"]["3_member_mode_discipline"] = c3

    # --- condition 4: no NaN / traceback / OOM / fatal NCCL signature --------
    c4: dict[str, Any] = {}
    for arm in ARMS:
        scan = log_scans[arm]
        if scan is None:
            c4[arm] = {"ok": False, "why": "logs dir missing"}
            fail(f"C4/{arm}: logs dir missing")
            continue
        found = {label: n for label, n in scan["fatal"].items() if n > 0}
        c4[arm] = {
            "ok": not found,
            "found": found,
            "files_scanned": scan["files_scanned"],
            "sealed_files_skipped": scan["sealed_files_skipped"],
        }
        if found:
            fail(f"C4/{arm}: fatal signatures {found}")
    report["conditions"]["4_no_fatal_log_signatures"] = c4

    # --- condition 5: every saved checkpoint hash-inventoried ----------------
    c5: dict[str, Any] = {"note": (
        "Full per-file sha256 inventory of every saved global_step_* dir is "
        "recorded in this report (arms.<arm>.checkpoint_inventory) before any "
        "retention action; checkpoint files are hashed, never parsed."
    )}
    for arm in ARMS:
        ck = root / ckpts[arm]
        entry = {}
        problems = []
        cfg = effective_configs[arm]
        save_freq = None
        if isinstance(cfg, dict):
            freqs = _flat_leaves_ending(cfg, "save_freq")
            if len(set(freqs.values())) == 1:
                save_freq = next(iter(freqs.values()))
        if not isinstance(save_freq, int) or save_freq <= 0 or EXPECTED_STEPS % save_freq:
            problems.append(f"save_freq unreadable or invalid: {save_freq!r}")
        else:
            expected = [s for s in range(save_freq, EXPECTED_STEPS + 1, save_freq)]
            saved = sorted(
                int(p.name.split("_")[-1])
                for p in ck.glob("global_step_*")
                if p.is_dir() and p.name.split("_")[-1].isdigit()
            ) if ck.is_dir() else []
            entry["expected_steps"] = expected
            entry["saved_steps"] = saved
            if saved != expected:
                problems.append(
                    f"saved steps {saved} != expected {expected} "
                    "(missing steps imply retention before inventory)")
            inventory: dict[str, Any] = {}
            for step in saved:
                inv = _checkpoint_inventory(ck / f"global_step_{step}")
                inventory[f"global_step_{step}"] = inv
                if inv["n_files"] == 0:
                    problems.append(f"global_step_{step} is empty")
            tracker_path = ck / "checkpoint_tracker.json"
            if tracker_path.is_file():
                inventory["checkpoint_tracker.json"] = {
                    "sha256": sha256_file(tracker_path),
                    "bytes": tracker_path.stat().st_size,
                }
            report["arms"][arm]["checkpoint_inventory"] = inventory
            entry["inventory_files"] = sum(
                v["n_files"] for k, v in inventory.items() if k.startswith("global_step_"))
            entry["inventory_bytes"] = sum(
                v["total_bytes"] for k, v in inventory.items() if k.startswith("global_step_"))
        entry["ok"] = not problems
        c5[arm] = entry
        for problem in problems:
            fail(f"C5/{arm}: {problem}")
    ledger = root / RETENTION_LEDGER
    c5["retention_ledger_present"] = ledger.is_file()
    if not ledger.is_file():
        fail(f"C5: retention ledger missing: {RETENTION_LEDGER}")
    c5["ok"] = c5["retention_ledger_present"] and all(c5[arm]["ok"] for arm in ARMS)
    report["conditions"]["5_checkpoint_hash_inventory"] = c5

    # --- condition 6: this report precedes any endpoint readout --------------
    readout_artifacts = sorted(
        p.name for p in (root / "reports").glob(ENDPOINT_READOUT_GLOB)) if (root / "reports").is_dir() else []
    c6 = {
        "endpoint_readout_artifacts_present": readout_artifacts,
        "audit_written_at_utc": generated_at,
        "ok": not readout_artifacts,
        "note": (
            "This report is the §9 condition-6 record. The condition fails if "
            "any Gate-1 endpoint readout artifact already exists at audit "
            "time, and existing audit outputs are never overwritten."
        ),
    }
    if readout_artifacts:
        fail(f"C6: endpoint readout artifacts already exist: {readout_artifacts}")
    report["conditions"]["6_report_precedes_readout"] = c6

    # --- condition 7: corpus audits (T1 projection / T4 resample) passed -----
    c7: dict[str, Any] = {}
    for arm in ARMS:
        rel, audit_key, marker_key = CORPUS_BUILD_REPORTS[arm]
        entry = {"report": rel, "audit_key": audit_key}
        problems = []
        path = root / rel
        if not path.is_file():
            problems.append(f"build report missing: {rel}")
        else:
            report_sha = sha256_file(path)
            entry["report_sha256"] = report_sha
            if marker is not None and (marker.get("artifact_sha256") or {}).get(marker_key) != report_sha:
                problems.append(f"build report sha256 != marker artifact_sha256.{marker_key}")
            try:
                build = read_json(path)
            except json.JSONDecodeError:
                build = None
                problems.append("build report unparseable")
            if isinstance(build, dict):
                block = build.get(audit_key)
                checks = (block or {}).get("checks") if isinstance(block, dict) else None
                errors = (block or {}).get("errors") if isinstance(block, dict) else None
                entry["checks"] = checks
                if not isinstance(checks, dict) or not checks or not all(checks.values()):
                    problems.append(f"{audit_key}.checks not all true: {checks!r}")
                elif checks.get("status_pass") is not True:
                    problems.append(f"{audit_key}.checks.status_pass is not true")
                if errors:
                    problems.append(f"{audit_key}.errors nonempty: {errors!r}")
        for key in MARKER_CORPUS_CHECKS[arm]:
            if marker is None or (marker.get("checks") or {}).get(key) is not True:
                problems.append(f"marker.checks.{key} is not true")
        entry["ok"] = not problems
        c7[arm] = entry
        for problem in problems:
            fail(f"C7/{arm}: {problem}")
    report["conditions"]["7_prelaunch_corpus_audits"] = c7

    # --- condition 8: matched-difference discipline --------------------------
    c8: dict[str, Any] = {"allowed_changes": [
        "data.train_files", "trainer.experiment_name", "trainer.save_checkpoint_path"]}
    problems = []
    template = root / TEMPLATE_CONFIG
    checker = root / MATCHED_DIFF_CHECKER
    if not template.is_file():
        problems.append(f"template config missing: {TEMPLATE_CONFIG}")
    elif marker is not None and (marker.get("artifact_sha256") or {}).get("member_config") != sha256_file(template):
        problems.append("template config sha256 != marker artifact_sha256.member_config")
    if not checker.is_file():
        problems.append(f"matched-diff checker missing: {MATCHED_DIFF_CHECKER}")
    elif marker is not None and (marker.get("artifact_sha256") or {}).get("matched_diff_checker") != sha256_file(checker):
        problems.append("matched-diff checker sha256 != marker artifact_sha256.matched_diff_checker")
    if marker is not None and (marker.get("checks") or {}).get("matched_difference_audit_passed") is not True:
        problems.append("marker.checks.matched_difference_audit_passed is not true")
    if template.is_file():
        for arm in ARMS:
            for label, rel in (
                ("registered", ARM_CONFIGS[arm]),
                ("effective", f"{runs[arm]}/effective_config.yaml"),
            ):
                candidate = root / rel
                if not candidate.is_file():
                    problems.append(f"{arm}: {label} config missing: {rel}")
                    continue
                violations = matched_diff_check(candidate, template)
                c8[f"{arm}_{label}_violations"] = violations
                for violation in violations:
                    problems.append(f"{arm}/{label}: {violation}")
    c8["ok"] = not problems
    for problem in problems:
        fail(f"C8: {problem}")
    report["conditions"]["8_matched_difference"] = c8

    # --- condition 9: adversarial fixtures + audited-artifact non-identity ---
    c9: dict[str, Any] = {}
    problems = []
    missing_tests = [rel for rel in REQUIRED_FIXTURE_TESTS if not (root / rel).is_file()]
    c9["required_fixture_tests"] = list(REQUIRED_FIXTURE_TESTS)
    c9["missing_fixture_tests"] = missing_tests
    if missing_tests:
        problems.append(f"missing adversarial fixture tests: {missing_tests}")
    for arm in ARMS:
        rel = CORPUS_BUILD_REPORTS[arm][0]
        path = root / rel
        if not path.is_file():
            problems.append(f"{arm}: build report missing for non-identity check")
            continue
        try:
            build = read_json(path)
        except json.JSONDecodeError:
            problems.append(f"{arm}: build report unparseable for non-identity check")
            continue
        output = build.get("output_sha256") or {}
        source = build.get("source_sha256") or {}
        overlap = sorted(set(output) & set(source))
        c9[f"{arm}_compared_files"] = overlap
        if not overlap:
            problems.append(f"{arm}: no overlapping output/source files to compare")
        identical = [name for name in overlap if output[name] == source[name]]
        if identical:
            problems.append(f"{arm}: audited output byte-identical to source: {identical}")
    c9["ok"] = not problems
    for problem in problems:
        fail(f"C9: {problem}")
    report["conditions"]["9_fixtures_and_nonidentity"] = c9

    report["failures"] = failures
    report["verdict"] = "PASS" if not failures else "FAIL"

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md.write_text(_markdown_twin(report), encoding="utf-8")
    return report


def _markdown_twin(report: dict[str, Any]) -> str:
    lines = [
        "# Mini-A5 Gate-1 completion — acceptance audit",
        "",
        f"- schema_version: `{report['schema_version']}`",
        f"- registration: `{report['registration']}`",
        f"- marker: `{report['registration_marker']}`",
        f"- generated_at_utc: {report['generated_at_utc']}",
        f"- **verdict: {report['verdict']}**",
        "",
        "## Conditions",
        "",
        "| condition | status |",
        "|---|---|",
    ]
    for name, block in sorted(report["conditions"].items()):
        if isinstance(block, dict) and "ok" in block:
            ok = bool(block["ok"])
        else:
            ok = all(
                child.get("ok", True)
                for child in block.values()
                if isinstance(child, dict)
            )
        lines.append(f"| {name} | {'ok' if ok else 'FAIL'} |")
    lines += ["", "## Arms", ""]
    for arm, block in sorted(report["arms"].items()):
        lines.append(f"- **{arm}**: run `{block['run']}`, checkpoint `{block['checkpoint']}`")
        inventory = block.get("checkpoint_inventory") or {}
        steps = [k for k in sorted(inventory) if k.startswith("global_step_")]
        n_files = sum(inventory[k]["n_files"] for k in steps)
        n_bytes = sum(inventory[k]["total_bytes"] for k in steps)
        lines.append(
            f"  - checkpoint inventory: {len(steps)} saved steps, "
            f"{n_files} files, {n_bytes} bytes (per-file sha256 in the JSON twin)")
    lines += ["", "## Failures", ""]
    if report["failures"]:
        lines += [f"- {failure}" for failure in report["failures"]]
    else:
        lines.append("(none)")
    lines += ["", "## Sealing", "", report["note"], ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--std-run", default=DEFAULT_RUNS["std"])
    parser.add_argument("--necessity-run", default=DEFAULT_RUNS["necessity"])
    parser.add_argument("--std-checkpoint", default=DEFAULT_CKPTS["std"])
    parser.add_argument("--necessity-checkpoint", default=DEFAULT_CKPTS["necessity"])
    parser.add_argument("--out-json", type=Path,
                        default=Path("reports/mini_a5_gate1_acceptance_audit_v1.json"))
    parser.add_argument("--out-md", type=Path,
                        default=Path("reports/mini_a5_gate1_acceptance_audit_v1.md"))
    parser.add_argument("--utc-override", default=None,
                        help="fixture-test hook: pin generated_at_utc for determinism")
    args = parser.parse_args()
    root = args.root.resolve()
    out_json = args.out_json if args.out_json.is_absolute() else root / args.out_json
    out_md = args.out_md if args.out_md.is_absolute() else root / args.out_md
    try:
        report = run_audit(
            root=root,
            runs={"std": args.std_run, "necessity": args.necessity_run},
            ckpts={"std": args.std_checkpoint, "necessity": args.necessity_checkpoint},
            out_json=out_json,
            out_md=out_md,
            utc_override=args.utc_override,
        )
    except Refusal as refusal:
        print(f"REFUSED (no report written): {refusal}", file=sys.stderr)
        raise SystemExit(1)
    print(f"VERDICT: {report['verdict']}")
    for name, block in sorted(report["conditions"].items()):
        if isinstance(block, dict) and "ok" in block:
            ok = bool(block["ok"])
        else:
            ok = all(c.get("ok", True) for c in block.values() if isinstance(c, dict))
        print(f"  {name:34s} {'ok' if ok else 'FAIL'}")
    for failure in report["failures"]:
        print(f"  ! {failure}")
    print(f"wrote {out_json}")
    print(f"wrote {out_md}")
    print(SEALED_NOTE)
    raise SystemExit(0 if report["verdict"] == "PASS" else 1)


if __name__ == "__main__":
    main()
