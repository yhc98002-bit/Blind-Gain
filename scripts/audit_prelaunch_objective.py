#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any


EXPECTED_TASK_IDS = tuple(f"L{index}" for index in range(14))
TASK_LINE_RE = re.compile(r"^- `(L[0-9]+)` reports: (.+)$")
REPORT_TOKEN_RE = re.compile(r"`(reports/[^`]+)`")
LEDGER_LINE_RE = re.compile(r"^(L(?:[0-9]|1[0-3])) \| (pass|fail|blocked) \| (\S.*)$")
VERSIONED_AUDITED_RE = re.compile(r"_v[0-9]+_audited(?=\.)")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_task_registry(path: Path) -> dict[str, tuple[str, ...]]:
    registry: dict[str, tuple[str, ...]] = {}
    order: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = TASK_LINE_RE.fullmatch(line)
        if not match:
            continue
        task_id, report_text = match.groups()
        if task_id in registry:
            raise ValueError(f"duplicate prelaunch task ID in registry: {task_id}")
        reports = tuple(REPORT_TOKEN_RE.findall(report_text))
        if not reports:
            raise ValueError(f"prelaunch task has no named reports: {task_id}")
        if len(reports) != len(set(reports)):
            raise ValueError(f"prelaunch task repeats a named report: {task_id}")
        for relative in reports:
            candidate = Path(relative)
            if candidate.is_absolute() or ".." in candidate.parts or candidate.parts[0] != "reports":
                raise ValueError(f"unsafe named report for {task_id}: {relative}")
        registry[task_id] = reports
        order.append(task_id)
    missing = sorted(set(EXPECTED_TASK_IDS) - set(registry))
    extra = sorted(set(registry) - set(EXPECTED_TASK_IDS))
    if missing or extra:
        raise ValueError(f"prelaunch registry task set mismatch: missing={missing}, extra={extra}")
    if tuple(order) != EXPECTED_TASK_IDS:
        raise ValueError(f"prelaunch registry task order mismatch: found={order}")
    return registry


def parse_prelaunch_ledger(path: Path, expected_ids: tuple[str, ...]) -> dict[str, dict[str, str]]:
    parsed: dict[str, dict[str, str]] = {}
    order: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        match = LEDGER_LINE_RE.fullmatch(line)
        if not match:
            raise ValueError(f"invalid prelaunch ledger line {line_number}: {line!r}")
        task_id, status, note = match.groups()
        if task_id in parsed:
            raise ValueError(f"duplicate prelaunch task ID in ledger: {task_id}")
        parsed[task_id] = {"status": status, "note": note}
        order.append(task_id)
    missing = sorted(set(expected_ids) - set(parsed))
    extra = sorted(set(parsed) - set(expected_ids))
    if missing or extra:
        raise ValueError(f"prelaunch ledger task set mismatch: missing={missing}, extra={extra}")
    if tuple(order) != expected_ids:
        raise ValueError(f"prelaunch ledger task order mismatch: found={order}")
    return parsed


def resolve_unaudited_counterpart(audited: Path) -> Path | None:
    direct = audited.with_name(audited.name.replace("_audited", "", 1))
    if direct.is_file():
        return direct
    fallback_name = VERSIONED_AUDITED_RE.sub("", audited.name, count=1)
    fallback = audited.with_name(fallback_name)
    return fallback if fallback.is_file() else None


def audited_file_checks(reports_dir: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    checks: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for audited in sorted(
        path for path in reports_dir.rglob("*") if path.is_file() and "_audited" in path.name
    ):
        counterpart = resolve_unaudited_counterpart(audited)
        record: dict[str, Any] = {
            "audited": str(audited),
            "audited_size_bytes": audited.stat().st_size,
            "audited_sha256": _sha256(audited),
            "counterpart": str(counterpart) if counterpart else None,
            "byte_identical": None,
        }
        if counterpart is not None:
            record.update(
                {
                    "counterpart_size_bytes": counterpart.stat().st_size,
                    "counterpart_sha256": _sha256(counterpart),
                    "byte_identical": audited.read_bytes() == counterpart.read_bytes(),
                }
            )
            if record["byte_identical"]:
                errors.append(f"audited report is byte-identical to counterpart: {audited} == {counterpart}")
        checks[str(audited.relative_to(reports_dir.parent))] = record
    return checks, errors


def build_prelaunch_objective_audit(root: Path) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    registry: dict[str, tuple[str, ...]] = {}
    ledger: dict[str, dict[str, str]] = {}
    try:
        registry = parse_task_registry(root / "PRELAUNCH_TASKS.md")
    except (OSError, ValueError) as error:
        errors.append(str(error))
    if registry:
        try:
            ledger = parse_prelaunch_ledger(
                root / "reports/prelaunch_progress.md", tuple(registry)
            )
        except (OSError, ValueError) as error:
            errors.append(str(error))

    pass_report_checks: dict[str, dict[str, dict[str, Any]]] = {}
    if ledger:
        for task_id, entry in ledger.items():
            if entry["status"] != "pass":
                continue
            task_checks: dict[str, dict[str, Any]] = {}
            for relative in registry[task_id]:
                path = root / relative
                present = path.is_file()
                nonempty = present and path.stat().st_size > 0
                task_checks[relative] = {
                    "present": present,
                    "nonempty": nonempty,
                    "size_bytes": path.stat().st_size if present else None,
                }
                if not nonempty:
                    errors.append(f"pass task {task_id} lacks non-empty named report: {relative}")
            pass_report_checks[task_id] = task_checks

    l13_dependency = True
    if ledger and ledger["L13"]["status"] == "pass":
        prereg = root / "reports/preregistration_pilot_v1.md"
        l13_dependency = ledger["L12"]["status"] == "pass" and prereg.is_file() and prereg.stat().st_size > 0
        if not l13_dependency:
            errors.append("L13 pass requires L12 pass and a non-empty reports/preregistration_pilot_v1.md")

    audited_checks: dict[str, dict[str, Any]] = {}
    try:
        audited_checks, audited_errors = audited_file_checks(root / "reports")
        errors.extend(audited_errors)
    except OSError as error:
        errors.append(str(error))

    consistency_audit: dict[str, Any] = {}
    if ledger and registry:
        from scripts.audit_consistency import build_consistency_audit

        consistency_audit = build_consistency_audit(root, ledger, registry)
        errors.extend(consistency_audit["errors"])

    checks = {
        "task_registry_has_exact_L0_through_L13": bool(registry),
        "ledger_has_exact_one_valid_line_per_registered_task": bool(ledger),
        "every_pass_has_nonempty_named_reports": bool(ledger)
        and all(
            all(record["present"] and record["nonempty"] for record in reports.values())
            for reports in pass_report_checks.values()
        ),
        "L13_pass_implies_L12_pass_and_preregistration": bool(ledger) and l13_dependency,
        "audited_reports_are_not_byte_identical_to_counterparts": not any(
            record["byte_identical"] is True for record in audited_checks.values()
        ),
        "scientific_consistency_audit_passes": consistency_audit.get("status")
        == "pass",
    }
    return {
        "schema_version": "blind-gains.prelaunch-objective-audit.v1",
        "status": "pass" if all(checks.values()) and not errors else "fail",
        "checks": checks,
        "expected_task_ids": list(EXPECTED_TASK_IDS),
        "registry": {task_id: list(paths) for task_id, paths in registry.items()},
        "ledger": ledger,
        "pass_report_checks": pass_report_checks,
        "audited_file_checks": audited_checks,
        "scientific_consistency_audit": consistency_audit,
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--output", type=Path, default=Path("reports/prelaunch_objective_audit.json")
    )
    args = parser.parse_args()
    payload = build_prelaunch_objective_audit(args.root)
    output = args.output if args.output.is_absolute() else args.root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, output)
    print(json.dumps(payload, sort_keys=True))
    raise SystemExit(0 if payload["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
