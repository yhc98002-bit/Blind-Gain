#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from typing import Any

from src.train.m5_resume_integrity import (
    continuity_checks,
    raw_hash_continuity,
    read_training_metrics,
    sha256,
    validate_config_derivation,
)


def _read(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _atomic_write(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def render(payload: dict[str, Any], json_output: Path) -> str:
    checks = payload["checks"]
    failed = [name for name, value in checks.items() if not value]
    return "\n".join(
        [
            "# M5 Restore-and-Resume Integrity",
            "",
            "Status:",
            f"- Integrity precondition: `{payload['status']}`.",
            "- This is an engineering precondition and does not declare M5 or a PI gate passed.",
            "",
            "Evidence:",
            f"- Machine artifact: `{json_output}`.",
            f"- Source raw checkpoint: `{payload['source_checkpoint']}`.",
            f"- Step-101 run: `{payload['integrity_run_manifest']}`.",
            f"- Checks: `{len(checks) - len(failed)}/{len(checks)}` true.",
            "- Continuity bounds were committed before the step-101 run and are recorded in the machine artifact.",
            "",
            "Problems:",
            f"- Failed checks: `{failed}`.",
            "",
            "Decision:",
            "- None. A passing integrity artifact authorizes the already registered fixed step-400 launch; it does not interpret scientific outcomes.",
            "",
            "Next actions:",
            "- Launch the step-400 continuation from the original verified step-100 state, not from the integrity checkpoint.",
            "- Preserve the fixed terminal step and registered evaluation checkpoints.",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-config", type=Path, required=True)
    parser.add_argument("--integrity-config", type=Path, required=True)
    parser.add_argument("--longhorizon-config", type=Path, required=True)
    parser.add_argument("--relocation-marker", type=Path, required=True)
    parser.add_argument("--restored-checkpoint-audit", type=Path, required=True)
    parser.add_argument("--integrity-run-manifest", type=Path, required=True)
    parser.add_argument("--source-metrics", type=Path, required=True)
    parser.add_argument("--integrity-metrics", type=Path, required=True)
    parser.add_argument("--step101-checkpoint-audit", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()

    integrity_config = validate_config_derivation(
        args.base_config, args.integrity_config, mode="integrity"
    )
    longhorizon_config = validate_config_derivation(
        args.base_config, args.longhorizon_config, mode="longhorizon"
    )
    relocation = _read(args.relocation_marker)
    restored = _read(args.restored_checkpoint_audit)
    hashes = raw_hash_continuity(relocation, restored)
    run_manifest = _read(args.integrity_run_manifest)
    step101_audit = _read(args.step101_checkpoint_audit)
    continuity = continuity_checks(
        read_training_metrics(args.source_metrics),
        read_training_metrics(args.integrity_metrics),
    )
    manifest_checks = {
        "integrity_run_complete": run_manifest.get("status") == "complete"
        and run_manifest.get("exit_code") == 0
        and run_manifest.get("artifacts_exist") is True,
        "integrity_run_identity": run_manifest.get("job_type")
        == "m5_anchor_resume_integrity_step101"
        and run_manifest.get("resumed_from_global_step") == 100
        and run_manifest.get("target_global_step") == 101,
        "integrity_config_hash_bound": run_manifest.get("config_hash")
        == sha256(args.integrity_config),
        "step101_checkpoint_audit_pass": step101_audit.get("status") == "pass"
        and step101_audit.get("expected_step") == 101
        and step101_audit.get("files_stable_during_hash") is True,
    }
    checks = {
        "integrity_config_exact_registered_diff": integrity_config["status"] == "pass",
        "longhorizon_config_exact_registered_diff": longhorizon_config["status"]
        == "pass",
        "raw_hash_continuity": hashes["status"] == "pass",
        "loss_and_step_continuity": continuity["status"] == "pass",
        **manifest_checks,
    }
    payload = {
        "schema_version": "blind-gains.m5-restore-resume-integrity.v1",
        "status": "pass" if all(checks.values()) else "fail",
        "scientific_gate_decision": None,
        "created_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "checks": checks,
        "integrity_config_audit": integrity_config,
        "longhorizon_config_audit": longhorizon_config,
        "raw_hash_continuity": hashes,
        "continuity": continuity,
        "source_checkpoint": str(args.relocation_marker.parent.parent),
        "integrity_run_manifest": str(args.integrity_run_manifest),
        "provenance": {
            str(path): sha256(path)
            for path in (
                args.relocation_marker,
                args.restored_checkpoint_audit,
                args.integrity_run_manifest,
                args.source_metrics,
                args.integrity_metrics,
                args.step101_checkpoint_audit,
            )
        },
    }
    _atomic_write(args.json_output, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    _atomic_write(args.markdown_output, render(payload, args.json_output))
    print(json.dumps({"status": payload["status"], "checks": checks}, sort_keys=True))
    raise SystemExit(0 if payload["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
