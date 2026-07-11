#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


TASK_IDS = [
    "P0.1", "P0.2", "P0.3", "P0.4", "P0.5",
    "P1.1", "P1.2", "P1.3", "P1.4", "P1.5", "P1.6", "P1.7", "P1.8", "P1.9", "P1.10", "P1.11",
    "P2.1", "P2.2",
]


def read_ledger(path: Path) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = [part.strip() for part in line.split("|", 2)]
        if len(parts) != 3:
            raise ValueError(f"invalid ledger line: {line!r}")
        task_id, status, _ = parts
        if task_id in statuses:
            raise ValueError(f"duplicate ledger task: {task_id}")
        if status not in {"pass", "fail", "blocked"}:
            raise ValueError(f"invalid ledger status for {task_id}: {status}")
        statuses[task_id] = status
    missing = set(TASK_IDS) - set(statuses)
    extra = set(statuses) - set(TASK_IDS)
    if missing or extra:
        raise ValueError(f"ledger task mismatch; missing={sorted(missing)}, extra={sorted(extra)}")
    return statuses


def _json_status(path: Path, *keys: str) -> bool:
    if not path.is_file():
        return False
    try:
        value: Any = json.loads(path.read_text(encoding="utf-8"))
        for key in keys or ("status",):
            if not isinstance(value, dict):
                return False
            value = value.get(key)
        return value is True or value == "pass"
    except (json.JSONDecodeError, OSError):
        return False


def _exact_package_ready(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        cells = payload["cells"]
        return bool(
            payload.get("status") == "automated_pass_human_audit_pending"
            and payload.get("n_pairs") == 1200
            and cells["qwen25vl3b"]["caption"]["metrics"]["n_pairs"] == 1200
            and cells["qwen25vl7b"]["caption"]["metrics"]["n_pairs"] == 1200
        )
    except (KeyError, TypeError, json.JSONDecodeError, OSError):
        return False


def compute_checks(root: Path, ledger: dict[str, str]) -> dict[str, bool]:
    reports = root / "reports"
    contact_dir = reports / "contact_sheets" / "fliptrack_v02r19"
    return {
        "measurement_system_repaired": all(ledger[task] == "pass" for task in ("P0.1", "P0.2", "P0.3", "P0.4", "P0.5")),
        "anchor_complete_with_step0_curve": ledger["P1.1"] == "pass" and (reports / "anchor_recipe_report.md").is_file(),
        "layer1_base_table_complete": ledger["P1.2"] == "pass" and (reports / "base_external_benchmarks.md").is_file(),
        "v02_packaging_linter_passes": ledger["P1.4"] == "pass"
        and _json_status(reports / "fliptrack_v02r19_lint.json"),
        "v02_artifact_gate_passes": ledger["P1.5"] == "pass"
        and _json_status(reports / "artifact_gate_v02_r19.json", "gate", "status"),
        "v02_templates_and_contact_sheets": ledger["P1.6"] == "pass" and contact_dir.is_dir() and len(list(contact_dir.glob("*.png"))) >= 3,
        "v02_positive_controls": ledger["P1.7"] == "pass" and (reports / "positive_controls_v02.md").is_file(),
        "v02_exact_caption_stores": ledger["P1.8"] == "pass"
        and _exact_package_ready(reports / "fliptrack_v02r19_exact_package.json"),
        "three_arm_mechanical_pilot": ledger["P2.1"] == "pass" and (reports / "mech_pilot_3arm_geo3k.md").is_file(),
        "geometry3k_blind_solvability": ledger["P2.2"] == "pass"
        and (reports / "blind_solvability_geo3k_v3_audited.md").is_file(),
        "datasets_and_required_licenses": ledger["P1.9"] == "pass" and (reports / "license_log_v2.csv").is_file(),
        "decontamination_calibrated": ledger["P1.10"] == "pass" and (reports / "decon_geo3k_vs_layer1.md").is_file(),
        "repository_and_gate_logic_clean": ledger["P1.11"] == "pass" and (root / "tests" / "test_gate_logic.py").is_file(),
    }


def machine_ready(checks: dict[str, bool]) -> bool:
    return bool(checks) and all(checks.values())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--ledger", default="reports/gate2_progress.md")
    parser.add_argument("--output", default="reports/gate2_machine_check_v2.json")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    ledger = read_ledger(root / args.ledger)
    checks = compute_checks(root, ledger)
    output_path = root / args.output
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite Gate-2 machine check: {output_path}")
    output: dict[str, Any] = {
        "machine_checks": checks,
        "machine_ready_for_pi_audit": machine_ready(checks),
        "unsatisfied_checks": [name for name, satisfied in checks.items() if not satisfied],
        "gpu_hours_utilization_reported": (root / "reports" / "gpu_hours_utilization.md").is_file(),
        "pi_gate_decision": "not_evaluated",
        "note": "This script checks artifacts only; GPU utilization is reported but is not a gate; it does not declare Gate 2 passed.",
    }
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
