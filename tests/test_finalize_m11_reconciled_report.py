from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from scripts.finalize_m11_reconciled_report import _publish_pair, validate_queue_gate


def _queue_fixture(tmp_path: Path, *, status: str) -> tuple[Path, list[Path]]:
    run = tmp_path / "experiments/runs/queue"
    run.mkdir(parents=True)
    cells = {}
    metrics = []
    for index in range(18):
        metric_run = tmp_path / f"experiments/runs/metric-{index}"
        metric_run.mkdir()
        metric = metric_run / "metrics.json"
        metric.write_text('{"private_value":0.5}\n', encoding="utf-8")
        metrics.append(metric)
        cells[f"cell-{index}"] = {
            "status": "complete" if status == "cells_complete_pending_report" else "running",
            "kind": "fliptrack" if index < 12 else "blind",
            "metrics": str(metric.relative_to(tmp_path)),
        }
    state = run / "queue_state.json"
    state.write_text(
        json.dumps(
            {
                "status": status,
                "performance_values_opened": False,
                "cells": cells,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (run / "run_manifest.json").write_text(
        json.dumps(
            {
                "job_type": "m11_generalization_reconciled_backfill_queue",
                "status": "complete" if status == "cells_complete_pending_report" else "running",
                "exit_code": 0 if status == "cells_complete_pending_report" else None,
                "expected_artifacts": [str(state.relative_to(tmp_path))],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return run, metrics


def test_incomplete_queue_is_rejected_before_any_metric_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run, metrics = _queue_fixture(tmp_path, status="running")
    original = Path.read_text

    def guarded_read(path: Path, *args, **kwargs):
        if path in metrics:
            raise AssertionError("metric value opened before the complete queue gate")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded_read)
    with pytest.raises(ValueError, match="queue run is not complete"):
        validate_queue_gate(run, root=tmp_path)


def test_complete_queue_exposes_exact_registered_metric_matrix(tmp_path: Path) -> None:
    run, _ = _queue_fixture(tmp_path, status="cells_complete_pending_report")

    _, state, fliptrack, blind = validate_queue_gate(run, root=tmp_path)

    assert len(state["cells"]) == 18
    assert len(fliptrack) == 12
    assert len(blind) == 6


def test_finalizer_launcher_is_cpu_only_and_commit_bound() -> None:
    root = Path(__file__).resolve().parents[1]
    source = (root / "scripts/launch_m11_reconciled_report.sh").read_text(
        encoding="utf-8"
    )

    assert 'job_type: "m11_reconciled_final_report"' in source
    assert 'node: "login"' in source
    assert "--preflight-only" in source
    assert "critical M11 final-report code differs from HEAD" in source
    assert "storage_guard.py --tier S" in source


def test_paired_publication_rolls_back_when_second_rename_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    machine = tmp_path / "result.json"
    markdown = tmp_path / "result.md"
    original = os.replace
    calls = 0

    def fail_second(source: Path, destination: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated Markdown publication failure")
        original(source, destination)

    monkeypatch.setattr(os, "replace", fail_second)
    with pytest.raises(OSError, match="simulated Markdown"):
        _publish_pair(machine, "{}\n", markdown, "# report\n")

    assert not machine.exists()
    assert not markdown.exists()
    assert not list(tmp_path.glob(".*.partial.*"))
