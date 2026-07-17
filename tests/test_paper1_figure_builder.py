from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts.paper1.build_figures import build_figure, validate_spec


def test_pending_figure_refuses_to_render(tmp_path: Path) -> None:
    source = tmp_path / "result.json"
    source.write_text("{}\n", encoding="utf-8")
    spec = {
        "status": "pending",
        "inputs": [{"path": "result.json", "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}],
        "plot": "{result-pending:test}",
    }

    with pytest.raises(ValueError, match="not ready"):
        validate_spec(tmp_path, "fixture", spec)


def test_ready_figure_requires_exact_input_hash(tmp_path: Path) -> None:
    source = tmp_path / "result.json"
    source.write_text("{}\n", encoding="utf-8")
    spec = {
        "status": "ready",
        "inputs": [{"path": "result.json", "sha256": "0" * 64}],
        "plot": {"type": "grouped_bar"},
    }

    with pytest.raises(ValueError, match="hash mismatch"):
        validate_spec(tmp_path, "fixture", spec)


def test_ready_chart_delta_requires_registered_null_diagnostics(tmp_path: Path) -> None:
    source = tmp_path / "result.json"
    source.write_text("{}\n", encoding="utf-8")
    spec = {
        "status": "ready",
        "uses_chart_deltas": True,
        "inputs": [
            {
                "path": "result.json",
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            }
        ],
        "plot": {
            "type": "grouped_bar",
            "title": "Cued chart point-value reading delta",
            "labels": ["A1"],
            "series": [{"label": "change", "values": [0.1]}],
        },
    }

    with pytest.raises(ValueError, match="lacks the registered R19 null"):
        validate_spec(tmp_path, "fixture", spec)


def test_registered_dissociation_slot_pins_null_before_chart_delta_rendering() -> None:
    root = Path(__file__).resolve().parents[1]
    payload = __import__("json").loads(
        (root / "docs/paper1/figure_specs.json").read_text(encoding="utf-8")
    )
    spec = payload["figures"]["dissociation"]

    assert spec["uses_chart_deltas"] is True
    assert {
        record["path"]: record["sha256"] for record in spec["inputs"]
    }["reports/pilot_4arm_seed1_r19_null_v1.json"] == (
        "5c8bb51bfca8a9175c8ad7f4efd9d8d8f80e56d3595f3f1c9f30645a7d9c4f78"
    )


def test_ready_grouped_bar_writes_nonempty_png(tmp_path: Path) -> None:
    source = tmp_path / "result.json"
    source.write_text('{"status":"pass"}\n', encoding="utf-8")
    spec = {
        "status": "ready",
        "inputs": [
            {
                "path": "result.json",
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            }
        ],
        "plot": {
            "type": "grouped_bar",
            "title": "Fixture",
            "xlabel": "Arm",
            "ylabel": "Accuracy",
            "labels": ["A1", "A2"],
            "series": [{"label": "post", "values": [0.5, 0.3]}],
        },
    }
    output = tmp_path / "figure.png"

    build_figure(tmp_path, "fixture", spec, output)

    assert output.is_file()
    assert output.stat().st_size > 1000


def test_ready_audit_table_writes_nonempty_png(tmp_path: Path) -> None:
    source = tmp_path / "audit.json"
    source.write_text('{"status":"pass"}\n', encoding="utf-8")
    spec = {
        "status": "ready",
        "inputs": [
            {
                "path": "audit.json",
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            }
        ],
        "plot": {
            "type": "table",
            "title": "Audit evidence",
            "columns": ["Audit", "Result"],
            "rows": [["parser", "pass"], ["human", "60/60"]],
        },
    }
    output = tmp_path / "audit-table.png"

    build_figure(tmp_path, "audits", spec, output)

    assert output.is_file()
    assert output.stat().st_size > 1000


def test_audit_table_rejects_ragged_rows(tmp_path: Path) -> None:
    source = tmp_path / "audit.json"
    source.write_text('{"status":"pass"}\n', encoding="utf-8")
    spec = {
        "status": "ready",
        "inputs": [
            {
                "path": "audit.json",
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            }
        ],
        "plot": {
            "type": "table",
            "title": "Invalid",
            "columns": ["Audit", "Result"],
            "rows": [["parser"]],
        },
    }

    with pytest.raises(ValueError, match="row length"):
        build_figure(tmp_path, "audits", spec, tmp_path / "invalid.png")
