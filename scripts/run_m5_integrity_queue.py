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


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def gpu_observations(node: str) -> dict[int, tuple[int, int]]:
    command = [
        "ssh",
        node,
        "nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader,nounits",
    ]
    output = subprocess.run(command, check=True, text=True, capture_output=True).stdout
    result: dict[int, tuple[int, int]] = {}
    for line in output.splitlines():
        index, memory, utilization = (int(value.strip()) for value in line.split(","))
        result[index] = (memory, utilization)
    if set(result) != set(range(8)):
        raise RuntimeError(f"incomplete GPU inventory from {node}")
    return result


def wait_for_capacity(
    nodes: list[str], state: dict[str, Any], state_path: Path, poll_seconds: int
) -> tuple[str, list[int]]:
    streaks = {node: {gpu: 0 for gpu in range(8)} for node in nodes}
    while True:
        snapshots: dict[str, Any] = {}
        for node in nodes:
            observed = gpu_observations(node)
            snapshots[node] = {
                str(gpu): {"memory_mib": values[0], "utilization_pct": values[1]}
                for gpu, values in observed.items()
            }
            for gpu, (memory, utilization) in observed.items():
                streaks[node][gpu] = (
                    streaks[node][gpu] + 1
                    if memory <= 1024 and utilization <= 10
                    else 0
                )
            stable = [gpu for gpu in range(8) if streaks[node][gpu] >= 2]
            if len(stable) >= 4:
                selected = stable[:4]
                state.update(
                    {
                        "status": "capacity_acquired",
                        "selected_node": node,
                        "selected_gpus": selected,
                        "last_gpu_observations": snapshots,
                        "updated_utc": utc_now(),
                    }
                )
                atomic_json(state_path, state)
                return node, selected
        state.update(
            {
                "status": "waiting_for_four_stable_free_gpus",
                "last_gpu_observations": snapshots,
                "free_streaks": streaks,
                "poll_count": int(state.get("poll_count", 0)) + 1,
                "updated_utc": utc_now(),
            }
        )
        atomic_json(state_path, state)
        time.sleep(poll_seconds)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--restore-run", required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--poll-seconds", type=int, default=60)
    args = parser.parse_args()
    run_dir = args.run_dir if args.run_dir.is_absolute() else ROOT / args.run_dir
    state_path = run_dir / "queue_state.json"
    if state_path.exists():
        raise FileExistsError(f"refusing existing queue state: {state_path}")
    state: dict[str, Any] = {
        "schema_version": "blind-gains.m5-integrity-queue-state.v1",
        "status": "waiting_for_restore",
        "created_utc": utc_now(),
        "restore_run": args.restore_run,
        "poll_count": 0,
        "scientific_gate_decision": None,
    }
    atomic_json(state_path, state)

    restore_manifest = ROOT / args.restore_run / "run_manifest.json"
    while True:
        manifest = json.loads(restore_manifest.read_text(encoding="utf-8"))
        if manifest.get("status") == "complete":
            break
        if manifest.get("status") in {"fail", "blocked"}:
            raise RuntimeError("M5 raw restore did not complete")
        time.sleep(args.poll_seconds)

    node, gpus = wait_for_capacity(
        ["an12", "an29"], state, state_path, args.poll_seconds
    )
    launch = subprocess.run(
        [
            "bash",
            "scripts/launch_m5_anchor_integrity.sh",
            node,
            ",".join(str(gpu) for gpu in gpus),
            args.restore_run,
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    child_run = launch.stdout.strip().splitlines()[-1]
    child_manifest_path = ROOT / child_run / "run_manifest.json"
    state.update(
        {
            "status": "integrity_running",
            "child_run": child_run,
            "updated_utc": utc_now(),
        }
    )
    atomic_json(state_path, state)
    while True:
        child = json.loads(child_manifest_path.read_text(encoding="utf-8"))
        if child.get("status") == "complete":
            break
        if child.get("status") in {"fail", "blocked"}:
            raise RuntimeError("M5 step-101 integrity child failed")
        time.sleep(args.poll_seconds)

    checkpoint = ROOT / "checkpoints/m5_anchor_resume_integrity_step101/global_step_101"
    checkpoint_audit = run_dir / "step101_checkpoint_audit.json"
    checkpoint_sha = run_dir / "step101_checkpoint.sha256"
    subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            "scripts/audit_easyr1_resume_checkpoint.py",
            "--checkpoint-dir",
            str(checkpoint),
            "--expected-step",
            "101",
            "--expected-world-size",
            "4",
            "--output-json",
            str(checkpoint_audit),
            "--output-sha256",
            str(checkpoint_sha),
        ],
        cwd=ROOT,
        check=True,
    )
    restore_audit = ROOT / args.restore_run / "restored_checkpoint_audit.json"
    subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            "scripts/audit_m5_resume_integrity.py",
            "--base-config",
            "configs/train/anchor_a0_recipe_3b_geo3k.yaml",
            "--integrity-config",
            "configs/train/m5_anchor_resume_integrity_step101.yaml",
            "--longhorizon-config",
            "configs/train/m5_anchor_longhorizon_400.yaml",
            "--relocation-marker",
            (
                "checkpoints/anchor_a0_recipe_3b_geo3k/"
                "anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_100/actor/"
                "RAW_STATE_RELOCATED.json"
            ),
            "--restored-checkpoint-audit",
            str(restore_audit),
            "--integrity-run-manifest",
            str(child_manifest_path),
            "--source-metrics",
            (
                "checkpoints/anchor_a0_recipe_3b_geo3k/"
                "anchor_a0_recipe_3b_geo3k_20260709T224852Z/experiment_log.jsonl"
            ),
            "--integrity-metrics",
            "checkpoints/m5_anchor_resume_integrity_step101/experiment_log.jsonl",
            "--step101-checkpoint-audit",
            str(checkpoint_audit),
            "--json-output",
            "reports/m5_restore_resume_integrity.json",
            "--markdown-output",
            "reports/m5_restore_resume_integrity.md",
        ],
        cwd=ROOT,
        check=True,
    )
    state.update(
        {
            "status": "complete",
            "integrity_report": "reports/m5_restore_resume_integrity.json",
            "updated_utc": utc_now(),
        }
    )
    atomic_json(state_path, state)


if __name__ == "__main__":
    main()
