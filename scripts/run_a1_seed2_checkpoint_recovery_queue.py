#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.partial")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def a3_ready(manifest: dict[str, Any], checkpoint_root: Path) -> bool:
    return bool(
        manifest.get("status") == "complete"
        and manifest.get("exit_code") == 0
        and manifest.get("artifacts_exist") is True
        and (checkpoint_root / "global_step_100/actor/huggingface/model.safetensors.index.json").is_file()
        and (checkpoint_root / "global_step_100/actor/RAW_STATE_RELOCATED.json").is_file()
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--a3-run", type=Path, required=True)
    parser.add_argument("--a1-run", type=Path, required=True)
    parser.add_argument("--failed-watcher-run", type=Path, required=True)
    parser.add_argument("--poll-seconds", type=int, default=60)
    args = parser.parse_args()
    if args.poll_seconds < 10:
        raise ValueError("poll interval must be >= 10 seconds")
    state_path = args.run_dir / "queue_state.json"
    if state_path.exists():
        raise FileExistsError(state_path)
    state: dict[str, Any] = {
        "schema_version": "blind-gains.a1-seed2-checkpoint-recovery-queue.v1",
        "status": "waiting_for_a3_checkpoint_finalization",
        "created_utc": now(),
        "performance_values_opened": False,
    }
    write_json(state_path, state)
    a3_manifest_path = args.a3_run / "run_manifest.json"
    a3_manifest = read_json(a3_manifest_path)
    checkpoint_root = Path(str(a3_manifest["checkpoint_path"]))
    while not a3_ready(a3_manifest, checkpoint_root):
        if a3_manifest.get("status") in {"fail", "failed", "error", "blocked"}:
            raise RuntimeError("A3 failed; A1 recovery queue remains fail-closed")
        state.update({"updated_utc": now(), "a3_status": a3_manifest.get("status")})
        write_json(state_path, state)
        time.sleep(args.poll_seconds)
        a3_manifest = read_json(a3_manifest_path)

    free_streak = 0
    state["status"] = "waiting_for_an29_trainer_release"
    while free_streak < 2:
        trainer = subprocess.run(
            ["ssh", "an29", "pgrep -af '[p]ython.*verl.trainer.main.*BlindGain'"],
            text=True,
            capture_output=True,
        )
        free_streak = free_streak + 1 if trainer.returncode != 0 else 0
        state.update({"updated_utc": now(), "trainer_free_streak": free_streak})
        write_json(state_path, state)
        if free_streak < 2:
            time.sleep(args.poll_seconds)

    launch = subprocess.run(
        [
            "bash",
            "scripts/launch_pilot_completed_checkpoint_recovery.sh",
            "an29",
            str(args.a1_run),
            str(args.failed_watcher_run),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if launch.returncode != 0:
        raise RuntimeError(f"A1 checkpoint recovery launch failed: {launch.stderr.strip()}")
    runs = [line for line in launch.stdout.splitlines() if line.startswith("experiments/runs/")]
    if len(runs) != 1:
        raise RuntimeError(f"ambiguous recovery launch output: {launch.stdout!r}")
    state.update({"status": "launched", "updated_utc": now(), "recovery_run": runs[0]})
    write_json(state_path, state)


if __name__ == "__main__":
    main()
