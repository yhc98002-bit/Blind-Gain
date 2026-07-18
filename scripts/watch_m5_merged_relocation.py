#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

from scripts.watch_anchor_checkpoints import (
    merged_checkpoint_complete,
    relocate_merged,
)


ROOT = Path(__file__).resolve().parents[1]
INTERMEDIATE_STEPS = (150, 200, 250, 300, 350)
EVALUATED_STEPS = (150, 200, 300)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def valid_evaluation_marker(marker: Path, *, step: int, actor_dir: Path) -> bool:
    if not marker.is_file():
        return False
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    index = actor_dir / "huggingface/model.safetensors.index.json"
    return bool(
        index.is_file()
        and payload.get("schema_version") == "blind-gains.m5-step-eval-marker.v1"
        and payload.get("status") == "complete"
        and payload.get("global_step") == step
        and Path(str(payload.get("checkpoint_path", ""))).resolve()
        == (actor_dir / "huggingface").resolve()
        and payload.get("checkpoint_index_sha256") == _sha256(index)
        and payload.get("geo3k_status") == "complete"
        and payload.get("r19_status") == "complete"
    )


def wait_for_merge(actor_dir: Path, poll_seconds: int) -> None:
    while not merged_checkpoint_complete(actor_dir / "huggingface"):
        time.sleep(poll_seconds)


def wait_for_evaluation(marker: Path, *, step: int, actor_dir: Path, poll_seconds: int) -> None:
    while not valid_evaluation_marker(marker, step=step, actor_dir=actor_dir):
        time.sleep(poll_seconds)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--run-label", required=True)
    parser.add_argument("--evaluation-marker-dir", type=Path, required=True)
    parser.add_argument("--poll-seconds", type=int, default=60)
    parser.add_argument("--resume-after-step", type=int, default=0)
    args = parser.parse_args()
    if args.poll_seconds < 10:
        raise ValueError("poll interval must be at least 10 seconds")
    if args.resume_after_step not in {0, 100, 150}:
        raise ValueError("M5 resume-after step must be 0, 100, or 150")

    for step in (item for item in INTERMEDIATE_STEPS if item > args.resume_after_step):
        actor_dir = args.run_root / f"global_step_{step}" / "actor"
        wait_for_merge(actor_dir, args.poll_seconds)
        if step in EVALUATED_STEPS:
            marker = args.evaluation_marker_dir / f"step{step}_evaluation_complete.json"
            wait_for_evaluation(
                marker,
                step=step,
                actor_dir=actor_dir,
                poll_seconds=args.poll_seconds,
            )
        relocate_merged(
            actor_dir,
            args.archive_root,
            step,
            scope="m5_longhorizon",
            run_label=args.run_label,
        )


if __name__ == "__main__":
    main()
