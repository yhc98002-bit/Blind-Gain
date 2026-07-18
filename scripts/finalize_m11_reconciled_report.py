#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from scripts.build_generalization_audits import (
    build_payload,
    render_markdown,
)


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_JOB_TYPES = frozenset(
    {
        "m11_generalization_reconciled_backfill_queue",
        "m11_generalization_reconciled_backfill_queue_v2",
    }
)
EXPECTED_STATE = "cells_complete_pending_report"


def _load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve(value: str | Path, root: Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def _publish_pair(machine: Path, machine_content: str, markdown: Path, markdown_content: str) -> None:
    if machine.exists() or markdown.exists():
        raise FileExistsError("refusing to overwrite registered M11 report outputs")
    machine.parent.mkdir(parents=True, exist_ok=True)
    markdown.parent.mkdir(parents=True, exist_ok=True)
    temporary = {
        machine: machine.with_name(f".{machine.name}.partial.{os.getpid()}"),
        markdown: markdown.with_name(f".{markdown.name}.partial.{os.getpid()}"),
    }
    published: list[Path] = []
    try:
        for final, content in (
            (machine, machine_content),
            (markdown, markdown_content),
        ):
            with temporary[final].open("x", encoding="utf-8") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
        for final in (machine, markdown):
            os.replace(temporary[final], final)
            published.append(final)
    except BaseException:
        for final in published:
            final.unlink(missing_ok=True)
        for temp in temporary.values():
            temp.unlink(missing_ok=True)
        raise


def validate_queue_gate(
    queue_run: Path,
    *,
    root: Path = ROOT,
) -> tuple[dict[str, Any], dict[str, Any], list[Path], list[Path]]:
    run = _resolve(queue_run, root)
    runs_root = (root / "experiments/runs").resolve()
    if run.parent != runs_root or run.is_symlink():
        raise ValueError("M11 queue must be an immutable direct child of experiments/runs")
    manifest_path = run / "run_manifest.json"
    state_path = run / "queue_state.json"
    if (
        not manifest_path.is_file()
        or manifest_path.is_symlink()
        or not state_path.is_file()
        or state_path.is_symlink()
    ):
        raise ValueError("M11 queue manifest/state is absent or symbolic")
    manifest = _load_object(manifest_path)
    state = _load_object(state_path)
    if (
        manifest.get("job_type") not in EXPECTED_JOB_TYPES
        or manifest.get("status") != "complete"
        or manifest.get("exit_code") != 0
    ):
        raise ValueError("M11 queue run is not complete with exit code zero")
    registered = {_resolve(value, root) for value in manifest.get("expected_artifacts", [])}
    if state_path.resolve() not in registered:
        raise ValueError("M11 queue state is not a registered queue artifact")
    if state.get("status") != EXPECTED_STATE:
        raise ValueError(f"M11 queue state is not {EXPECTED_STATE}")
    if state.get("performance_values_opened") is not False:
        raise ValueError("M11 queue did not preserve the no-early-read contract")
    cells = state.get("cells")
    if not isinstance(cells, dict) or len(cells) != 18:
        raise ValueError("M11 queue must contain exactly 18 registered cells")
    if any(not isinstance(cell, dict) or cell.get("status") != "complete" for cell in cells.values()):
        raise ValueError("M11 queue contains a non-complete cell")

    fliptrack: list[Path] = []
    blind: list[Path] = []
    for cell_id, cell in sorted(cells.items()):
        metric_value = cell.get("metrics")
        if not isinstance(metric_value, str) or not metric_value:
            raise ValueError(f"M11 completed cell lacks a metric path: {cell_id}")
        metric = _resolve(metric_value, root)
        if metric.name != "metrics.json" or metric.parent.parent != runs_root:
            raise ValueError(f"M11 metric is outside an immutable run: {cell_id}")
        if metric.is_symlink() or not metric.is_file() or metric.stat().st_size == 0:
            raise ValueError(f"M11 metric is absent, symbolic, or empty: {cell_id}")
        kind = cell.get("kind")
        if kind == "fliptrack":
            fliptrack.append(metric)
        elif kind == "blind":
            blind.append(metric)
        else:
            raise ValueError(f"M11 cell has an unsupported kind: {cell_id}")
    if len(fliptrack) != 12 or len(blind) != 6:
        raise ValueError("M11 queue must expose the exact 12 FlipTrack and 6 blind metrics")
    return manifest, state, fliptrack, blind


def finalize_report(
    *,
    queue_run: Path,
    stage_manifests: list[Path],
    machine_output: Path,
    markdown_output: Path,
    root: Path = ROOT,
) -> dict[str, Any]:
    manifest, state, fliptrack, blind = validate_queue_gate(queue_run, root=root)
    machine = _resolve(machine_output, root)
    markdown = _resolve(markdown_output, root)
    if machine.exists() or markdown.exists():
        raise FileExistsError("refusing to overwrite registered M11 report outputs")
    stages = [_resolve(path, root) for path in stage_manifests]
    if not stages:
        raise ValueError("at least one model-stage manifest is required")
    payload = build_payload(fliptrack, blind, stages)
    if payload.get("status") != "pass":
        raise ValueError(f"M11 evidence conjunction failed: {payload.get('errors')}")
    queue_path = _resolve(queue_run, root)
    payload["queue_provenance"] = {
        "run": str(queue_path.relative_to(root)),
        "run_manifest_sha256": _sha256(queue_path / "run_manifest.json"),
        "queue_state_sha256": _sha256(queue_path / "queue_state.json"),
        "queue_git_hash": manifest.get("git_hash"),
        "cell_count": len(state["cells"]),
        "performance_values_opened_only_after_complete_queue_gate": True,
    }
    _publish_pair(
        machine,
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        markdown,
        render_markdown(payload, machine_output),
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue-run", type=Path, required=True)
    parser.add_argument("--model-stage-manifest", type=Path, action="append", default=[])
    parser.add_argument("--machine-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    if args.preflight_only:
        _, state, fliptrack, blind = validate_queue_gate(args.queue_run)
        print(
            json.dumps(
                {
                    "status": "pass",
                    "cells": len(state["cells"]),
                    "fliptrack_metrics": len(fliptrack),
                    "blind_metrics": len(blind),
                    "performance_values_opened": False,
                },
                sort_keys=True,
            )
        )
        return
    if args.machine_output is None or args.markdown_output is None:
        raise ValueError("machine and Markdown outputs are required")
    payload = finalize_report(
        queue_run=args.queue_run,
        stage_manifests=args.model_stage_manifest,
        machine_output=args.machine_output,
        markdown_output=args.markdown_output,
    )
    print(json.dumps({"status": payload["status"], "errors": payload["errors"]}))


if __name__ == "__main__":
    main()
