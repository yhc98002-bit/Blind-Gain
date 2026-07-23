#!/usr/bin/env python3
"""Build the immutable Mini-A5 MAIN-run registration marker.

Binds docs/registered_mini_a5_main_v1.md at the current HEAD, verifies every
registered input is committed byte-identical to the worktree, verifies the
completed smoke audit passed with zero main steps authorized by it, and writes
reports/mini_a5_main_registration_marker_v1.json authorizing 120 optimizer
steps per main arm.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from src.fliptrack.schema import sha256_file

ROOT = Path(__file__).resolve().parents[1]
REGISTRATION_DOCUMENT = Path("docs/registered_mini_a5_main_v1.md")
MARKER_OUTPUT = Path("reports/mini_a5_main_registration_marker_v1.json")
LAUNCHER = Path("scripts/launch_mini_a5_main.sh")
EASYR1_WORKTREE = Path("artifacts/repos/EasyR1-mini-a5")
EASYR1_REVISION = "dd71bbd252694f5f850213eec15795b6b88d9fea"
MAIN_STEPS_PER_ARM = 120
REGISTERED_ARTIFACTS = {
    "cp_config": Path("configs/train/mini_a5_cp_3b_v1.yaml"),
    "member_config": Path("configs/train/mini_a5_same_data_3b_v1.yaml"),
    "train_corpus": Path("data/mini_a5_train_v1/train.parquet"),
    "fixed_subsets_manifest": Path("data/mini_a5_fixed_subsets_v1_manifest.json"),
    "monitoring_val": Path("data/mini_a5_plumbing_val_v1.jsonl"),
    "pair_grouping": Path("src/train/cp_grouping.py"),
    "reward": Path("src/rewards/cp_grpo_reward.py"),
    "overlay": Path("docs/easyr1_mini_a5_pair_grouping_patch.diff"),
    "step0_audit": Path("reports/mini_a5_step0_reward_audit_v1.json"),
    "catch_audit": Path("reports/mini_a5_catch_audit_v1.json"),
    "advantage_audit": Path("reports/mini_a5_advantage_equivalence_v2.json"),
    "smoke_audit": Path("reports/mini_a5_plumbing_smoke_audit_v1.json"),
}


def _run(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def _committed_bytes(commit: str, path: Path) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"], cwd=ROOT, check=True, capture_output=True
    ).stdout


def build_marker(registration_commit: str) -> dict[str, Any]:
    head = _run("git", "rev-parse", "HEAD")
    artifact_hashes = {
        name: sha256_file(ROOT / path) for name, path in REGISTERED_ARTIFACTS.items()
    }
    document_text = (ROOT / REGISTRATION_DOCUMENT).read_text(encoding="utf-8")
    committed_identity = {
        name: _committed_bytes(registration_commit, path)
        == (ROOT / path).read_bytes()
        for name, path in REGISTERED_ARTIFACTS.items()
    }
    committed_identity["registration_document"] = _committed_bytes(
        registration_commit, REGISTRATION_DOCUMENT
    ) == (ROOT / REGISTRATION_DOCUMENT).read_bytes()

    smoke_audit = json.loads((ROOT / REGISTERED_ARTIFACTS["smoke_audit"]).read_text())
    easyr1_diff = subprocess.run(
        ["git", "diff", "--binary", "--no-ext-diff"],
        cwd=ROOT / EASYR1_WORKTREE,
        check=True,
        capture_output=True,
    ).stdout
    import hashlib

    checks = {
        "registration_commit_exists": bool(
            _run("git", "cat-file", "-t", registration_commit) == "commit"
        ),
        "registration_commit_is_head": registration_commit == head,
        "all_registered_artifacts_present": all(
            (ROOT / path).is_file() for path in REGISTERED_ARTIFACTS.values()
        ),
        "registered_files_identical_to_commit": all(committed_identity.values()),
        "document_contains_every_registered_hash": all(
            value in document_text for value in artifact_hashes.values()
        ),
        "document_authorizes_120_steps_per_arm": "120-step" in document_text
        and "max_steps=120" in document_text,
        "document_registers_exact_commands": "launch_mini_a5_main.sh cp" in document_text
        and "launch_mini_a5_main.sh member" in document_text,
        "smoke_audit_passed": smoke_audit.get("status") == "pass",
        "smoke_audit_authorized_zero_main_steps": smoke_audit.get(
            "main_optimizer_steps_authorized_by_this_audit", None
        )
        == 0,
        "isolated_easyr1_revision_exact": _run(
            "git", "rev-parse", "HEAD", cwd=ROOT / EASYR1_WORKTREE
        )
        == EASYR1_REVISION,
        "isolated_easyr1_diff_nonempty": len(easyr1_diff) > 0,
        "launcher_present": (ROOT / LAUNCHER).is_file(),
    }
    marker = {
        "schema_version": "blind-gains.mini-a5-main-registration-marker.v1",
        "status": "registered" if all(checks.values()) else "failed",
        "registration_document": str(REGISTRATION_DOCUMENT),
        "registration_document_sha256": sha256_file(ROOT / REGISTRATION_DOCUMENT),
        "registration_commit": registration_commit,
        "head_at_marker_build": head,
        "main_config_sha256": {
            "cp": artifact_hashes["cp_config"],
            "member": artifact_hashes["member_config"],
        },
        "train_corpus_sha256": artifact_hashes["train_corpus"],
        "artifact_sha256": artifact_hashes,
        "committed_identity": committed_identity,
        "checks": checks,
        "easyr1_revision": EASYR1_REVISION,
        "easyr1_worktree_diff_sha256": hashlib.sha256(easyr1_diff).hexdigest(),
        "launcher_sha256": sha256_file(ROOT / LAUNCHER),
        "main_optimizer_steps_authorized_per_arm": MAIN_STEPS_PER_ARM
        if all(checks.values())
        else 0,
        "arms_authorized": ["cp", "member"] if all(checks.values()) else [],
        "scientific_gate_decision": None,
    }
    return marker


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registration-commit", required=True)
    parser.add_argument("--output", type=Path, default=MARKER_OUTPUT)
    args = parser.parse_args()
    if (ROOT / args.output).exists():
        raise FileExistsError(f"refusing to overwrite marker: {args.output}")
    marker = build_marker(args.registration_commit)
    (ROOT / args.output).write_text(
        json.dumps(marker, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": marker["status"], "checks": marker["checks"]}, sort_keys=True))
    if marker["status"] != "registered":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
