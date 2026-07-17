#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARMS = ("a1_real", "a3_caption", "a2_gray", "a2b_noimage")


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _atomic(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def gpu_snapshot(node: str) -> dict[int, dict[str, int]]:
    result = subprocess.run(
        [
            "ssh",
            node,
            "nvidia-smi --query-gpu=index,memory.used,utilization.gpu "
            "--format=csv,noheader,nounits",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    snapshot: dict[int, dict[str, int]] = {}
    for line in result.stdout.splitlines():
        fields = [int(value.strip()) for value in line.split(",")]
        if len(fields) != 3:
            raise ValueError(f"malformed GPU row from {node}: {line!r}")
        snapshot[fields[0]] = {
            "memory_mib": fields[1],
            "utilization_pct": fields[2],
        }
    if set(snapshot) != set(range(8)):
        raise ValueError(f"{node} did not report exactly GPUs 0-7")
    return snapshot


def free_allowed_gpus(
    snapshot: dict[int, dict[str, int]], allowed: tuple[int, ...]
) -> list[int]:
    return [
        gpu
        for gpu in allowed
        if snapshot[gpu]["memory_mib"] <= 1024
        and snapshot[gpu]["utilization_pct"] <= 10
    ]


def _launch(node: str, gpu: int, arm: str) -> Path | None:
    result = subprocess.run(
        ["bash", "scripts/launch_support_sharpening_followup.sh", node, str(gpu), arm],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode == 75:
        return None
    if result.returncode != 0:
        raise RuntimeError(
            f"M10 launcher failed for {arm} on {node}:{gpu}, rc={result.returncode}: "
            f"stdout={result.stdout!r} stderr={result.stderr!r}"
        )
    candidates = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not candidates:
        raise RuntimeError(f"M10 launcher returned no run directory for {arm}")
    run_dir = ROOT / candidates[-1]
    if not (run_dir / "run_manifest.json").is_file():
        raise RuntimeError(f"M10 child manifest is absent: {run_dir}")
    return run_dir


def run_queue(
    run_dir: Path,
    *,
    node: str,
    allowed_gpus: tuple[int, ...],
    poll_seconds: int,
    stable_polls: int,
) -> int:
    state_path = run_dir / "queue_state.json"
    state: dict[str, Any] = {
        "schema_version": "blind-gains.support-sharpening-queue.v1",
        "status": "waiting_capacity",
        "created_utc": _utc(),
        "updated_utc": _utc(),
        "node": node,
        "allowed_gpu_ids": list(allowed_gpus),
        "placement_reason": (
            "Only an12 GPUs 5-6 are eligible after their existing M11 cells release; "
            "an29 remains reserved for seed 2 and M11 repair."
        ),
        "gpu_free_streaks": {str(gpu): 0 for gpu in allowed_gpus},
        "last_gpu_snapshot": {},
        "arms": {
            arm: {"status": "pending", "gpu": None, "run_dir": None}
            for arm in ARMS
        },
        "events": [],
        "performance_values_opened": False,
        "scientific_gate_decision": None,
    }
    _atomic(state_path, state)

    while True:
        for arm, record in state["arms"].items():
            if record["status"] != "running":
                continue
            child = _load(ROOT / str(record["run_dir"]) / "run_manifest.json")
            child_status = child.get("status")
            if child_status in {"complete", "fail"}:
                record["status"] = child_status
                state["events"].append(
                    {
                        "time_utc": _utc(),
                        "event": f"child_{child_status}",
                        "arm": arm,
                        "run_dir": record["run_dir"],
                    }
                )

        terminal = {record["status"] for record in state["arms"].values()}
        if terminal <= {"complete", "fail"}:
            state["status"] = "complete" if terminal == {"complete"} else "fail"
            state["updated_utc"] = _utc()
            _atomic(state_path, state)
            return 0 if state["status"] == "complete" else 3

        try:
            snapshot = gpu_snapshot(node)
            state["last_gpu_snapshot"] = snapshot
            observed_free = free_allowed_gpus(snapshot, allowed_gpus)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            state["last_gpu_snapshot"] = {"error": str(error)}
            observed_free = []
        running_gpus = {
            int(record["gpu"])
            for record in state["arms"].values()
            if record["status"] == "running" and record["gpu"] is not None
        }
        for gpu in allowed_gpus:
            if gpu in observed_free and gpu not in running_gpus:
                state["gpu_free_streaks"][str(gpu)] += 1
            else:
                state["gpu_free_streaks"][str(gpu)] = 0

        stable = [
            gpu
            for gpu in allowed_gpus
            if state["gpu_free_streaks"][str(gpu)] >= stable_polls
            and gpu not in running_gpus
        ]
        pending = [arm for arm in ARMS if state["arms"][arm]["status"] == "pending"]
        for arm, gpu in zip(pending, stable):
            launched = _launch(node, gpu, arm)
            state["gpu_free_streaks"][str(gpu)] = 0
            if launched is None:
                state["events"].append(
                    {
                        "time_utc": _utc(),
                        "event": "launch_race_retry",
                        "arm": arm,
                        "gpu": gpu,
                    }
                )
                continue
            state["arms"][arm] = {
                "status": "running",
                "gpu": gpu,
                "run_dir": str(launched.relative_to(ROOT)),
            }
            state["events"].append(
                {
                    "time_utc": _utc(),
                    "event": "child_launched",
                    "arm": arm,
                    "gpu": gpu,
                    "run_dir": str(launched.relative_to(ROOT)),
                }
            )
        state["status"] = (
            "running" if any(r["status"] == "running" for r in state["arms"].values())
            else "waiting_capacity"
        )
        state["updated_utc"] = _utc()
        _atomic(state_path, state)
        time.sleep(poll_seconds)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--node", default="an12", choices=("an12",))
    parser.add_argument("--allowed-gpus", default="5,6")
    parser.add_argument("--poll-seconds", type=int, default=60)
    parser.add_argument("--stable-polls", type=int, default=2)
    args = parser.parse_args()
    allowed = tuple(int(value) for value in args.allowed_gpus.split(","))
    if allowed != (5, 6):
        raise ValueError("registered M10 queue permits only an12 GPUs 5,6")
    if args.poll_seconds < 1 or args.stable_polls < 1:
        raise ValueError("poll interval and stable-poll count must be positive")
    raise SystemExit(
        run_queue(
            args.run_dir,
            node=args.node,
            allowed_gpus=allowed,
            poll_seconds=args.poll_seconds,
            stable_polls=args.stable_polls,
        )
    )


if __name__ == "__main__":
    main()
