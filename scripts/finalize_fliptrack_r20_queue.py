#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CELL_MAP = {
    "qwen25vl3b_real": "3b_real",
    "qwen25vl3b_gray": "3b_gray",
    "qwen25vl3b_noise": "3b_noise",
    "qwen25vl3b_caption": "3b_caption",
    "qwen25vl7b_real": "7b_real",
    "qwen25vl7b_gray": "7b_gray",
    "qwen25vl7b_noise": "7b_noise",
    "qwen25vl7b_caption": "7b_caption",
}
DEGRADATION_MAP = {
    "qwen25vl3b_mild": "mild",
    "qwen25vl3b_medium": "medium",
    "qwen25vl3b_severe": "severe",
}
EXPECTED_CELLS = set(CELL_MAP) | set(DEGRADATION_MAP)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = Path(f"{path}.partial")
    partial.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(partial, path)


def validate_queue_runs(
    root: Path, queue: dict[str, Any]
) -> tuple[dict[str, Path], dict[str, Path]]:
    if queue.get("status") != "complete":
        raise ValueError(f"R20 queue is not complete: {queue.get('status')}")
    cells = queue.get("cells")
    if not isinstance(cells, dict) or set(cells) != EXPECTED_CELLS:
        observed = set(cells) if isinstance(cells, dict) else set()
        raise ValueError(
            f"R20 queue cell mismatch: missing={sorted(EXPECTED_CELLS - observed)}, "
            f"extra={sorted(observed - EXPECTED_CELLS)}"
        )
    sources: dict[str, Path] = {}
    aggregates: dict[str, Path] = {}
    for cell_id, record in cells.items():
        if not isinstance(record, dict):
            raise ValueError(f"R20 queue cell record is invalid: {cell_id}")
        source = Path(str(record.get("run_dir", "")))
        aggregate = Path(str(record.get("aggregate_run", "")))
        source_manifest = root / source / "run_manifest.json"
        aggregate_manifest = root / aggregate / "run_manifest.json"
        if not source_manifest.is_file() or not aggregate_manifest.is_file():
            raise ValueError(f"R20 queue cell artifacts are missing: {cell_id}")
        source_payload = _read_json(source_manifest)
        aggregate_payload = _read_json(aggregate_manifest)
        if source_payload.get("status") != "complete":
            raise ValueError(f"R20 source run is not complete: {source}")
        if aggregate_payload.get("status") != "complete":
            raise ValueError(f"R20 aggregate run is not complete: {aggregate}")
        if Path(str(aggregate_payload.get("source_run", ""))) != source:
            raise ValueError(f"R20 aggregate/source mismatch for {cell_id}")
        sources[cell_id] = source
        aggregates[cell_id] = aggregate
    return sources, aggregates


def _launch_comparison(
    left: Path,
    right: Path,
    left_label: str,
    right_label: str,
    run_tag: str,
) -> Path:
    completed = subprocess.run(
        [
            "bash",
            "scripts/launch_fliptrack_compare.sh",
            str(left),
            str(right),
            left_label,
            right_label,
            run_tag,
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"comparison launcher returned no run directory: {run_tag}")
    run_dir = Path(lines[-1])
    manifest = _read_json(ROOT / run_dir / "run_manifest.json")
    if manifest.get("status") != "complete":
        raise RuntimeError(f"comparison run did not complete: {run_dir}")
    return run_dir


def _existing_comparison(state: dict[str, Any], key: str) -> Path | None:
    value = state.get(key)
    if not value:
        return None
    run_dir = Path(str(value))
    manifest_path = ROOT / run_dir / "run_manifest.json"
    if not manifest_path.is_file() or _read_json(manifest_path).get("status") != "complete":
        raise ValueError(f"recorded comparison is not complete: {run_dir}")
    return run_dir


def _wait_for_queue(queue_state: Path, poll_seconds: int) -> dict[str, Any]:
    while True:
        queue = _read_json(queue_state)
        status = queue.get("status")
        if status == "complete":
            return queue
        if status == "fail":
            raise RuntimeError(f"R20 scoring queue failed: {queue_state}")
        print(f"r20_finalize_wait queue_status={status}", flush=True)
        time.sleep(poll_seconds)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue-state", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--poll-seconds", type=int, default=60)
    parser.add_argument(
        "--release-manifest", type=Path, default=Path("data/fliptrack_r20/manifest.jsonl")
    )
    parser.add_argument(
        "--lint-json", type=Path, default=Path("reports/fliptrack_r20_lint.json")
    )
    parser.add_argument(
        "--attacker-json", type=Path, default=Path("reports/artifact_gate_r20.json")
    )
    parser.add_argument(
        "--output-json", type=Path, default=Path("reports/fliptrack_r20_confirmatory.json")
    )
    parser.add_argument(
        "--output-markdown", type=Path, default=Path("reports/fliptrack_r20_confirmatory.md")
    )
    args = parser.parse_args()
    if args.poll_seconds <= 0:
        raise ValueError("poll seconds must be positive")

    state = _read_json(args.state) if args.state.is_file() else {
        "schema_version": "blind-gains.fliptrack-r20-finalizer.v1",
        "status": "waiting",
        "queue_state": str(args.queue_state),
        "real_comparison_run": None,
        "caption_comparison_run": None,
    }
    if state.get("queue_state") != str(args.queue_state):
        raise ValueError("R20 finalizer state belongs to a different queue")
    if state.get("status") == "complete":
        for key, path in {
            "output_json_sha256": args.output_json,
            "output_markdown_sha256": args.output_markdown,
        }.items():
            if not path.is_file() or state.get(key) != _sha256(path):
                raise ValueError(f"completed R20 finalizer output drift: {path}")
        print(json.dumps(state, sort_keys=True))
        return
    _atomic_write(args.state, state)

    queue = _wait_for_queue(args.queue_state, args.poll_seconds)
    sources, aggregates = validate_queue_runs(ROOT, queue)
    state["status"] = "finalizing"
    state["queue_config_sha256"] = queue.get("config_sha256")
    _atomic_write(args.state, state)

    real_comparison = _existing_comparison(state, "real_comparison_run")
    if real_comparison is None:
        real_comparison = _launch_comparison(
            sources["qwen25vl3b_real"],
            sources["qwen25vl7b_real"],
            "3b_real",
            "7b_real",
            "r20_3b_vs_7b_real",
        )
        state["real_comparison_run"] = str(real_comparison)
        _atomic_write(args.state, state)

    caption_comparison = _existing_comparison(state, "caption_comparison_run")
    if caption_comparison is None:
        caption_comparison = _launch_comparison(
            sources["qwen25vl3b_caption"],
            sources["qwen25vl7b_caption"],
            "3b_caption",
            "7b_caption",
            "r20_3b_vs_7b_caption",
        )
        state["caption_comparison_run"] = str(caption_comparison)
        _atomic_write(args.state, state)

    if args.output_json.exists() or args.output_markdown.exists():
        raise FileExistsError("refusing to overwrite an existing R20 confirmatory report")
    command = [
        str(ROOT / ".venv" / "bin" / "python"),
        "scripts/build_fliptrack_r20_confirmatory.py",
    ]
    for cell_id, key in CELL_MAP.items():
        command.extend(["--cell", f"{key}={aggregates[cell_id]}"])
    for cell_id, key in DEGRADATION_MAP.items():
        command.extend(["--degradation", f"{key}={aggregates[cell_id]}"])
    command.extend(
        [
            "--real-comparison-run",
            str(real_comparison),
            "--caption-comparison-run",
            str(caption_comparison),
            "--release-manifest",
            str(args.release_manifest),
            "--lint-json",
            str(args.lint_json),
            "--attacker-json",
            str(args.attacker_json),
            "--output-json",
            str(args.output_json),
            "--output-markdown",
            str(args.output_markdown),
        ]
    )
    subprocess.run(command, cwd=ROOT, check=True)
    package = _read_json(args.output_json)
    if package.get("status") != "pass":
        raise RuntimeError(f"R20 confirmatory package status is not pass: {package.get('status')}")
    state.update(
        {
            "status": "complete",
            "output_json": str(args.output_json),
            "output_json_sha256": _sha256(args.output_json),
            "output_markdown": str(args.output_markdown),
            "output_markdown_sha256": _sha256(args.output_markdown),
        }
    )
    _atomic_write(args.state, state)
    print(json.dumps(state, sort_keys=True))


if __name__ == "__main__":
    main()
