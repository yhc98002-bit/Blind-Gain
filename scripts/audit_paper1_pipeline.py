#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from scripts.paper1.build_figures import PLOTTERS, validate_spec


EXPECTED_DOCS = (
    "README.md",
    "outline.md",
    "master_result_table.md",
    "figure_registry.md",
    "methods_appendix.md",
    "data_card.md",
    "contribution_nonoverlap.md",
    "figure_specs.json",
)
EXPECTED_FIGURES = {
    "decomposition": "grouped_bar",
    "hurdle": "hurdle",
    "dissociation": "scatter",
    "audits": "table",
}
PROHIBITED_CLAIMS = (
    "captions contain more information than images",
    "vision hurts",
    "caption training is blind training",
)
REGISTERED_SEED1_STATUS = "registered seed-1 result; confirmation pending seeds 2–3"
REGISTERED_SEED1_FAMILIES = {
    "3B Geometry3K seed 1: A2-gray R19 geometry delta",
    "3B Geometry3K seed 1: `D_caption^final`",
}
REGISTERED_DIAGNOSTIC_STATUS = (
    "complete; not an original pilot endpoint; branch unassigned"
)
REGISTERED_DIAGNOSTIC_VALUES = {
    "Seed-1 post-registered visual-evidence ranking diagnostic": (
        "geometry margin DiD +0.150142 [0.144849,0.155388]; "
        "pair-success effect 0.000000; top-1 effect +0.008333"
    )
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _result_registry_rows(master: str) -> tuple[list[dict[str, str]], list[str]]:
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    for line_number, line in enumerate(master.splitlines(), start=1):
        if not line.startswith("|") or "Registered artifact" in line or "---" in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 4:
            errors.append(f"malformed result registry row {line_number}: {line}")
            continue
        family, artifact, status, value = cells
        rows.append(
            {
                "family": family,
                "artifact": artifact.strip("`"),
                "status": status,
                "value": value.strip("`"),
            }
        )
    return rows, errors


def build_audit(root: Path) -> dict[str, Any]:
    root = root.resolve()
    paper = root / "docs/paper1"
    files: dict[str, dict[str, Any]] = {}
    for name in EXPECTED_DOCS:
        path = paper / name
        present = path.is_file()
        nonempty = present and path.stat().st_size > 0
        files[name] = {
            "present": present,
            "nonempty": nonempty,
            "size_bytes": path.stat().st_size if present else None,
            "sha256": _sha256(path) if nonempty else None,
        }

    errors: list[str] = []
    try:
        specs = json.loads((paper / "figure_specs.json").read_text(encoding="utf-8"))[
            "figures"
        ]
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        specs = {}
        errors.append(f"invalid figure registry: {error}")

    figure_checks: dict[str, dict[str, Any]] = {}
    for figure, expected_plotter in EXPECTED_FIGURES.items():
        spec = specs.get(figure)
        pending = isinstance(spec, dict) and spec.get("status") == "pending"
        fail_closed = False
        if isinstance(spec, dict):
            try:
                validate_spec(root, figure, spec)
            except ValueError as error:
                fail_closed = "not ready" in str(error)
        figure_checks[figure] = {
            "present": isinstance(spec, dict),
            "status_pending": pending,
            "pending_refuses_render": fail_closed,
            "registered_plotter": expected_plotter,
            "plotter_implemented": expected_plotter in PLOTTERS,
        }

    markdown = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(paper.glob("*.md"))
        if path.is_file()
    )
    lower_markdown = markdown.lower()
    master = (paper / "master_result_table.md").read_text(encoding="utf-8") if (
        paper / "master_result_table.md"
    ).is_file() else ""
    result_rows, result_row_errors = _result_registry_rows(master)
    errors.extend(result_row_errors)
    pending_rows = [row for row in result_rows if row["status"] == "pending"]
    seed1_rows = [row for row in result_rows if row["status"] == REGISTERED_SEED1_STATUS]
    diagnostic_rows = [
        row for row in result_rows if row["status"] == REGISTERED_DIAGNOSTIC_STATUS
    ]
    known_status_rows = pending_rows + seed1_rows + diagnostic_rows
    seed1_artifacts_exist = all(
        (root / row["artifact"]).is_file() and (root / row["artifact"]).stat().st_size > 0
        for row in seed1_rows
    )
    seed1_values_numeric = True
    for row in seed1_rows:
        try:
            float(row["value"])
        except ValueError:
            seed1_values_numeric = False
    diagnostic_artifacts_exist = all(
        (root / row["artifact"]).is_file() and (root / row["artifact"]).stat().st_size > 0
        for row in diagnostic_rows
    )
    diagnostic_values_exact = {
        row["family"]: row["value"] for row in diagnostic_rows
    } == REGISTERED_DIAGNOSTIC_VALUES

    checks = {
        "all_expected_documents_nonempty": all(
            record["present"] and record["nonempty"] for record in files.values()
        ),
        "exact_registered_figure_set": set(specs) == set(EXPECTED_FIGURES),
        "all_required_plotters_implemented": all(
            record["plotter_implemented"] for record in figure_checks.values()
        ),
        "pending_figures_fail_closed": all(
            record["status_pending"] and record["pending_refuses_render"]
            for record in figure_checks.values()
        ),
        "result_registry_rows_follow_registered_state_contract": bool(result_rows)
        and len(known_status_rows) == len(result_rows)
        and all(row["value"] == "{result-pending}" for row in pending_rows)
        and {row["family"] for row in seed1_rows} == REGISTERED_SEED1_FAMILIES
        and seed1_artifacts_exist
        and seed1_values_numeric,
        "registered_diagnostic_row_is_exact": diagnostic_artifacts_exist
        and diagnostic_values_exact,
        "required_terminology_present": "caption-mediated accessibility" in lower_markdown,
        "prohibited_claims_absent": not any(
            phrase in lower_markdown for phrase in PROHIBITED_CLAIMS
        ),
        "figure_builder_and_tests_present": (
            root / "scripts/paper1/build_figures.py"
        ).is_file()
        and (root / "tests/test_paper1_figure_builder.py").is_file(),
    }
    for name, value in checks.items():
        if not value:
            errors.append(name)
    return {
        "schema_version": "blind-gains.paper1-pipeline-audit.v2",
        "status": "pass" if all(checks.values()) and not errors else "fail",
        "checks": checks,
        "files": files,
        "figures": figure_checks,
        "result_rows": result_rows,
        "errors": errors,
    }


def _atomic_write(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite Paper-1 audit: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def render_markdown(
    payload: dict[str, Any], json_path: Path, *, report_version: int
) -> str:
    check_rows = [
        f"| `{name}` | `{str(value).lower()}` |"
        for name, value in payload["checks"].items()
    ]
    return "\n".join(
        [
            f"# Paper 1 Pipeline Status V{report_version}",
            "",
            "Status:",
            f"- M13 pipeline-delivery status: `{payload['status']}`.",
            "- This closes the reusable paper artifact pipeline, not any pending scientific result.",
            "- Result slots remain explicit and fail closed until their registered, hash-pinned inputs exist.",
            "",
            "Checks:",
            "| Check | Result |",
            "| --- | --- |",
            *check_rows,
            "",
            "Evidence:",
            f"- Machine audit: `{json_path}`.",
            "- Workspace: `docs/paper1/`.",
            "- Figure builder: `scripts/paper1/build_figures.py`.",
            "- Builder tests: `tests/test_paper1_figure_builder.py`.",
            "- Supported outputs: decomposition bars, hurdle intervals, dissociation scatter, and audit tables.",
            "",
            "Decision:",
            "- Pipeline implementation is complete and remains continuously populated as registered readouts land.",
            "- No pending value is promoted to a result by this status.",
        ]
    ) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    payload = build_audit(root)
    json_path = args.json_output if args.json_output.is_absolute() else root / args.json_output
    markdown_path = (
        args.markdown_output
        if args.markdown_output.is_absolute()
        else root / args.markdown_output
    )
    version_match = re.search(r"_v([0-9]+)$", markdown_path.stem)
    if version_match is None:
        raise ValueError(
            "paper pipeline markdown output must end in a version suffix such as _v4.md"
        )
    report_version = int(version_match.group(1))
    _atomic_write(json_path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    display_json = json_path.relative_to(root) if json_path.is_relative_to(root) else json_path
    _atomic_write(
        markdown_path,
        render_markdown(
            payload,
            Path(display_json),
            report_version=report_version,
        ),
    )
    print(json.dumps({"status": payload["status"], "errors": payload["errors"]}))
    raise SystemExit(0 if payload["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
