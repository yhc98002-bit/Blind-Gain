#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from scripts.audit_prelaunch_objective import audited_file_checks


EXPECTED_TASK_IDS = tuple(f"M{index}" for index in range(15))
REQUIRED_PASS_TASKS = ("M0", "M1", "M11", "M13")
REGISTRY_ROW_RE = re.compile(r"^\| (M(?:[0-9]|1[0-4])) \| .+ \| .+ \| (?P<evidence>.+) \|$")
REPORT_TOKEN_RE = re.compile(r"`(reports/[^`]+)`")
LEDGER_LINE_RE = re.compile(r"^(M(?:[0-9]|1[0-4])) \| (pass|fail|blocked) \| (\S.*)$")
PREREGISTRATION = Path("reports/preregistration_pilot_v1.md")
REGISTERED_EXTENSIONS = Path("docs/registered_extensions_v1.md")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_main_registry(path: Path) -> dict[str, tuple[str, ...]]:
    registry: dict[str, tuple[str, ...]] = {}
    order: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = REGISTRY_ROW_RE.fullmatch(line)
        if match is None:
            continue
        task_id = match.group(1)
        if task_id in registry:
            raise ValueError(f"duplicate main registry task: {task_id}")
        reports = tuple(REPORT_TOKEN_RE.findall(match.group("evidence")))
        if not reports:
            raise ValueError(f"main registry task has no named report: {task_id}")
        if len(reports) != len(set(reports)):
            raise ValueError(f"main registry task repeats a report: {task_id}")
        for relative in reports:
            candidate = Path(relative)
            if (
                candidate.is_absolute()
                or ".." in candidate.parts
                or not candidate.parts
                or candidate.parts[0] != "reports"
            ):
                raise ValueError(f"unsafe named report for {task_id}: {relative}")
        registry[task_id] = reports
        order.append(task_id)
    if tuple(order) != EXPECTED_TASK_IDS:
        raise ValueError(
            "main registry must define exactly M0 through M14 in order: "
            f"found={order}"
        )
    return registry


def parse_main_progress(
    path: Path, expected_ids: tuple[str, ...]
) -> dict[str, dict[str, str]]:
    ledger: dict[str, dict[str, str]] = {}
    order: list[str] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for line_number, line in enumerate(lines, start=1):
        match = LEDGER_LINE_RE.fullmatch(line)
        if match is None:
            raise ValueError(f"invalid main progress line {line_number}: {line!r}")
        task_id, status, note = match.groups()
        if task_id in ledger:
            raise ValueError(f"duplicate main progress task: {task_id}")
        ledger[task_id] = {"status": status, "note": note}
        order.append(task_id)
    if tuple(order) != expected_ids:
        raise ValueError(
            "main progress must contain exactly one line per registry task in order: "
            f"found={order}"
        )
    return ledger


def _nonempty_file(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 0


def build_main_objective_audit(root: Path) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    registry: dict[str, tuple[str, ...]] = {}
    ledger: dict[str, dict[str, str]] = {}

    try:
        registry = parse_main_registry(root / "MAIN_TASKS.md")
    except (OSError, ValueError) as error:
        errors.append(str(error))
    if registry:
        try:
            ledger = parse_main_progress(
                root / "reports/main_progress.md", tuple(registry)
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
                    "sha256": _sha256(path) if nonempty else None,
                }
                if not nonempty:
                    errors.append(
                        f"pass task {task_id} lacks non-empty named report: {relative}"
                    )
            pass_report_checks[task_id] = task_checks

    preregistration_required_by = [
        task_id
        for task_id in ("M2", "M3")
        if ledger.get(task_id, {}).get("status") == "pass"
    ]
    preregistration_ok = not preregistration_required_by or _nonempty_file(
        root / PREREGISTRATION
    )
    if not preregistration_ok:
        errors.append(
            f"pass tasks {preregistration_required_by} require {PREREGISTRATION}"
        )

    extensions_required_by = [
        task_id
        for task_id in ("M5", "M6", "M7", "M9")
        if ledger.get(task_id, {}).get("status") == "pass"
    ]
    extensions_ok = not extensions_required_by or _nonempty_file(
        root / REGISTERED_EXTENSIONS
    )
    if not extensions_ok:
        errors.append(
            f"pass tasks {extensions_required_by} require {REGISTERED_EXTENSIONS}"
        )

    audited_checks: dict[str, dict[str, Any]] = {}
    try:
        audited_checks, audited_errors = audited_file_checks(root / "reports")
        errors.extend(audited_errors)
    except OSError as error:
        errors.append(str(error))
    audited_distinct = not any(
        record.get("byte_identical") is True for record in audited_checks.values()
    )
    required_tasks_pass = bool(ledger) and all(
        ledger.get(task_id, {}).get("status") == "pass"
        for task_id in REQUIRED_PASS_TASKS
    )
    if ledger and not required_tasks_pass:
        missing = [
            task_id
            for task_id in REQUIRED_PASS_TASKS
            if ledger.get(task_id, {}).get("status") != "pass"
        ]
        errors.append(f"required objective tasks are not pass: {missing}")

    checks = {
        "registry_defines_exact_M0_through_M14": bool(registry),
        "progress_has_exactly_one_valid_line_per_registry_task": bool(ledger),
        "required_M0_M1_M11_M13_tasks_pass": required_tasks_pass,
        "every_pass_has_all_nonempty_named_reports": bool(ledger)
        and all(
            all(record["present"] and record["nonempty"] for record in reports.values())
            for reports in pass_report_checks.values()
        ),
        "M2_or_M3_pass_requires_preregistration": bool(ledger)
        and preregistration_ok,
        "M5_M6_M7_or_M9_pass_requires_registered_extensions": bool(ledger)
        and extensions_ok,
        "audited_files_are_not_byte_identical_to_counterparts": audited_distinct,
    }
    return {
        "schema_version": "blind-gains.main-objective-audit.v1",
        "status": "pass" if all(checks.values()) and not errors else "fail",
        "checks": checks,
        "expected_task_ids": list(EXPECTED_TASK_IDS),
        "required_pass_task_ids": list(REQUIRED_PASS_TASKS),
        "registry": {task_id: list(paths) for task_id, paths in registry.items()},
        "ledger": ledger,
        "pass_report_checks": pass_report_checks,
        "preregistration_dependency": {
            "required_by": preregistration_required_by,
            "path": str(PREREGISTRATION),
            "present_nonempty": _nonempty_file(root / PREREGISTRATION),
            "satisfied": preregistration_ok,
        },
        "registered_extensions_dependency": {
            "required_by": extensions_required_by,
            "path": str(REGISTERED_EXTENSIONS),
            "present_nonempty": _nonempty_file(root / REGISTERED_EXTENSIONS),
            "satisfied": extensions_ok,
        },
        "audited_file_checks": audited_checks,
        "errors": errors,
    }


def render_markdown(payload: dict[str, Any], json_path: Path) -> str:
    check_rows = [
        f"| `{name}` | `{str(value).lower()}` |"
        for name, value in payload["checks"].items()
    ]
    passed_tasks = [
        task_id
        for task_id, entry in payload["ledger"].items()
        if entry["status"] == "pass"
    ]
    lines = [
        "# Main Objective Audit V1",
        "",
        "Status:",
        f"- Machine audit status: `{payload['status']}`.",
        f"- Machine status JSON: `{json_path}`.",
        "- This audit checks registry and dependency integrity; scientific task gates remain PI decisions.",
        "",
        "Checks:",
        "| Check | Result |",
        "| --- | --- |",
        *check_rows,
        "",
        "Evidence:",
        f"- Registry task IDs: `{payload['expected_task_ids']}`.",
        f"- Ledger rows: `{len(payload['ledger'])}`.",
        f"- Tasks currently marked pass: `{passed_tasks}`.",
        f"- Audited files examined: `{len(payload['audited_file_checks'])}`.",
        f"- Errors: `{payload['errors']}`.",
        "",
        "Decision:",
        "- A machine `pass` proves only the enumerated repository invariants at this revision.",
        "- The separate full `python -m pytest tests/` invocation remains required evidence.",
    ]
    return "\n".join(lines) + "\n"


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    json_output = args.json_output if args.json_output.is_absolute() else root / args.json_output
    markdown_output = (
        args.markdown_output
        if args.markdown_output.is_absolute()
        else root / args.markdown_output
    )
    if json_output.exists() or markdown_output.exists():
        raise FileExistsError("refusing to overwrite main objective audit artifacts")
    payload = build_main_objective_audit(root)
    _atomic_write(json_output, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    display_json = json_output.relative_to(root) if json_output.is_relative_to(root) else json_output
    _atomic_write(markdown_output, render_markdown(payload, Path(display_json)))
    print(json.dumps({"status": payload["status"], "errors": payload["errors"]}))
    raise SystemExit(0 if payload["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
