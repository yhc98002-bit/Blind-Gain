from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.select_fliptrack_templates import select_templates, sha256_file


def _write_jsonl(path: Path, rows: list[dict[str, str]]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_selector_hash_locks_sources_and_exact_template_counts(tmp_path: Path) -> None:
    source = tmp_path / "source.jsonl"
    _write_jsonl(
        source,
        [
            {"pair_id": "p2", "template_id": "keep"},
            {"pair_id": "p1", "template_id": "keep"},
            {"pair_id": "p3", "template_id": "drop"},
        ],
    )
    config = tmp_path / "selection.json"
    config.write_text(
        json.dumps(
            {
                "schema_version": "test",
                "expected_total_pairs": 2,
                "sources": [{"path": str(source), "sha256": sha256_file(source), "templates": {"keep": 2}}],
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "selected.jsonl"
    summary = select_templates(config, output, tmp_path / "summary.json")
    assert summary["n_pairs"] == 2
    assert [json.loads(line)["pair_id"] for line in output.read_text().splitlines()] == ["p1", "p2"]


def test_selector_rejects_source_drift(tmp_path: Path) -> None:
    source = tmp_path / "source.jsonl"
    _write_jsonl(source, [{"pair_id": "p1", "template_id": "keep"}])
    config = tmp_path / "selection.json"
    config.write_text(
        json.dumps(
            {
                "schema_version": "test",
                "expected_total_pairs": 1,
                "sources": [{"path": str(source), "sha256": "0" * 64, "templates": {"keep": 1}}],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="source hash mismatch"):
        select_templates(config, tmp_path / "selected.jsonl", tmp_path / "summary.json")
