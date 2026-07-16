#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from src.fliptrack.schema import sha256_file


ROOT = Path(__file__).resolve().parents[1]
REGISTRATION_DOCUMENT = Path("docs/registered_mini_a5_smoke_v1.md")
EASYR1_WORKTREE = Path("artifacts/repos/EasyR1-mini-a5")
EASYR1_REVISION = "dd71bbd252694f5f850213eec15795b6b88d9fea"
REGISTERED_ARTIFACTS = {
    "cp_config": Path("configs/train/mini_a5_cp_plumbing_smoke_v1.yaml"),
    "member_config": Path("configs/train/mini_a5_member_plumbing_smoke_v1.yaml"),
    "plumbing_data": Path("data/mini_a5_plumbing_val_v1.jsonl"),
    "pair_grouping": Path("src/train/cp_grouping.py"),
    "reward": Path("src/rewards/cp_grpo_reward.py"),
    "overlay": Path("docs/easyr1_mini_a5_pair_grouping_patch.diff"),
    "step0_audit": Path("reports/mini_a5_step0_reward_audit_v1.json"),
    "catch_audit": Path("reports/mini_a5_catch_audit_v1.json"),
    "advantage_audit": Path("reports/mini_a5_advantage_equivalence_v2.json"),
}


def _run(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.run(
        args,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def document_contains_registered_hashes(
    document: str, hashes: dict[str, str]
) -> bool:
    return all(value in document for value in hashes.values())


def _committed_bytes(commit: str, path: Path) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout


def build_marker(registration_commit: str) -> dict[str, Any]:
    head = _run("git", "rev-parse", "HEAD")
    artifacts = {name: ROOT / path for name, path in REGISTERED_ARTIFACTS.items()}
    artifact_hashes = {
        name: sha256_file(path) if path.is_file() else ""
        for name, path in artifacts.items()
    }
    document_path = ROOT / REGISTRATION_DOCUMENT
    document = document_path.read_text(encoding="utf-8") if document_path.is_file() else ""
    committed_identity: dict[str, bool] = {}
    for name, relative in {
        "registration_document": REGISTRATION_DOCUMENT,
        **REGISTERED_ARTIFACTS,
    }.items():
        path = ROOT / relative
        try:
            committed_identity[name] = path.is_file() and _committed_bytes(
                registration_commit, relative
            ) == path.read_bytes()
        except subprocess.CalledProcessError:
            committed_identity[name] = False

    advantage = (
        json.loads(artifacts["advantage_audit"].read_text(encoding="utf-8"))
        if artifacts["advantage_audit"].is_file()
        else {}
    )
    catch = (
        json.loads(artifacts["catch_audit"].read_text(encoding="utf-8"))
        if artifacts["catch_audit"].is_file()
        else {}
    )
    step0 = (
        json.loads(artifacts["step0_audit"].read_text(encoding="utf-8"))
        if artifacts["step0_audit"].is_file()
        else {}
    )
    worktree_revision = ""
    worktree_diff = b""
    if (ROOT / EASYR1_WORKTREE).exists():
        try:
            worktree_revision = _run(
                "git", "rev-parse", "HEAD", cwd=ROOT / EASYR1_WORKTREE
            )
            worktree_diff = subprocess.run(
                ["git", "diff", "--binary", "--no-ext-diff"],
                cwd=ROOT / EASYR1_WORKTREE,
                check=True,
                capture_output=True,
            ).stdout
        except subprocess.CalledProcessError:
            pass
    import hashlib

    worktree_diff_sha = hashlib.sha256(worktree_diff).hexdigest()
    checks = {
        "registration_commit_is_head": registration_commit == head,
        "registration_commit_exists": bool(
            _run("git", "cat-file", "-t", registration_commit) == "commit"
        ),
        "all_registered_artifacts_present": all(path.is_file() for path in artifacts.values()),
        "document_contains_every_registered_hash": document_contains_registered_hashes(
            document, artifact_hashes
        ),
        "document_registers_exact_commands": "bash scripts/launch_mini_a5_plumbing_smoke.sh cp <node> 0,1,2,3,4,5,6,7"
        in document
        and "bash scripts/launch_mini_a5_plumbing_smoke.sh member <node> 0,1,2,3,4,5,6,7"
        in document,
        "document_authorizes_smoke_only": "at most one optimizer step per smoke mode"
        in document
        and "It authorizes zero optimizer steps for either 120-step M6 main arm"
        in document,
        "registered_files_identical_to_commit": all(committed_identity.values()),
        "advantage_audit_passed_31_checks": advantage.get("status") == "pass"
        and len(advantage.get("checks", {})) == 31
        and all(advantage.get("checks", {}).values()),
        "step0_and_catch_audits_passed": step0.get("status") == "pass"
        and catch.get("status") == "pass",
        "isolated_easyr1_revision_exact": worktree_revision == EASYR1_REVISION,
        "isolated_easyr1_diff_nonempty": bool(worktree_diff)
        and b"BLIND_GAINS_CP_ADVANTAGE_AUDIT" in worktree_diff,
    }
    status = "registered" if all(checks.values()) else "fail"
    launcher = ROOT / "scripts/launch_mini_a5_plumbing_smoke.sh"
    return {
        "schema_version": "blind-gains.mini-a5-smoke-registration.v1",
        "status": status,
        "checks": checks,
        "registration_commit": registration_commit,
        "registration_document": str(REGISTRATION_DOCUMENT),
        "registration_document_sha256": sha256_file(document_path),
        "registered_artifact_sha256": artifact_hashes,
        "smoke_config_sha256": {
            "cp": artifact_hashes["cp_config"],
            "member": artifact_hashes["member_config"],
        },
        "plumbing_data_sha256": artifact_hashes["plumbing_data"],
        "launcher_sha256": sha256_file(launcher),
        "easyr1_revision": worktree_revision,
        "easyr1_worktree_diff_sha256": worktree_diff_sha,
        "smoke_optimizer_steps_authorized_per_mode": 1 if status == "registered" else 0,
        "main_optimizer_steps_authorized": 0,
        "scientific_gate_decision": None,
        "committed_identity": committed_identity,
    }


def render_markdown(payload: dict[str, Any], machine_path: Path) -> str:
    rows = [
        f"| `{name}` | `{'pass' if result else 'fail'}` |"
        for name, result in payload["checks"].items()
    ]
    return "\n".join(
        [
            "# Mini-A5 Smoke Registration Audit V1",
            "",
            "Status:",
            f"- Registration marker status: `{payload['status']}`.",
            "- This marker authorizes at most one CP and one member smoke step; it authorizes zero main M6 steps.",
            "- No scientific gate decision is made.",
            "",
            "Evidence:",
            f"- Machine marker: `{machine_path}`.",
            f"- Registration commit: `{payload['registration_commit']}`.",
            f"- Registration document SHA256: `{payload['registration_document_sha256']}`.",
            f"- EasyR1 worktree diff SHA256: `{payload['easyr1_worktree_diff_sha256']}`.",
            f"- Smoke config hashes: `{json.dumps(payload['smoke_config_sha256'], sort_keys=True)}`.",
            "",
            "Checks:",
            "| Check | Result |",
            "| --- | --- |",
            *rows,
            "",
            "Decision:",
            "- The launcher remains fail-closed unless this marker is committed and its registration commit is an ancestor of launch `HEAD`.",
            "- Main M6 launch remains separately blocked after smoke completion.",
            "",
        ]
    )


def _atomic_write(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite registration marker: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registration-commit", required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    payload = build_marker(args.registration_commit)
    _atomic_write(args.json_output, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    _atomic_write(args.markdown_output, render_markdown(payload, args.json_output))
    print(json.dumps({"status": payload["status"], "checks": payload["checks"]}))
    raise SystemExit(0 if payload["status"] == "registered" else 1)


if __name__ == "__main__":
    main()
