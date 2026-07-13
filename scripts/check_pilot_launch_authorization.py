#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from scripts.audit_prelaunch_objective import EXPECTED_TASK_IDS, parse_prelaunch_ledger
from scripts.build_preregistration_pilot_draft import (
    ARM_CONDITIONS,
    ARM_CONFIGS,
    CHART_CONSTRUCT,
    PRIOR_OBSERVATION_DISCLOSURE,
    R20_CAVEAT,
    audit_arm_configs,
)


ARM_KEYS = {
    "a1_real": "A1 real",
    "a2_gray": "A2 gray",
    "a2b_noimage": "A2b no-image",
    "a3_caption": "A3 caption",
}
CHECKPOINT_NAMES = {
    "a1_real": "mech_a1_real",
    "a2_gray": "mech_a2_gray",
    "a2b_noimage": "mech_a2b_noimage",
    "a3_caption": "mech_a3_caption",
}
MAIN_TASK_IDS = tuple(f"M{index}" for index in range(15))
REGISTRATION_MARKERS = (
    "- R19 human contact-sheet audit: approved.",
    "- Registration state: merged-at-HEAD; merge is sign-off.",
    "- no pilot optimizer step has run",
    PRIOR_OBSERVATION_DISCLOSURE,
    R20_CAVEAT,
    CHART_CONSTRUCT,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_main_ledger(path: Path) -> dict[str, dict[str, str]]:
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line]
    if len(lines) != len(MAIN_TASK_IDS):
        raise ValueError("main ledger must contain exactly one line for M0 through M14")
    ledger: dict[str, dict[str, str]] = {}
    for line in lines:
        parts = line.split(" | ", maxsplit=2)
        if len(parts) != 3 or parts[1] not in {"pass", "fail", "blocked"} or not parts[2]:
            raise ValueError(f"invalid main ledger line: {line}")
        task, status, note = parts
        if task in ledger:
            raise ValueError(f"duplicate main ledger task: {task}")
        ledger[task] = {"status": status, "note": note}
    if tuple(ledger) != MAIN_TASK_IDS:
        raise ValueError("main ledger task order must be exactly M0 through M14")
    return ledger


def build_authorization(
    root: Path,
    arm: str,
    *,
    checkpoint_path: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    if arm not in ARM_KEYS:
        raise ValueError(f"unknown pilot arm: {arm}")
    errors: list[str] = []
    try:
        prelaunch_ledger = parse_prelaunch_ledger(
            root / "reports" / "prelaunch_progress.md", EXPECTED_TASK_IDS
        )
    except (OSError, ValueError) as error:
        prelaunch_ledger = {}
        errors.append(str(error))
    try:
        main_ledger = parse_main_ledger(root / "reports" / "main_progress.md")
    except (OSError, ValueError) as error:
        main_ledger = {}
        errors.append(str(error))

    prereg_path = root / "reports" / "preregistration_pilot_v1.md"
    prereg_text = prereg_path.read_text(encoding="utf-8") if prereg_path.is_file() else ""
    l3_audit_path = root / "reports" / "pilot_reward_smoke_audit_v4.json"
    try:
        l3_audit = json.loads(l3_audit_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        l3_audit = {}
    reward_spec_path = root / "reports" / "pilot_reward_spec_v3.md"
    filtered_ids = root / "data" / "geo3k_pilot_filtered_ids.json"
    try:
        config_audit = audit_arm_configs(root)
    except (OSError, KeyError, TypeError, ValueError) as error:
        config_audit = {"hashes": {}}
        errors.append(str(error))

    arm_label = ARM_KEYS[arm]
    config_relative = ARM_CONFIGS[arm_label]
    config_path = root / config_relative
    checkpoint_root = (root / "checkpoints" / "pilot").resolve()
    canonical_checkpoint_name = CHECKPOINT_NAMES[arm]
    selected_checkpoint_path = (
        checkpoint_root / canonical_checkpoint_name
        if checkpoint_path is None
        else checkpoint_path.resolve()
    )
    checkpoint_path_valid = (
        selected_checkpoint_path.parent == checkpoint_root
        and re.fullmatch(
            rf"{re.escape(canonical_checkpoint_name)}(?:_retry[1-9][0-9]*)?",
            selected_checkpoint_path.name,
        )
        is not None
    )
    config_hash = config_audit.get("hashes", {}).get(arm_label)
    filtered_hash = _sha256(filtered_ids) if filtered_ids.is_file() else None
    historical_dependencies = ("L3", "L4", "L5")
    checks = {
        "prelaunch_ledger_parses_exact_L0_through_L13": bool(prelaunch_ledger),
        "historical_dependencies_pass": bool(prelaunch_ledger)
        and all(
            prelaunch_ledger[task]["status"] == "pass"
            for task in historical_dependencies
        ),
        "main_ledger_parses_exact_M0_through_M14": bool(main_ledger),
        "M0_registration_pass": bool(main_ledger)
        and main_ledger["M0"]["status"] == "pass",
        "M2_not_predeclared": bool(main_ledger)
        and main_ledger["M2"]["status"] == "blocked",
        "final_preregistration_exists": prereg_path.is_file()
        and prereg_path.stat().st_size > 0,
        "merge_signoff_and_registration_content_exact": all(
            marker in prereg_text for marker in REGISTRATION_MARKERS
        ),
        "registration_placeholder_absent": "PENDING_RICHARD_MERGE" not in prereg_text,
        "l3_v6_audit_pass": l3_audit.get("schema_version")
        == "blind-gains.pilot-reward-smoke-audit.v6"
        and l3_audit.get("status") == "pass"
        and l3_audit.get("placement_audit", {}).get("status") == "pass"
        and all(l3_audit.get("placement_audit", {}).get("checks", {}).values()),
        "reward_spec_v3_exists": reward_spec_path.is_file()
        and reward_spec_path.stat().st_size > 0,
        "all_arm_configs_match_registered_structure": len(
            config_audit.get("hashes", {})
        )
        == 4,
        "selected_config_hash_pinned_in_preregistration": isinstance(config_hash, str)
        and config_hash in prereg_text,
        "filtered_ids_hash_pinned_in_preregistration": isinstance(filtered_hash, str)
        and filtered_hash in prereg_text,
        "selected_checkpoint_path_valid": checkpoint_path_valid,
        "selected_checkpoint_namespace_absent": checkpoint_path_valid
        and not selected_checkpoint_path.exists(),
    }
    failed = [name for name, passed in checks.items() if not passed]
    errors.extend(failed)
    return {
        "schema_version": "blind-gains.pilot-launch-authorization.v2",
        "status": "authorized" if all(checks.values()) and not errors else "blocked",
        "arm": arm,
        "arm_label": arm_label,
        "image_condition": ARM_CONDITIONS[arm_label],
        "checks": checks,
        "ledger_dependencies": {
            **{
                task: prelaunch_ledger.get(task)
                for task in historical_dependencies
            },
            "M0": main_ledger.get("M0"),
            "M2": main_ledger.get("M2"),
        },
        "preregistration": str(prereg_path),
        "preregistration_sha256": _sha256(prereg_path)
        if prereg_path.is_file()
        else None,
        "l3_audit": str(l3_audit_path),
        "l3_audit_sha256": _sha256(l3_audit_path)
        if l3_audit_path.is_file()
        else None,
        "reward_spec": str(reward_spec_path),
        "config": str(config_path),
        "config_sha256": config_hash,
        "filtered_ids": str(filtered_ids),
        "filtered_ids_sha256": filtered_hash,
        "checkpoint_path": str(selected_checkpoint_path),
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--arm", choices=tuple(ARM_KEYS), required=True)
    parser.add_argument("--checkpoint-path", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite pilot authorization: {args.output}")
    payload = build_authorization(
        args.root,
        args.arm,
        checkpoint_path=args.checkpoint_path,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(f".{args.output.name}.partial.{os.getpid()}")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, args.output)
    print(json.dumps(payload, sort_keys=True))
    raise SystemExit(0 if payload["status"] == "authorized" else 1)


if __name__ == "__main__":
    main()
