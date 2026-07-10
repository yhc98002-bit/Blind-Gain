#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any


GATE2_TASK_REPORTS: dict[str, tuple[str, ...]] = {
    "P0.1": ("reports/scorer_v2_spec.md",),
    "P0.2": ("reports/parser_agreement_audit.md",),
    "P0.3": ("reports/fliptrack_nulls.md",),
    "P0.4": ("reports/fliptrack_v01_rescored.md",),
    "P0.5": ("reports/grpo_config_diff.md",),
    "P1.1": ("reports/anchor_recipe_report.md",),
    "P1.2": ("reports/base_external_benchmarks.md", "reports/eval_harness_version.md"),
    "P1.3": ("reports/multinode_smoke.md",),
    "P1.4": ("reports/fliptrack_v02_packaging.md",),
    "P1.5": ("reports/artifact_gate_v02.md",),
    "P1.6": ("reports/fliptrack_v02_hardness.md",),
    "P1.7": ("reports/positive_controls_v02.md",),
    "P1.8": ("reports/caption_infra.md",),
    "P1.9": (
        "reports/virl39k_loader.md",
        "reports/license_log_v2.csv",
        "reports/dataset_license_triage_v2.md",
    ),
    "P1.10": ("reports/decon_geo3k_vs_layer1.md", "reports/decon_calibration.md"),
    "P1.11": ("reports/recovery_gate1.json", "reports/gate2_definition.md"),
    "P2.1": ("reports/mech_pilot_3arm_geo3k.md",),
    "P2.2": (
        "reports/blind_solvability_geo3k.md",
        "reports/blind_solvability_geo3k_v3_audited.md",
    ),
}
GATE2_TASK_IDS = tuple(GATE2_TASK_REPORTS)
LEDGER_LINE_RE = re.compile(r"^(P[0-9]+\.[0-9]+)\s*\|\s*(pass|fail|blocked)\s*\|\s*(\S.*)$")


def parse_gate2_ledger(path: Path) -> dict[str, dict[str, str]]:
    parsed: dict[str, dict[str, str]] = {}
    order: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        match = LEDGER_LINE_RE.fullmatch(line)
        if not match:
            raise ValueError(f"invalid Gate 2 ledger line {line_number}: {line!r}")
        task_id, status, note = match.groups()
        if task_id in parsed:
            raise ValueError(f"duplicate Gate 2 task ID: {task_id}")
        parsed[task_id] = {"status": status, "note": note}
        order.append(task_id)
    missing = sorted(set(GATE2_TASK_IDS) - set(parsed))
    extra = sorted(set(parsed) - set(GATE2_TASK_IDS))
    if missing or extra:
        raise ValueError(f"Gate 2 task set mismatch: missing={missing}, extra={extra}")
    if tuple(order) != GATE2_TASK_IDS:
        raise ValueError(f"Gate 2 task order mismatch: found={order}")
    return parsed


def build_gate2_objective_audit(root: Path) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    ledger: dict[str, dict[str, str]] = {}
    try:
        ledger = parse_gate2_ledger(root / "reports" / "gate2_progress.md")
    except (OSError, ValueError) as error:
        errors.append(str(error))

    report_checks: dict[str, dict[str, bool]] = {}
    if ledger:
        for task_id, entry in ledger.items():
            if entry["status"] != "pass":
                continue
            report_checks[task_id] = {
                relative: (root / relative).is_file()
                for relative in GATE2_TASK_REPORTS[task_id]
            }
            missing = [path for path, exists in report_checks[task_id].items() if not exists]
            if missing:
                errors.append(f"pass task {task_id} is missing named reports: {missing}")

    checks = {
        "ledger_has_exact_in_scope_task_set": bool(ledger),
        "ledger_has_one_valid_status_and_note_per_task": bool(ledger),
        "every_pass_task_has_all_named_reports": bool(ledger)
        and all(all(paths.values()) for paths in report_checks.values()),
    }
    return {
        "schema_version": "blind-gains.gate2-objective-audit.v1",
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "expected_task_ids": list(GATE2_TASK_IDS),
        "ledger_task_count": len(ledger),
        "ledger": ledger,
        "pass_report_checks": report_checks,
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("reports/gate2_objective_audit.json"))
    args = parser.parse_args()
    payload = build_gate2_objective_audit(args.root)
    output = args.output if args.output.is_absolute() else args.root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.partial.{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, output)
    print(json.dumps(payload, sort_keys=True))
    raise SystemExit(0 if payload["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
