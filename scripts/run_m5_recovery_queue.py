#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def utc_text() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def node_snapshot(node: str, gpu_ids: list[int]) -> dict[str, Any]:
    query = subprocess.run(
        [
            "ssh",
            node,
            "nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader,nounits; "
            "grep '^MemAvailable:' /proc/meminfo | tr -cd '0-9'; echo; "
            "pgrep -af '[p]ython.*verl.trainer.main.*BlindGain' || true",
        ],
        check=True,
        text=True,
        capture_output=True,
    ).stdout.splitlines()
    gpu_rows = snapshot_gpu_rows(query[:8])
    try:
        mem_available_kib = int(query[8])
    except (IndexError, ValueError) as error:
        raise RuntimeError(f"could not parse {node} host memory") from error
    trainers = query[9:]
    selected = {gpu: gpu_rows[gpu] for gpu in gpu_ids}
    return {
        "node": node,
        "selected_gpus": selected,
        "mem_available_kib": mem_available_kib,
        "project_trainers": trainers,
        "selected_gpus_free": all(
            row["memory_mib"] <= 1024 and row["utilization_pct"] <= 10
            for row in selected.values()
        ),
        "host_memory_sufficient": mem_available_kib >= 681574400,
        "project_trainer_absent": not trainers,
    }


def snapshot_gpu_rows(lines: list[str]) -> dict[int, dict[str, int]]:
    if len(lines) != 8:
        raise RuntimeError(f"expected eight GPU rows, found {len(lines)}")
    rows: dict[int, dict[str, int]] = {}
    for line in lines:
        values = [int(value.strip()) for value in line.split(",")]
        if len(values) != 3:
            raise RuntimeError(f"malformed GPU row: {line!r}")
        index, memory, utilization = values
        rows[index] = {"memory_mib": memory, "utilization_pct": utilization}
    if set(rows) != set(range(8)):
        raise RuntimeError("GPU index set is not 0..7")
    return rows


def resume_seed_queue(hold_path: Path, output_path: Path) -> dict[str, Any]:
    hold = read_json(hold_path)
    pid = int(hold["pid"])
    expected = "scripts/run_pilot_followup_queue.py --seed 2"
    proc_cmdline = Path(f"/proc/{pid}/cmdline")
    if not proc_cmdline.is_file():
        result = {"status": "queue_process_absent", "pid": pid, "resumed": False}
    else:
        command = proc_cmdline.read_bytes().replace(b"\0", b" ").decode("utf-8")
        if expected not in command:
            raise RuntimeError("operational-hold PID no longer identifies the seed-2 queue")
        os.kill(pid, signal.SIGCONT)
        result = {
            "status": "resumed",
            "pid": pid,
            "resumed": True,
            "command": command,
        }
    result.update(
        {
            "schema_version": "blind-gains.queue-operational-resume.v1",
            "created_utc": utc_text(),
            "source_hold": str(hold_path),
            "reason": "M5 recovery owns an29; the seed queue may continue monitoring without racing that node.",
            "performance_values_opened": False,
        }
    )
    if output_path.exists():
        raise FileExistsError(output_path)
    atomic_json(output_path, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--restore-run", type=Path, required=True)
    parser.add_argument("--a1-run", type=Path, required=True)
    parser.add_argument("--seed-queue-hold", type=Path, required=True)
    parser.add_argument("--node", choices=("an12", "an29"), default="an29")
    parser.add_argument("--gpu-ids", default="2,5,6,7")
    parser.add_argument("--poll-seconds", type=int, default=120)
    args = parser.parse_args()
    gpu_ids = [int(value) for value in args.gpu_ids.split(",")]
    if len(gpu_ids) != 4 or len(set(gpu_ids)) != 4 or any(not 0 <= value < 8 for value in gpu_ids):
        raise ValueError("M5 recovery queue requires four unique GPU ids")
    if args.poll_seconds < 30:
        raise ValueError("poll interval must be at least 30 seconds")
    state_path = args.run_dir / "queue_state.json"
    resume_record = args.run_dir / "seed2_queue_resume.json"
    if state_path.exists():
        raise FileExistsError(state_path)
    state: dict[str, Any] = {
        "schema_version": "blind-gains.m5-recovery-queue.v1",
        "status": "waiting_for_restore_and_a1",
        "created_utc": utc_text(),
        "restore_run": str(args.restore_run),
        "a1_run": str(args.a1_run),
        "node": args.node,
        "gpu_ids": gpu_ids,
        "stable_capacity_polls": 0,
        "performance_values_opened": False,
        "scientific_gate_decision": None,
    }
    atomic_json(state_path, state)

    stable_polls = 0
    while True:
        restore = read_json(args.restore_run / "run_manifest.json")
        a1 = read_json(args.a1_run / "run_manifest.json")
        if restore.get("status") in {"fail", "failed", "error", "blocked"}:
            raise RuntimeError("step-150 restore failed; M5 recovery remains blocked")
        if a1.get("status") in {"fail", "failed", "error", "blocked"}:
            raise RuntimeError("A1 seed-2 failed; M5 placement requires a fresh audit")

        prerequisites = {
            "restore_complete": restore.get("status") == "complete"
            and restore.get("exit_code") == 0,
            "a1_complete": a1.get("status") == "complete" and a1.get("exit_code") == 0,
        }
        snapshot: dict[str, Any] | None = None
        if all(prerequisites.values()):
            snapshot = node_snapshot(args.node, gpu_ids)
            capacity = (
                snapshot["selected_gpus_free"]
                and snapshot["host_memory_sufficient"]
                and snapshot["project_trainer_absent"]
            )
            stable_polls = stable_polls + 1 if capacity else 0
        else:
            stable_polls = 0

        state.update(
            {
                "status": "waiting_for_stable_capacity"
                if all(prerequisites.values())
                else "waiting_for_restore_and_a1",
                "updated_utc": utc_text(),
                "prerequisites": prerequisites,
                "node_snapshot": snapshot,
                "stable_capacity_polls": stable_polls,
            }
        )
        atomic_json(state_path, state)
        if stable_polls < 2:
            time.sleep(args.poll_seconds)
            continue

        launch = subprocess.run(
            [
                "bash",
                "scripts/launch_m5_anchor_recovery150.sh",
                args.node,
                ",".join(map(str, gpu_ids)),
                str(args.restore_run),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        if launch.returncode in {74, 75, 76}:
            stable_polls = 0
            state.update(
                {
                    "status": "launch_capacity_race_retry",
                    "updated_utc": utc_text(),
                    "launcher_exit_code": launch.returncode,
                    "launcher_stderr": launch.stderr.strip(),
                }
            )
            atomic_json(state_path, state)
            time.sleep(args.poll_seconds)
            continue
        if launch.returncode != 0:
            raise RuntimeError(
                f"M5 recovery launcher failed ({launch.returncode}): {launch.stderr.strip()}"
            )
        run_dirs = [
            line.strip()
            for line in launch.stdout.splitlines()
            if line.startswith("experiments/runs/m5_anchor_longhorizon_400_resume150_")
        ]
        if len(run_dirs) != 1:
            raise RuntimeError(f"ambiguous M5 recovery launch output: {launch.stdout!r}")
        seed_queue = resume_seed_queue(args.seed_queue_hold, resume_record)
        state.update(
            {
                "status": "launched",
                "updated_utc": utc_text(),
                "training_run": run_dirs[0],
                "launcher_stdout": launch.stdout.strip(),
                "seed2_queue_resume": seed_queue,
                "performance_values_opened": False,
            }
        )
        atomic_json(state_path, state)
        return


if __name__ == "__main__":
    main()
