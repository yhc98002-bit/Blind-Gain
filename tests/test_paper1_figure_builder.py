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
