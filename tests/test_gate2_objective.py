from __future__ import annotations

from pathlib import Path

from scripts.audit_gate2_objective import (
    GATE2_TASK_IDS,
    GATE2_TASK_REPORTS,
    build_gate2_objective_audit,
)


ROOT = Path(__file__).resolve().parents[1]


def _fixture_root(tmp_path: Path, *, pass_task: str = "P0.1") -> Path:
    reports = tmp_path / "reports"
    reports.mkdir()
    lines = []
    for task_id in GATE2_TASK_IDS:
        status = "pass" if task_id == pass_task else "blocked"
        lines.append(f"{task_id} | {status} | fixture note for {task_id}")
    (reports / "gate2_progress.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for relative in GATE2_TASK_REPORTS[pass_task]:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")
    return tmp_path


def test_current_repository_satisfies_gate2_ledger_objective() -> None:
    payload = build_gate2_objective_audit(ROOT)
    assert payload["status"] == "pass", payload["errors"]
    assert payload["ledger_task_count"] == 18


def test_gate2_objective_rejects_extra_post_gate_task(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    ledger = root / "reports" / "gate2_progress.md"
    ledger.write_text(ledger.read_text(encoding="utf-8") + "P3.1 | blocked | extra\n", encoding="utf-8")

    payload = build_gate2_objective_audit(root)

    assert payload["status"] == "fail"
    assert "extra=['P3.1']" in payload["errors"][0]


def test_gate2_objective_rejects_duplicate_status_line(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    ledger = root / "reports" / "gate2_progress.md"
    ledger.write_text(ledger.read_text(encoding="utf-8") + "P0.1 | pass | duplicate\n", encoding="utf-8")

    payload = build_gate2_objective_audit(root)

    assert payload["status"] == "fail"
    assert "duplicate Gate 2 task ID" in payload["errors"][0]


def test_gate2_objective_rejects_pass_without_named_report(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    missing = root / GATE2_TASK_REPORTS["P0.1"][0]
    missing.unlink()

    payload = build_gate2_objective_audit(root)

    assert payload["status"] == "fail"
    assert payload["checks"]["every_pass_task_has_all_named_reports"] is False


def test_gate2_objective_rejects_unresolved_pass_status_line(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    report = root / GATE2_TASK_REPORTS["P0.1"][0]
    report.write_text("Status:\n- Evaluation remains pending.\n", encoding="utf-8")

    payload = build_gate2_objective_audit(root)

    assert payload["status"] == "fail"
    assert payload["scientific_consistency_audit"]["checks"][
        "pass_report_status_lines_are_resolved"
    ] is False


def test_gate2_objective_rejects_byte_identical_audited_copy(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    (root / "reports" / "result.md").write_text("same\n", encoding="utf-8")
    (root / "reports" / "result_audited.md").write_text("same\n", encoding="utf-8")

    payload = build_gate2_objective_audit(root)

    assert payload["status"] == "fail"
    assert payload["scientific_consistency_audit"]["checks"][
        "audited_files_are_distinct"
    ] is False


def test_gate2_objective_rejects_missing_or_nonpass_machine_status(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    report = root / GATE2_TASK_REPORTS["P0.1"][0]
    report.write_text(
        "Status:\n- Complete.\n\nEvidence:\n"
        "- Machine status JSON: `reports/missing.json`.\n",
        encoding="utf-8",
    )
    payload = build_gate2_objective_audit(root)
    assert payload["status"] == "fail"

    machine = root / "reports" / "machine.json"
    machine.write_text('{"status": "fail"}\n', encoding="utf-8")
    report.write_text(
        "Status:\n- Complete.\n\nEvidence:\n"
        "- Machine status JSON: `reports/machine.json`.\n",
        encoding="utf-8",
    )
    payload = build_gate2_objective_audit(root)
    assert payload["status"] == "fail"
    assert payload["scientific_consistency_audit"]["checks"][
        "referenced_machine_statuses_pass"
    ] is False


def test_gate2_objective_rejects_incomplete_full_layer1_claim(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    report = root / GATE2_TASK_REPORTS["P0.1"][0]
    report.write_text(
        "Status:\n- The full Layer-1 base table contains MMStar and BLINK.\n",
        encoding="utf-8",
    )

    payload = build_gate2_objective_audit(root)

    assert payload["status"] == "fail"
    assert payload["scientific_consistency_audit"]["checks"][
        "full_claims_include_registered_members"
    ] is False
