from __future__ import annotations

import json
from pathlib import Path

from scripts.audit_paper1_pipeline import build_audit, render_markdown


def test_current_paper1_pipeline_passes_all_delivery_checks() -> None:
    root = Path(__file__).resolve().parents[1]

    payload = build_audit(root)

    assert payload["status"] == "pass"
    assert all(payload["checks"].values())
    assert payload["errors"] == []


def test_ready_label_with_pending_payload_is_rejected(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    paper = tmp_path / "docs/paper1"
    paper.mkdir(parents=True)
    for source in (root / "docs/paper1").iterdir():
        if source.is_file():
            (paper / source.name).write_bytes(source.read_bytes())
    specs = json.loads((paper / "figure_specs.json").read_text(encoding="utf-8"))
    specs["figures"]["decomposition"]["status"] = "ready"
    (paper / "figure_specs.json").write_text(
        json.dumps(specs, indent=2) + "\n", encoding="utf-8"
    )
    scripts = tmp_path / "scripts/paper1"
    scripts.mkdir(parents=True)
    (scripts / "build_figures.py").write_text("fixture\n", encoding="utf-8")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_paper1_figure_builder.py").write_text("fixture\n", encoding="utf-8")

    payload = build_audit(tmp_path)

    assert payload["status"] == "fail"
    assert payload["checks"]["pending_figures_fail_closed"] is False


def test_versioned_markdown_title_uses_requested_report_version() -> None:
    payload = {"status": "pass", "checks": {"fixture": True}}

    markdown = render_markdown(
        payload,
        Path("reports/paper1_pipeline_status_v5.json"),
        report_version=5,
    )

    assert markdown.startswith("# Paper 1 Pipeline Status V5\n")
    assert "Status V3" not in markdown
