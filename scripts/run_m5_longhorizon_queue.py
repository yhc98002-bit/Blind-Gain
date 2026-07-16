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


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def observations(node: str) -> tuple[dict[int, tuple[int, int]], bool]:
    command = "nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader,nounits"
    output = subprocess.run(["ssh", node, command], check=True, text=True, capture_output=True).stdout
    gpus = {}
    for line in output.splitlines():
        index, memory, utilization = (int(value.strip()) for value in line.split(","))
        gpus[index] = (memory, utilization)
    trainer = subprocess.run(
        ["ssh", node, "pgrep -af '[p]ython.*verl.trainer.main.*BlindGain'"],
        text=True,
        capture_output=True,
    ).returncode == 0
    return gpus, trainer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--poll-seconds", type=int, default=60)
    args = parser.parse_args()
    state_path = args.run_dir / "queue_state.json"
    if state_path.exists():
        raise FileExistsError(state_path)
    state: dict[str, Any] = {
        "schema_version": "blind-gains.m5-longhorizon-queue.v1",
        "status": "waiting_for_integrity",
        "created_utc": _now(),
        "scientific_gate_decision": None,
    }
    _write(state_path, state)

    integrity = ROOT / "reports/m5_restore_resume_integrity.json"
    while True:
        if integrity.is_file():
            payload = json.loads(integrity.read_text(encoding="utf-8"))
            if payload.get("status") == "fail":
                raise RuntimeError("M5 restore integrity failed")
            if payload.get("status") == "pass" and all(payload.get("checks", {}).values()):
                break
        time.sleep(args.poll_seconds)

    streaks = {node: {gpu: 0 for gpu in range(8)} for node in ("an12", "an29")}
    while True:
        snapshots: dict[str, Any] = {}
        selected: tuple[str, list[int]] | None = None
        for node in ("an12", "an29"):
            gpus, trainer = observations(node)
            snapshots[node] = {
                "project_trainer_active": trainer,
                "gpus": {str(gpu): {"memory_mib": values[0], "utilization_pct": values[1]} for gpu, values in gpus.items()},
            }
            for gpu, (memory, utilization) in gpus.items():
                streaks[node][gpu] = streaks[node][gpu] + 1 if not trainer and memory <= 1024 and utilization <= 10 else 0
            stable = [gpu for gpu in range(8) if streaks[node][gpu] >= 2]
            if len(stable) >= 4:
                selected = (node, stable[:4])
                break
        state.update({"status": "waiting_for_four_stable_free_gpus", "updated_utc": _now(), "snapshots": snapshots, "free_streaks": streaks})
        _write(state_path, state)
        if selected is None:
            time.sleep(args.poll_seconds)
            continue
        node, gpus = selected
        launch = subprocess.run(
            ["bash", "scripts/launch_m5_anchor_longhorizon.sh", node, ",".join(map(str, gpus))],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        if launch.returncode in {74, 75, 76}:
            state.update({"status": "capacity_race_retry", "last_launch_stderr": launch.stderr.strip(), "updated_utc": _now()})
            _write(state_path, state)
            time.sleep(args.poll_seconds)
            continue
        if launch.returncode != 0:
            raise RuntimeError(f"M5 launch failed ({launch.returncode}): {launch.stderr.strip()}")
        runs = [line.strip() for line in launch.stdout.splitlines() if line.startswith("experiments/runs/m5_anchor_longhorizon_400_")]
        if len(runs) != 1:
            raise RuntimeError(f"ambiguous M5 launch output: {launch.stdout!r}")
        state.update({"status": "launched", "training_run": runs[0], "node": node, "gpu_ids": gpus, "updated_utc": _now()})
        _write(state_path, state)
        return


if __name__ == "__main__":
    main()
