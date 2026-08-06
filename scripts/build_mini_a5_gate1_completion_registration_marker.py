#!/usr/bin/env python3
"""Build the immutable Mini-A5 Gate-1 COMPLETION registration marker (T6).

Follows the scripts/build_mini_a5_main_registration_marker.py pattern for
docs/registered_mini_a5_gate1_completion_v1.md: binds the registration
document's commit as an ancestor of HEAD, verifies every registered input is
committed byte-identical to the worktree at HEAD, verifies the T1/T4/T7
corpus and input audits passed, machine-checks the matched-difference
discipline (acceptance condition 8) for both completion configs, and writes
reports/mini_a5_gate1_completion_registration_marker_v1.json authorizing 120
optimizer steps per completion arm (std, necessity) plus one smoke step per
mode. scripts/launch_mini_a5_main.sh and the Gate-1 smoke/step-0 launchers
verify their inputs against this marker's per-mode hashes at launch.

Adversarial fixture (I10): tests/test_build_mini_a5_gate1_marker_fixture.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from scripts.check_mini_a5_matched_diff import check as matched_diff_check
from src.fliptrack.schema import sha256_file

ROOT = Path(__file__).resolve().parents[1]
REGISTRATION_DOCUMENT = Path("docs/registered_mini_a5_gate1_completion_v1.md")
MARKER_OUTPUT = Path("reports/mini_a5_gate1_completion_registration_marker_v1.json")
LAUNCHER = Path("scripts/launch_mini_a5_main.sh")
SMOKE_LAUNCHER = Path("scripts/launch_mini_a5_gate1_plumbing_smoke.sh")
STEP0_LAUNCHER = Path("scripts/launch_mini_a5_gate1_step0.sh")
MEMBER_TEMPLATE = Path("configs/train/mini_a5_same_data_3b_v1.yaml")
EASYR1_WORKTREE = Path("artifacts/repos/EasyR1-mini-a5")
EASYR1_REVISION = "dd71bbd252694f5f850213eec15795b6b88d9fea"
MAIN_STEPS_PER_ARM = 120
ARMS = ("std", "necessity")
REGISTERED_ARTIFACTS = {
    "std_config": Path("configs/train/mini_a5_std_3b_v1.yaml"),
    "necessity_config": Path("configs/train/mini_a5_necessity_3b_v1.yaml"),
    "member_config": MEMBER_TEMPLATE,
    "cp_config": Path("configs/train/mini_a5_cp_3b_v1.yaml"),
    "std_corpus": Path("data/mini_a5_std_train_v1/train.parquet"),
    "necessity_corpus": Path("data/mini_a5_necessity_train_v1/train.parquet"),
    "necessity_delta_q": Path("data/mini_a5_necessity_metadata_v1/delta_q.jsonl"),
    "necessity_source_map": Path("data/mini_a5_necessity_train_v1/source_map.jsonl"),
    "blind_solvability_manifest": Path(
        "data/mini_a5_train_blind_solvability_manifest_v1.jsonl"
    ),
    "monitoring_val": Path("data/mini_a5_plumbing_val_v1.jsonl"),
    "fixed_subsets_manifest": Path("data/mini_a5_fixed_subsets_v1_manifest.json"),
    "pair_grouping": Path("src/train/cp_grouping.py"),
    "reward": Path("src/rewards/cp_grpo_reward.py"),
    "overlay": Path("docs/easyr1_mini_a5_pair_grouping_patch.diff"),
    "std_build_report": Path("reports/mini_a5_std_corpus_build_v1.json"),
    "manifest_build_report": Path(
        "reports/mini_a5_blind_solvability_manifest_build_v1.json"
    ),
    "necessity_build_report": Path("reports/mini_a5_necessity_corpus_build_v1.json"),
    "smoke_inputs_report": Path("reports/mini_a5_gate1_smoke_inputs_build_v1.json"),
    "smoke_std_config": Path("configs/train/mini_a5_std_plumbing_smoke_v1.yaml"),
    "smoke_necessity_config": Path(
        "configs/train/mini_a5_necessity_plumbing_smoke_v1.yaml"
    ),
    "smoke_std_data": Path("data/mini_a5_std_plumbing_train_v1.jsonl"),
    "smoke_necessity_data": Path("data/mini_a5_necessity_plumbing_train_v1.jsonl"),
    "step0_std_sample": Path("data/mini_a5_std_step0_sample_v1.jsonl"),
    "step0_necessity_sample": Path("data/mini_a5_necessity_step0_sample_v1.jsonl"),
    "matched_diff_checker": Path("scripts/check_mini_a5_matched_diff.py"),
}
# Hashes that must appear verbatim inside the registration document (its
# section 5 table); artifacts born after filing are pinned by this marker.
DOC_BOUND_ARTIFACTS = (
    "std_config",
    "necessity_config",
    "member_config",
    "cp_config",
    "monitoring_val",
    "pair_grouping",
    "reward",
    "overlay",
)


def _run(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.run(
        args, cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


def _committed_bytes(commit: str, path: Path) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"], cwd=ROOT, check=True, capture_output=True
    ).stdout


def document_contains_registered_hashes(
    document_text: str, hashes: dict[str, str]
) -> bool:
    return all(value in document_text for value in hashes.values())


def _is_ancestor(commit: str, head: str) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, head],
        cwd=ROOT,
        capture_output=True,
    )
    return result.returncode == 0


def build_marker(registration_commit: str) -> dict[str, Any]:
    head = _run("git", "rev-parse", "HEAD")
    artifact_hashes = {
        name: sha256_file(ROOT / path) for name, path in REGISTERED_ARTIFACTS.items()
    }
    document_text = (ROOT / REGISTRATION_DOCUMENT).read_text(encoding="utf-8")
    committed_identity = {
        name: _committed_bytes(head, path) == (ROOT / path).read_bytes()
        for name, path in REGISTERED_ARTIFACTS.items()
    }
    committed_identity["registration_document"] = _committed_bytes(
        registration_commit, REGISTRATION_DOCUMENT
    ) == (ROOT / REGISTRATION_DOCUMENT).read_bytes()
    committed_identity["launcher"] = _committed_bytes(head, LAUNCHER) == (
        ROOT / LAUNCHER
    ).read_bytes()
    committed_identity["smoke_launcher"] = _committed_bytes(head, SMOKE_LAUNCHER) == (
        ROOT / SMOKE_LAUNCHER
    ).read_bytes()
    committed_identity["step0_launcher"] = _committed_bytes(head, STEP0_LAUNCHER) == (
        ROOT / STEP0_LAUNCHER
    ).read_bytes()

    std_report = json.loads(
        (ROOT / REGISTERED_ARTIFACTS["std_build_report"]).read_text(encoding="utf-8")
    )
    necessity_report = json.loads(
        (ROOT / REGISTERED_ARTIFACTS["necessity_build_report"]).read_text(
            encoding="utf-8"
        )
    )
    smoke_inputs_report = json.loads(
        (ROOT / REGISTERED_ARTIFACTS["smoke_inputs_report"]).read_text(encoding="utf-8")
    )
    easyr1_diff = subprocess.run(
        ["git", "diff", "--binary", "--no-ext-diff"],
        cwd=ROOT / EASYR1_WORKTREE,
        check=True,
        capture_output=True,
    ).stdout

    doc_bound = {name: artifact_hashes[name] for name in DOC_BOUND_ARTIFACTS}
    checks = {
        "registration_commit_exists": bool(
            _run("git", "cat-file", "-t", registration_commit) == "commit"
        ),
        "registration_commit_is_ancestor_of_head": _is_ancestor(
            registration_commit, head
        ),
        "all_registered_artifacts_present": all(
            (ROOT / path).is_file() for path in REGISTERED_ARTIFACTS.values()
        ),
        "registered_files_identical_to_commit": all(committed_identity.values()),
        "document_contains_registered_config_hashes": document_contains_registered_hashes(
            document_text, doc_bound
        ),
        "document_authorizes_120_step_arms": "120-step arms" in document_text
        and "120 steps" in document_text,
        "document_registers_exact_commands": "launch_mini_a5_main.sh std" in document_text
        and "launch_mini_a5_main.sh necessity" in document_text,
        "document_records_pi_ratification": "## Ratification" in document_text
        and "ratified by the PI on 2026-08-06" in document_text,
        "std_projection_audit_passed": std_report.get("projection_audit", {})
        .get("checks", {})
        .get("status_pass")
        is True,
        "necessity_resample_audit_passed": necessity_report.get("resample_audit", {})
        .get("checks", {})
        .get("status_pass")
        is True,
        "necessity_draw_frequency_audit_passed": necessity_report.get(
            "resample_audit", {}
        )
        .get("checks", {})
        .get("empirical_draw_frequency_consistent")
        is True,
        "smoke_inputs_audit_passed": all(
            smoke_inputs_report.get("arms", {})
            .get(arm, {})
            .get("audit", {})
            .get("checks", {})
            .get("status_pass")
            is True
            for arm in ARMS
        ),
        "matched_difference_audit_passed": not matched_diff_check(
            ROOT / REGISTERED_ARTIFACTS["std_config"], ROOT / MEMBER_TEMPLATE
        )
        and not matched_diff_check(
            ROOT / REGISTERED_ARTIFACTS["necessity_config"], ROOT / MEMBER_TEMPLATE
        ),
        "smoke_matched_difference_audit_passed": not matched_diff_check(
            ROOT / REGISTERED_ARTIFACTS["smoke_std_config"],
            ROOT / Path("configs/train/mini_a5_member_plumbing_smoke_v1.yaml"),
        )
        and not matched_diff_check(
            ROOT / REGISTERED_ARTIFACTS["smoke_necessity_config"],
            ROOT / Path("configs/train/mini_a5_member_plumbing_smoke_v1.yaml"),
        ),
        "isolated_easyr1_revision_exact": _run(
            "git", "rev-parse", "HEAD", cwd=ROOT / EASYR1_WORKTREE
        )
        == EASYR1_REVISION,
        "isolated_easyr1_diff_nonempty": len(easyr1_diff) > 0,
        "launchers_present": (ROOT / LAUNCHER).is_file()
        and (ROOT / SMOKE_LAUNCHER).is_file()
        and (ROOT / STEP0_LAUNCHER).is_file(),
    }
    all_pass = all(checks.values())
    marker = {
        "schema_version": "blind-gains.mini-a5-gate1-completion-registration-marker.v1",
        "status": "registered" if all_pass else "failed",
        "registration_document": str(REGISTRATION_DOCUMENT),
        "registration_document_sha256": sha256_file(ROOT / REGISTRATION_DOCUMENT),
        "registration_commit": registration_commit,
        "head_at_marker_build": head,
        "main_config_sha256": {
            "std": artifact_hashes["std_config"],
            "necessity": artifact_hashes["necessity_config"],
        },
        "train_corpus_sha256": {
            "std": artifact_hashes["std_corpus"],
            "necessity": artifact_hashes["necessity_corpus"],
        },
        "smoke_config_sha256": {
            "std": artifact_hashes["smoke_std_config"],
            "necessity": artifact_hashes["smoke_necessity_config"],
        },
        "smoke_data_sha256": {
            "std": artifact_hashes["smoke_std_data"],
            "necessity": artifact_hashes["smoke_necessity_data"],
        },
        "step0_sample_sha256": {
            "std": artifact_hashes["step0_std_sample"],
            "necessity": artifact_hashes["step0_necessity_sample"],
        },
        "artifact_sha256": artifact_hashes,
        "committed_identity": committed_identity,
        "checks": checks,
        "easyr1_revision": EASYR1_REVISION,
        "easyr1_worktree_diff_sha256": hashlib.sha256(easyr1_diff).hexdigest(),
        "launcher_sha256": sha256_file(ROOT / LAUNCHER),
        "smoke_launcher_sha256": sha256_file(ROOT / SMOKE_LAUNCHER),
        "step0_launcher_sha256": sha256_file(ROOT / STEP0_LAUNCHER),
        "main_optimizer_steps_authorized_per_arm": MAIN_STEPS_PER_ARM if all_pass else 0,
        "smoke_optimizer_steps_authorized_per_mode": 1 if all_pass else 0,
        "arms_authorized": list(ARMS) if all_pass else [],
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
