#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from scripts.audit_prelaunch_objective import audited_file_checks


BAD_STATUS_RE = re.compile(r"\b(?:incomplete|pending|failed)\b", re.IGNORECASE)
SECTION_RE = re.compile(r"^[A-Za-z][A-Za-z0-9 /_-]*:$")
MACHINE_STATUS_RE = re.compile(
    r"^- Machine status JSON:\s*`(?P<path>reports/[^`#]+\.json)"
    r"(?:#(?P<pointer>[A-Za-z0-9_.-]+))?`\.?$"
)
FULL_LAYER1_RE = re.compile(
    r"\bfull\s+layer[- ]?1(?:\s+base)?\s+(?:suite|table)\b", re.IGNORECASE
)
REGISTERED_MEMBERS_RE = re.compile(r"^Registered members:\s*(?P<items>.+)$", re.MULTILINE)
REPORTED_MEMBERS_RE = re.compile(r"^Reported members:\s*(?P<items>.+)$", re.MULTILINE)

LAYER1_MEMBERS: tuple[str, ...] = (
    "MMStar",
    "MathVista",
    "BLINK",
    "HallusionBench",
    "MMVP",
    "MathVerse",
    "MMMU",
)


def _status_bullets(text: str) -> list[str]:
    bullets: list[str] = []
    in_status = False
    for line in text.splitlines():
        if line == "Status:":
            in_status = True
            continue
        if in_status and SECTION_RE.fullmatch(line):
            break
        if in_status and line.startswith("- "):
            bullets.append(line)
    return bullets


def _is_pass_status(value: Any) -> bool:
    return value is True or value == "pass"


def _resolve_json_pointer(payload: Any, pointer: str) -> Any:
    value = payload
    for key in pointer.split("."):
        if not isinstance(value, dict) or key not in value:
            raise KeyError(pointer)
        value = value[key]
    return value


def _parse_members(raw: str) -> set[str]:
    return {
        item.strip().strip("`")
        for item in raw.split(",")
        if item.strip().strip("`")
    }


def _full_claim_errors(relative: str, text: str) -> list[str]:
    errors: list[str] = []
    if FULL_LAYER1_RE.search(text):
        missing = [member for member in LAYER1_MEMBERS if member.lower() not in text.lower()]
        if missing:
            errors.append(
                f"full Layer-1 claim in {relative} omits registered members: {missing}"
            )

    if re.search(r"\bfull\s+(?:suite|table)\b", text, re.IGNORECASE):
        registered_match = REGISTERED_MEMBERS_RE.search(text)
        reported_match = REPORTED_MEMBERS_RE.search(text)
        if registered_match and reported_match:
            registered = _parse_members(registered_match.group("items"))
            reported = _parse_members(reported_match.group("items"))
            if registered != reported:
                errors.append(
                    f"full suite/table claim in {relative} has registered/reported mismatch: "
                    f"missing={sorted(registered - reported)}, extra={sorted(reported - registered)}"
                )
    return errors


def build_consistency_audit(
    root: Path,
    ledger: Mapping[str, Mapping[str, str]],
    task_reports: Mapping[str, Sequence[str]],
) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    pass_reports: dict[str, dict[str, Any]] = {}

    for task_id, entry in ledger.items():
        if entry.get("status") != "pass":
            continue
        for relative in task_reports[task_id]:
            path = root / relative
            if path.suffix.lower() != ".md" or not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            bad_status_lines = [
                line for line in _status_bullets(text) if BAD_STATUS_RE.search(line)
            ]
            machine_checks: list[dict[str, Any]] = []
            for line in text.splitlines():
                match = MACHINE_STATUS_RE.fullmatch(line)
                if not match:
                    continue
                json_relative = match.group("path")
                pointer = match.group("pointer") or "status"
                json_path = root / json_relative
                record: dict[str, Any] = {
                    "path": json_relative,
                    "pointer": pointer,
                    "present": json_path.is_file(),
                    "status_value": None,
                    "pass": False,
                }
                if not json_path.is_file():
                    errors.append(
                        f"machine status JSON referenced by {relative} is absent: {json_relative}"
                    )
                else:
                    try:
                        payload = json.loads(json_path.read_text(encoding="utf-8"))
                        value = _resolve_json_pointer(payload, pointer)
                        record["status_value"] = value
                        record["pass"] = _is_pass_status(value)
                        if not record["pass"]:
                            errors.append(
                                f"machine status JSON referenced by {relative} is non-pass: "
                                f"{json_relative}#{pointer}={value!r}"
                            )
                    except (OSError, json.JSONDecodeError, KeyError) as error:
                        errors.append(
                            f"machine status JSON referenced by {relative} is invalid: "
                            f"{json_relative}#{pointer}: {error}"
                        )
                machine_checks.append(record)

            full_claim_errors = _full_claim_errors(relative, text)
            errors.extend(full_claim_errors)
            if bad_status_lines:
                errors.append(
                    f"pass task {task_id} report {relative} has unresolved Status lines: "
                    f"{bad_status_lines}"
                )
            pass_reports[relative] = {
                "task_id": task_id,
                "bad_status_lines": bad_status_lines,
                "machine_status_checks": machine_checks,
                "full_claim_errors": full_claim_errors,
            }

    audited_checks, audited_errors = audited_file_checks(root / "reports")
    errors.extend(audited_errors)
    checks = {
        "pass_report_status_lines_are_resolved": not any(
            record["bad_status_lines"] for record in pass_reports.values()
        ),
        "audited_files_are_distinct": not audited_errors,
        "referenced_machine_statuses_pass": not any(
            not check["pass"]
            for record in pass_reports.values()
            for check in record["machine_status_checks"]
        ),
        "full_claims_include_registered_members": not any(
            record["full_claim_errors"] for record in pass_reports.values()
        ),
    }
    return {
        "schema_version": "blind-gains.scientific-consistency-audit.v1",
        "status": "pass" if all(checks.values()) and not errors else "fail",
        "checks": checks,
        "pass_reports": pass_reports,
        "audited_file_checks": audited_checks,
        "errors": errors,
    }
