from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.finalize_fliptrack_r20_queue import EXPECTED_CELLS, validate_queue_runs


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _complete_queue(root: Path) -> dict[str, object]:
    cells = {}
    for cell_id in sorted(EXPECTED_CELLS):
        source = Path("experiments/runs") / f"source_{cell_id}"
        aggregate = Path("experiments/runs") / f"aggregate_{cell_id}"
        _write_json(root / source / "run_manifest.json", {"status": "complete"})
        _write_json(
            root / aggregate / "run_manifest.json",
            {"status": "complete", "source_run": str(source)},
        )
        cells[cell_id] = {"run_dir": str(source), "aggregate_run": str(aggregate)}
    return {"status": "complete", "cells": cells}


def test_finalizer_validates_every_source_and_aggregate_identity(tmp_path: Path) -> None:
    queue = _complete_queue(tmp_path)

    sources, aggregates = validate_queue_runs(tmp_path, queue)

    assert set(sources) == EXPECTED_CELLS
    assert set(aggregates) == EXPECTED_CELLS


def test_finalizer_rejects_missing_registered_cell(tmp_path: Path) -> None:
    queue = _complete_queue(tmp_path)
    queue["cells"].pop("qwen25vl3b_severe")

    with pytest.raises(ValueError, match="cell mismatch"):
        validate_queue_runs(tmp_path, queue)


def test_finalizer_rejects_aggregate_from_different_source(tmp_path: Path) -> None:
    queue = _complete_queue(tmp_path)
    record = queue["cells"]["qwen25vl7b_real"]
    aggregate_manifest = tmp_path / record["aggregate_run"] / "run_manifest.json"
    _write_json(
        aggregate_manifest,
        {"status": "complete", "source_run": "experiments/runs/wrong_source"},
    )

    with pytest.raises(ValueError, match="aggregate/source mismatch"):
        validate_queue_runs(tmp_path, queue)
