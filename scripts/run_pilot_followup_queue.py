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
ARMS = ("a1_real", "a2_gray", "a2b_noimage", "a3_caption")


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def node_snapshot(node: str) -> dict[str, Any]:
    output = subprocess.run(
        ["ssh", node, "nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader,nounits"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout
    gpus = {}
    for line in output.splitlines():
        index, memory, utilization = (int(value.strip()) for value in line.split(","))
        gpus[index] = {"memory_mib": memory, "utilization_pct": utilization}
    trainer = subprocess.run(
        ["ssh", node, "pgrep -af '[p]ython.*verl.trainer.main.*BlindGain'"],
        text=True,
        capture_output=True,
    ).returncode == 0
    return {"project_trainer_active": trainer, "gpus": gpus}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, choices=(2, 3), required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--m5-queue-state", type=Path, required=True)
    parser.add_argument("--poll-seconds", type=int, default=60)
    args = parser.parse_args()
    state_path = args.run_dir / "queue_state.json"
    if state_path.exists():
        raise FileExistsError(state_path)
    records = {arm: {"status": "pending", "training_run": None} for arm in ARMS}
    state: dict[str, Any] = {
        "schema_version": "blind-gains.pilot-followup-queue.v1",
        "status": "waiting_for_m5_launch",
        "seed": args.seed,
        "arms": records,
        "created_utc": _now(),
        "performance_values_opened": False,
        "scientific_gate_decision": None,
    }
    _write(state_path, state)

    while True:
        if args.m5_queue_state.is_file() and _read(args.m5_queue_state).get("status") == "launched":
            break
        time.sleep(args.poll_seconds)

    streaks = {node: {gpu: 0 for gpu in range(8)} for node in ("an12", "an29")}
    while True:
        for arm, record in records.items():
            if record["status"] != "running":
                continue
            manifest = ROOT / str(record["training_run"]) / "run_manifest.json"
            if not manifest.is_file():
                continue
            status = _read(manifest).get("status")
            if status == "complete":
                record["status"] = "training_complete_pending_evaluation"
            elif status in {"fail", "failed", "error", "blocked"}:
                record["status"] = "failed"
                state.update({"status": "failed", "failed_arm": arm, "updated_utc": _now()})
                _write(state_path, state)
                raise RuntimeError(f"follow-up pilot arm failed: {arm}")

        if all(record["status"] == "training_complete_pending_evaluation" for record in records.values()):
            state.update({"status": "training_complete_pending_registered_evaluations", "updated_utc": _now()})
            _write(state_path, state)
            return

        snapshots = {node: node_snapshot(node) for node in ("an12", "an29")}
        for node, snapshot in snapshots.items():
            for gpu, values in snapshot["gpus"].items():
                free = not snapshot["project_trainer_active"] and values["memory_mib"] <= 1024 and values["utilization_pct"] <= 10
                streaks[node][gpu] = streaks[node][gpu] + 1 if free else 0

        pending = [arm for arm in ARMS if records[arm]["status"] == "pending"]
        for node in ("an12", "an29"):
            if not pending or snapshots[node]["project_trainer_active"]:
                continue
            stable = [gpu for gpu in range(8) if streaks[node][gpu] >= 2]
            if len(stable) < 4:
                continue
            arm = pending.pop(0)
            gpus = stable[:4]
            launch = subprocess.run(
                ["bash", "scripts/launch_mech_pilot_followup_arm.sh", str(args.seed), arm, node, ",".join(map(str, gpus))],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            if launch.returncode in {74, 75, 76}:
                continue
            if launch.returncode != 0:
                raise RuntimeError(f"seed-{args.seed} {arm} launch failed ({launch.returncode}): {launch.stderr.strip()}")
            runs = [line.strip() for line in launch.stdout.splitlines() if line.startswith("experiments/runs/mech_")]
            if len(runs) != 1:
                raise RuntimeError(f"ambiguous follow-up launch output: {launch.stdout!r}")
            records[arm].update({"status": "running", "training_run": runs[0], "node": node, "gpu_ids": gpus, "launched_utc": _now()})

        state.update({
            "status": "running" if any(record["status"] == "running" for record in records.values()) else "waiting_for_capacity",
            "arms": records,
            "node_snapshots": snapshots,
            "free_streaks": streaks,
            "updated_utc": _now(),
        })
        _write(state_path, state)
        time.sleep(args.poll_seconds)


if __name__ == "__main__":
    main()
