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
NODES = ("an29", "an12")
TERMINAL_FAILURES = {"fail", "failed", "error", "blocked", "cancelled", "canceled"}


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def dependency_state(
    seed2_manifest: Path,
    m6_manifest: Path,
    m5_manifest: Path,
) -> tuple[str, dict[str, str]]:
    manifests = {
        "seed2": _read(seed2_manifest),
        "m6_smoke": _read(m6_manifest),
        "m5": _read(m5_manifest),
    }
    statuses = {key: str(value.get("status")) for key, value in manifests.items()}
    if any(status in TERMINAL_FAILURES for status in statuses.values()):
        return "fail", statuses
    if (
        statuses["seed2"] != "complete"
        or statuses["m6_smoke"] != "complete"
        or statuses["m5"] not in {"running", "complete"}
    ):
        return "waiting", statuses

    seed2_artifacts = manifests["seed2"].get("expected_artifacts")
    if not isinstance(seed2_artifacts, list) or len(seed2_artifacts) < 2:
        return "fail", {**statuses, "seed2_artifact": "missing"}
    seed2_output = ROOT / str(seed2_artifacts[1])
    if not seed2_output.is_file():
        return "fail", {**statuses, "seed2_artifact": "absent"}
    seed2 = _read(seed2_output)
    seed2_checks = seed2.get("checks")
    if (
        seed2.get("status") != "complete"
        or seed2.get("performance_values_opened") is not False
        or not isinstance(seed2_checks, dict)
        or not seed2_checks
        or not all(seed2_checks.values())
    ):
        return "fail", {**statuses, "seed2_artifact": "invalid"}

    m6_artifacts = manifests["m6_smoke"].get("expected_artifacts")
    if not isinstance(m6_artifacts, list) or len(m6_artifacts) < 3:
        return "fail", {**statuses, "m6_artifact": "missing"}
    m6_state_path = ROOT / str(m6_artifacts[0])
    m6_audit_path = ROOT / str(m6_artifacts[1])
    if not m6_state_path.is_file() or not m6_audit_path.is_file():
        return "fail", {**statuses, "m6_artifact": "absent"}
    m6_state = _read(m6_state_path)
    m6_audit = _read(m6_audit_path)
    m6_checks = m6_audit.get("checks")
    if (
        m6_state.get("status") != "complete"
        or m6_state.get("main_optimizer_steps_authorized") != 0
        or m6_audit.get("status") != "pass"
        or not isinstance(m6_checks, dict)
        or not m6_checks
        or not all(m6_checks.values())
    ):
        return "fail", {**statuses, "m6_artifact": "invalid"}
    return "ready", statuses


def node_snapshot(node: str) -> dict[str, Any]:
    gpu_result = subprocess.run(
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
    gpus: dict[int, dict[str, int]] = {}
    for line in gpu_result.stdout.splitlines():
        index, memory, utilization = (int(value.strip()) for value in line.split(","))
        gpus[index] = {"memory_mib": memory, "utilization_pct": utilization}
    if set(gpus) != set(range(8)):
        raise ValueError(f"{node} did not report exactly GPUs 0-7")
    trainer = subprocess.run(
        ["ssh", node, "pgrep -af '[p]ython.*verl.trainer.main.*BlindGain'"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    ).returncode == 0
    return {"project_trainer_active": trainer, "gpus": gpus}


def _parse_run(output: str, prefix: str) -> str:
    values = [line.strip() for line in output.splitlines() if line.strip().startswith(prefix)]
    if len(values) != 1:
        raise RuntimeError(f"ambiguous launcher output: {output!r}")
    return values[0]


def launch_arm(arm: str, node: str, gpu_ids: list[int]) -> tuple[str, str]:
    result = subprocess.run(
        [
            "bash",
            "scripts/launch_mech_pilot_followup_arm.sh",
            "3",
            arm,
            node,
            ",".join(str(gpu) for gpu in gpu_ids),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode in {74, 75, 76}:
        raise BlockingIOError(result.stderr.strip())
    if result.returncode != 0:
        raise RuntimeError(
            f"seed-3 {arm} launch failed ({result.returncode}): {result.stderr.strip()}"
        )
    training_run = _parse_run(result.stdout, "experiments/runs/mech_")
    watcher = subprocess.run(
        ["bash", "scripts/launch_pilot_checkpoint_watch.sh", node, training_run],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if watcher.returncode != 0:
        raise RuntimeError(
            f"seed-3 {arm} checkpoint watcher failed to launch "
            f"({watcher.returncode}): {watcher.stderr.strip()}"
        )
    watcher_run = _parse_run(watcher.stdout, "experiments/runs/pilot_checkpoint_watch_")
    return training_run, watcher_run


def arm_checkpoint_ready(record: dict[str, Any]) -> tuple[bool, str]:
    training_run = ROOT / str(record["training_run"])
    watcher_run = ROOT / str(record["watcher_run"])
    training = _read(training_run / "run_manifest.json")
    watcher = _read(watcher_run / "run_manifest.json")
    training_status = str(training.get("status"))
    watcher_status = str(watcher.get("status"))
    if training_status in TERMINAL_FAILURES:
        raise RuntimeError(f"training reached terminal status {training_status}")
    if watcher_status in TERMINAL_FAILURES:
        raise RuntimeError(f"checkpoint watcher reached terminal status {watcher_status}")
    if training_status != "complete":
        return False, "training_running"
    if training.get("exit_code") != 0 or training.get("artifacts_exist") is not True:
        raise RuntimeError("training completion is not artifact-verified")
    checkpoint_root = Path(str(training["checkpoint_path"]))
    final_index = checkpoint_root / "global_step_100/actor/huggingface/model.safetensors.index.json"
    final_raw_marker = checkpoint_root / "global_step_100/actor/RAW_STATE_RELOCATED.json"
    if not final_index.is_file() or not final_raw_marker.is_file():
        return False, "waiting_step100_merge_and_retention"
    return True, "training_and_step100_retention_complete"


def run_queue(
    run_dir: Path,
    *,
    seed2_manifest: Path,
    m6_manifest: Path,
    m5_manifest: Path,
    poll_seconds: int,
    stable_polls: int,
) -> int:
    state_path = run_dir / "queue_state.json"
    records: dict[str, dict[str, Any]] = {
        arm: {"status": "pending", "training_run": None, "watcher_run": None}
        for arm in ARMS
    }
    state: dict[str, Any] = {
        "schema_version": "blind-gains.pilot-seed3-capacity-queue.v2",
        "status": "waiting_dependencies",
        "seed": 3,
        "arms": records,
        "dependencies": {
            "seed2": str(seed2_manifest),
            "m6_smoke": str(m6_manifest),
            "m5": str(m5_manifest),
        },
        "dependency_status": {},
        "created_utc": _now(),
        "performance_values_opened": False,
        "scientific_gate_decision": None,
    }
    _write(state_path, state)
    while True:
        dependency, statuses = dependency_state(seed2_manifest, m6_manifest, m5_manifest)
        state["dependency_status"] = statuses
        state["updated_utc"] = _now()
        if dependency == "fail":
            state["status"] = "failed_dependency"
            _write(state_path, state)
            return 2
        if dependency == "ready":
            break
        _write(state_path, state)
        time.sleep(poll_seconds)

    streaks = {node: {gpu: 0 for gpu in range(8)} for node in NODES}
    while True:
        for arm, record in records.items():
            if record["status"] not in {"running", "checkpoint_finalizing"}:
                continue
            try:
                ready, reason = arm_checkpoint_ready(record)
            except Exception as error:
                record.update({"status": "failed", "error": f"{type(error).__name__}: {error}"})
                state.update({"status": "failed", "failed_arm": arm, "updated_utc": _now()})
                _write(state_path, state)
                raise
            if ready:
                record.update({"status": "training_complete_pending_evaluation", "completed_utc": _now()})
            else:
                record.update({"status": "checkpoint_finalizing" if reason.startswith("waiting_step100") else "running", "structural_state": reason})

        if all(
            record["status"] == "training_complete_pending_evaluation"
            for record in records.values()
        ):
            state.update(
                {
                    "status": "training_complete_pending_registered_evaluations",
                    "updated_utc": _now(),
                    "arms": records,
                }
            )
            _write(state_path, state)
            return 0

        snapshots: dict[str, Any] = {}
        for node in NODES:
            try:
                snapshot = node_snapshot(node)
            except Exception as error:
                snapshots[node] = {"error": f"{type(error).__name__}: {error}"}
                streaks[node] = {gpu: 0 for gpu in range(8)}
                continue
            snapshots[node] = snapshot
            for gpu, values in snapshot["gpus"].items():
                free = (
                    not snapshot["project_trainer_active"]
                    and values["memory_mib"] <= 1024
                    and values["utilization_pct"] <= 10
                )
                streaks[node][gpu] = streaks[node][gpu] + 1 if free else 0

        pending = [arm for arm in ARMS if records[arm]["status"] == "pending"]
        for node in NODES:
            if not pending:
                break
            snapshot = snapshots.get(node, {})
            if snapshot.get("project_trainer_active") is not False:
                continue
            stable = [gpu for gpu in range(8) if streaks[node][gpu] >= stable_polls]
            if len(stable) < 4:
                continue
            arm = pending.pop(0)
            gpu_ids = stable[:4]
            try:
                training_run, watcher_run = launch_arm(arm, node, gpu_ids)
            except BlockingIOError as error:
                records[arm]["last_launch_refusal"] = str(error)
                continue
            records[arm].update(
                {
                    "status": "running",
                    "training_run": training_run,
                    "watcher_run": watcher_run,
                    "node": node,
                    "gpu_ids": gpu_ids,
                    "launched_utc": _now(),
                }
            )

        state.update(
            {
                "status": (
                    "running"
                    if any(record["status"] != "pending" for record in records.values())
                    else "waiting_capacity"
                ),
                "arms": records,
                "node_snapshots": snapshots,
                "free_streaks": streaks,
                "updated_utc": _now(),
            }
        )
        _write(state_path, state)
        time.sleep(poll_seconds)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--seed2-manifest", type=Path, required=True)
    parser.add_argument("--m6-manifest", type=Path, required=True)
    parser.add_argument("--m5-manifest", type=Path, required=True)
    parser.add_argument("--poll-seconds", type=int, default=60)
    parser.add_argument("--stable-polls", type=int, default=2)
    args = parser.parse_args()
    if args.poll_seconds < 10 or args.stable_polls < 2:
        raise ValueError("seed-3 queue requires poll_seconds >= 10 and stable_polls >= 2")
    raise SystemExit(
        run_queue(
            args.run_dir,
            seed2_manifest=args.seed2_manifest,
            m6_manifest=args.m6_manifest,
            m5_manifest=args.m5_manifest,
            poll_seconds=args.poll_seconds,
            stable_polls=args.stable_polls,
        )
    )


if __name__ == "__main__":
    main()
