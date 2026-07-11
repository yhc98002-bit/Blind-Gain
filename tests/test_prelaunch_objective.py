from __future__ import annotations

from pathlib import Path

from scripts.audit_prelaunch_objective import (
    EXPECTED_TASK_IDS,
    build_prelaunch_objective_audit,
)


ROOT = Path(__file__).resolve().parents[1]


def _fixture_root(tmp_path: Path) -> Path:
    reports = tmp_path / "reports"
    reports.mkdir()
    registry = ["# Fixture registry", ""]
    ledger = []
    for task_id in EXPECTED_TASK_IDS:
        registry.append(f"- `{task_id}` reports: `reports/{task_id.lower()}.md`")
        ledger.append(f"{task_id} | blocked | fixture note for {task_id}")
    (tmp_path / "PRELAUNCH_TASKS.md").write_text("\n".join(registry) + "\n", encoding="utf-8")
    (reports / "prelaunch_progress.md").write_text("\n".join(ledger) + "\n", encoding="utf-8")
    return tmp_path


def test_current_repository_satisfies_prelaunch_ledger_objective() -> None:
    payload = build_prelaunch_objective_audit(ROOT)

    assert payload["status"] == "pass", payload["errors"]
    assert list(payload["ledger"]) == list(EXPECTED_TASK_IDS)


def test_rejects_extra_ledger_task(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    ledger = root / "reports/prelaunch_progress.md"
    ledger.write_text(ledger.read_text(encoding="utf-8") + "L14 | blocked | extra\n", encoding="utf-8")

    payload = build_prelaunch_objective_audit(root)

    assert payload["status"] == "fail"
    assert "invalid prelaunch ledger line" in payload["errors"][0]


def test_rejects_extra_task_defined_in_registry(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    registry = root / "PRELAUNCH_TASKS.md"
    registry.write_text(
        registry.read_text(encoding="utf-8") + "- `L14` reports: `reports/l14.md`\n",
        encoding="utf-8",
    )

    payload = build_prelaunch_objective_audit(root)

    assert payload["status"] == "fail"
    assert "extra=['L14']" in payload["errors"][0]


def test_rejects_duplicate_ledger_task(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    ledger = root / "reports/prelaunch_progress.md"
    ledger.write_text(ledger.read_text(encoding="utf-8") + "L0 | blocked | duplicate\n", encoding="utf-8")

    payload = build_prelaunch_objective_audit(root)

    assert payload["status"] == "fail"
    assert "duplicate prelaunch task ID" in payload["errors"][0]


def test_rejects_pass_with_missing_or_empty_named_report(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    ledger = root / "reports/prelaunch_progress.md"
    lines = ledger.read_text(encoding="utf-8").splitlines()
    lines[1] = "L1 | pass | incorrectly asserted"
    ledger.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (root / "reports/l1.md").write_bytes(b"")

    payload = build_prelaunch_objective_audit(root)

    assert payload["status"] == "fail"
    assert payload["pass_report_checks"]["L1"]["reports/l1.md"]["nonempty"] is False


def test_rejects_L13_pass_without_L12_and_preregistration(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    ledger = root / "reports/prelaunch_progress.md"
    lines = ledger.read_text(encoding="utf-8").splitlines()
    lines[13] = "L13 | pass | dependency violation"
    ledger.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (root / "reports/l13.md").write_text("result\n", encoding="utf-8")

    payload = build_prelaunch_objective_audit(root)

    assert payload["status"] == "fail"
    assert payload["checks"]["L13_pass_implies_L12_pass_and_preregistration"] is False


def test_accepts_L13_only_with_L12_and_nonempty_preregistration(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    registry = root / "PRELAUNCH_TASKS.md"
    text = registry.read_text(encoding="utf-8").replace(
        "- `L12` reports: `reports/l12.md`",
        "- `L12` reports: `reports/preregistration_pilot_v1.md`",
    )
    registry.write_text(text, encoding="utf-8")
    ledger = root / "reports/prelaunch_progress.md"
    lines = ledger.read_text(encoding="utf-8").splitlines()
    lines[12] = "L12 | pass | approved preregistration"
    lines[13] = "L13 | pass | completed pilot"
    ledger.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (root / "reports/preregistration_pilot_v1.md").write_text("approved\n", encoding="utf-8")
    (root / "reports/l13.md").write_text("result\n", encoding="utf-8")

    payload = build_prelaunch_objective_audit(root)

    assert payload["status"] == "pass", payload["errors"]


def test_rejects_direct_byte_identical_audited_counterpart(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    (root / "reports/result.md").write_text("same\n", encoding="utf-8")
    (root / "reports/result_audited.md").write_text("same\n", encoding="utf-8")

    payload = build_prelaunch_objective_audit(root)

    assert payload["status"] == "fail"
    assert payload["audited_file_checks"]["reports/result_audited.md"]["byte_identical"] is True


def test_rejects_versioned_audited_copy_of_unversioned_report(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    (root / "reports/result.md").write_text("same\n", encoding="utf-8")
    (root / "reports/result_v3_audited.md").write_text("same\n", encoding="utf-8")

    payload = build_prelaunch_objective_audit(root)

    assert payload["status"] == "fail"
    check = payload["audited_file_checks"]["reports/result_v3_audited.md"]
    assert check["counterpart"].endswith("reports/result.md")
    assert check["byte_identical"] is True


def test_accepts_distinct_audited_artifact(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    (root / "reports/result.md").write_text("summary\n", encoding="utf-8")
    (root / "reports/result_audited.md").write_text("audit evidence\n", encoding="utf-8")

    payload = build_prelaunch_objective_audit(root)

    assert payload["status"] == "pass", payload["errors"]


def test_rejects_identical_audited_counterpart_in_nested_report_directory(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    nested = root / "reports/category"
    nested.mkdir()
    (nested / "result.json").write_text('{"value": 1}\n', encoding="utf-8")
    (nested / "result_audited.json").write_text('{"value": 1}\n', encoding="utf-8")

    payload = build_prelaunch_objective_audit(root)

    assert payload["status"] == "fail"
    check = payload["audited_file_checks"]["reports/category/result_audited.json"]
    assert check["byte_identical"] is True
