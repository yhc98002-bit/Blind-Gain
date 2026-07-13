#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    result_rows = [
        line
        for line in master.splitlines()
        if line.startswith("|") and "Registered artifact" not in line and "---" not in line
    ]

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
        "result_registry_has_only_explicit_pending_rows": bool(result_rows)
        and all("pending" in line and "{result-pending}" in line for line in result_rows),
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
        "schema_version": "blind-gains.paper1-pipeline-audit.v1",
        "status": "pass" if all(checks.values()) and not errors else "fail",
        "checks": checks,
        "files": files,
        "figures": figure_checks,
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


def render_markdown(payload: dict[str, Any], json_path: Path) -> str:
    check_rows = [
        f"| `{name}` | `{str(value).lower()}` |"
        for name, value in payload["checks"].items()
    ]
    return "\n".join(
        [
            "# Paper 1 Pipeline Status V3",
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
    _atomic_write(json_path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    display_json = json_path.relative_to(root) if json_path.is_relative_to(root) else json_path
    _atomic_write(markdown_path, render_markdown(payload, Path(display_json)))
    print(json.dumps({"status": payload["status"], "errors": payload["errors"]}))
    raise SystemExit(0 if payload["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
