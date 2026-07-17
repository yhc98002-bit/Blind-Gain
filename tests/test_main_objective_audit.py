from __future__ import annotations

from pathlib import Path

import pytest

from scripts.audit_main_objective import (
    EXPECTED_TASK_IDS,
    REQUIRED_PASS_TASKS,
    build_main_objective_audit,
    parse_main_progress,
    parse_main_registry,
    render_markdown,
)


def _registry_text() -> str:
    rows = [
        "# Registry",
        "",
        "| ID | Task | Dependencies | Required evidence |",
        "| --- | --- | --- | --- |",
    ]
    for task_id in EXPECTED_TASK_IDS:
        evidence = f"`reports/{task_id.lower()}_report.md`"
        if task_id == "M4":
            evidence = "`docs/registered_extensions_v1.md`; " + evidence
        rows.append(f"| {task_id} | Task {task_id} | none | {evidence} |")
    return "\n".join(rows) + "\n"


def _fixture(tmp_path: Path) -> Path:
    (tmp_path / "reports").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "MAIN_TASKS.md").write_text(_registry_text(), encoding="utf-8")
    ledger = [f"{task_id} | blocked | fixture {task_id}" for task_id in EXPECTED_TASK_IDS]
    (tmp_path / "reports/main_progress.md").write_text(
        "\n".join(ledger) + "\n", encoding="utf-8"
    )
    return tmp_path


def _mark_pass(root: Path, task_id: str) -> None:
    path = root / "reports/main_progress.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            f"{task_id} | blocked | fixture {task_id}",
            f"{task_id} | pass | fixture {task_id}",
        ),
        encoding="utf-8",
    )


def test_required_objective_tasks_cannot_remain_blocked(tmp_path: Path) -> None:
    root = _fixture(tmp_path)

    payload = build_main_objective_audit(root)

    assert payload["status"] == "fail"
    assert payload["checks"]["required_M0_M1_M4_M13_tasks_pass"] is False
    assert "required objective tasks are not pass" in "\n".join(payload["errors"])


def test_required_objective_tasks_pass_with_nonempty_evidence(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    for task_id in REQUIRED_PASS_TASKS:
        _mark_pass(root, task_id)
        (root / f"reports/{task_id.lower()}_report.md").write_text(
            f"{task_id} evidence\n", encoding="utf-8"
        )

    payload = build_main_objective_audit(root)

    assert payload["status"] == "pass"
    assert all(payload["checks"].values())


def test_m11_pass_cannot_substitute_for_required_m4(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    for task_id in ("M0", "M1", "M11", "M13"):
        _mark_pass(root, task_id)
        (root / f"reports/{task_id.lower()}_report.md").write_text(
            f"{task_id} evidence\n", encoding="utf-8"
        )

    payload = build_main_objective_audit(root)

    assert payload["status"] == "fail"
    assert payload["checks"]["required_M0_M1_M4_M13_tasks_pass"] is False
    assert "M4" in "\n".join(payload["errors"])


def test_pass_task_requires_every_named_report_nonempty(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    _mark_pass(root, "M8")

    payload = build_main_objective_audit(root)

    assert payload["status"] == "fail"
    assert payload["checks"]["every_pass_has_all_nonempty_named_reports"] is False
    assert "pass task M8 lacks non-empty named report" in "\n".join(payload["errors"])


@pytest.mark.parametrize("task_id", ("M2", "M3"))
def test_training_pass_requires_preregistration(tmp_path: Path, task_id: str) -> None:
    root = _fixture(tmp_path)
    _mark_pass(root, task_id)
    (root / f"reports/{task_id.lower()}_report.md").write_text("result\n", encoding="utf-8")

    payload = build_main_objective_audit(root)

    assert payload["status"] == "fail"
    assert payload["checks"]["M2_or_M3_pass_requires_preregistration"] is False


@pytest.mark.parametrize("task_id", ("M5", "M6", "M7", "M9"))
def test_extension_pass_requires_registered_document(tmp_path: Path, task_id: str) -> None:
    root = _fixture(tmp_path)
    _mark_pass(root, task_id)
    (root / f"reports/{task_id.lower()}_report.md").write_text("result\n", encoding="utf-8")

    payload = build_main_objective_audit(root)

    assert payload["status"] == "fail"
    assert (
        payload["checks"]["M5_M6_M7_or_M9_pass_requires_registered_extensions"]
        is False
    )


def test_extension_pass_rejects_draft_that_only_mentions_registration_marker(
    tmp_path: Path,
) -> None:
    root = _fixture(tmp_path)
    _mark_pass(root, "M5")
    (root / "reports/m5_report.md").write_text("result\n", encoding="utf-8")
    (root / "docs/registered_extensions_v1.md").write_text(
        "# Draft\n\nThis will later become `merged-at-HEAD; merge is sign-off`.\n",
        encoding="utf-8",
    )

    payload = build_main_objective_audit(root)

    assert payload["status"] == "fail"
    assert payload["registered_extensions_dependency"]["present_nonempty"] is True
    assert (
        payload["registered_extensions_dependency"]["exact_merged_at_head_marker"]
        is False
    )
    assert (
        payload["checks"]["M5_M6_M7_or_M9_pass_requires_registered_extensions"]
        is False
    )


def test_extension_pass_accepts_exact_merged_registration_marker(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    _mark_pass(root, "M5")
    (root / "reports/m5_report.md").write_text("result\n", encoding="utf-8")
    (root / "docs/registered_extensions_v1.md").write_text(
        "# Registered\n\n- Registration state: merged-at-HEAD; merge is sign-off.\n",
        encoding="utf-8",
    )

    payload = build_main_objective_audit(root)

    assert payload["registered_extensions_dependency"]["exact_merged_at_head_marker"]
    assert payload["checks"][
        "M5_M6_M7_or_M9_pass_requires_registered_extensions"
    ]


def test_identical_audited_counterpart_is_rejected(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    (root / "reports/measurement.json").write_text('{"status": "pass"}\n', encoding="utf-8")
    (root / "reports/measurement_audited.json").write_text(
        '{"status": "pass"}\n', encoding="utf-8"
    )

    payload = build_main_objective_audit(root)

    assert payload["status"] == "fail"
    assert payload["checks"]["audited_files_are_not_byte_identical_to_counterparts"] is False


def test_progress_rejects_extra_or_duplicate_status_lines(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    progress = root / "reports/main_progress.md"
    progress.write_text(
        progress.read_text(encoding="utf-8") + "M14 | blocked | duplicate\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate main progress task"):
        parse_main_progress(progress, EXPECTED_TASK_IDS)


def test_registry_and_progress_derive_exact_task_order(tmp_path: Path) -> None:
    root = _fixture(tmp_path)

    registry = parse_main_registry(root / "MAIN_TASKS.md")
    progress = parse_main_progress(root / "reports/main_progress.md", tuple(registry))

    assert tuple(registry) == EXPECTED_TASK_IDS
    assert tuple(progress) == EXPECTED_TASK_IDS


def test_versioned_markdown_title_uses_requested_report_version() -> None:
    payload = {
        "status": "pass",
        "checks": {"fixture": True},
        "ledger": {},
        "expected_task_ids": list(EXPECTED_TASK_IDS),
        "audited_file_checks": {},
        "errors": [],
    }

    markdown = render_markdown(
        payload,
        Path("reports/main_objective_audit_v29.json"),
        report_version=29,
    )

    assert markdown.startswith("# Main Objective Audit V29\n")
    assert "Audit V1" not in markdown
