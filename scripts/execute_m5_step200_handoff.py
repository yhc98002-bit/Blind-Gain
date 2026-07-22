#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Any

from scripts.relocate_rederivable_tree import (
    inventory_tree,
    validate_embedded_checksum_manifests,
)


ROOT = Path(__file__).resolve().parents[1]


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite handoff artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def metric_memory_rows(metric_log: Path) -> list[tuple[int, float]]:
    rows: dict[int, float] = {}
    with metric_log.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                payload = json.loads(line)
                step = payload.get("step")
                memory = payload.get("perf", {}).get("cpu_memory_used_gb")
            except (json.JSONDecodeError, AttributeError):
                continue
            if isinstance(step, int) and isinstance(memory, (int, float)):
                rows[step] = float(memory)
    return sorted(rows.items())


def recent_memory_slope(rows: list[tuple[int, float]], window: int = 10) -> float:
    selected = rows[-window:]
    if len(selected) < 2 or selected[-1][0] == selected[0][0]:
        raise RuntimeError("insufficient distinct operational memory rows")
    return (selected[-1][1] - selected[0][1]) / (selected[-1][0] - selected[0][0])


def _ssh(node: str, command: str) -> str:
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", node, command],
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"{node} command failed ({result.returncode}): {result.stderr.strip()}")
    return result.stdout


def process_identity(
    node: str, wrapper_pid: int, expected_config: Path
) -> dict[str, Any]:
    wrapper = _ssh(
        node,
        f"ps -o pid=,ppid=,pgid=,user=,args= -p {wrapper_pid}",
    ).strip()
    fields = wrapper.split(maxsplit=4)
    if (
        len(fields) != 5
        or int(fields[0]) != wrapper_pid
        or int(fields[1]) != 1
        or "scripts/run_manifest_job.py" not in fields[4]
    ):
        raise RuntimeError("registered M5 wrapper identity is absent or changed")
    children = _ssh(
        node,
        f"ps --ppid {wrapper_pid} -o pid=,ppid=,pgid=,user=,args=",
    )
    trainer_rows = [
        row.strip()
        for row in children.splitlines()
        if "python -u -m verl.trainer.main" in row
        and f"config={expected_config.resolve()}" in row
    ]
    if len(trainer_rows) != 1:
        raise RuntimeError("registered M5 trainer child is absent or ambiguous")
    trainer = trainer_rows[0].split(maxsplit=4)
    if (
        len(trainer) != 5
        or int(trainer[1]) != wrapper_pid
        or int(trainer[2]) != int(fields[2])
        or trainer[3] != fields[3]
    ):
        raise RuntimeError("M5 trainer parent/group/user identity mismatch")
    mem_text = _ssh(
        node, "awk '/^MemAvailable:/ {print $2}' /proc/meminfo"
    ).strip()
    return {
        "node": node,
        "wrapper_pid": wrapper_pid,
        "trainer_pid": int(trainer[0]),
        "process_group_id": int(fields[2]),
        "user": fields[3],
        "expected_config": str(expected_config.resolve()),
        "mem_available_kib": int(mem_text),
    }


def select_interrupt_signal(node: str, trainer_pid: int) -> dict[str, Any]:
    status = _ssh(
        node,
        f"awk '/^SigIgn:/ {{print $2}}' /proc/{trainer_pid}/status",
    ).strip()
    ignored_mask = int(status, 16)
    sigint_ignored = bool(ignored_mask & (1 << (signal.SIGINT - 1)))
    selected = signal.SIGTERM if sigint_ignored else signal.SIGINT
    return {
        "ignored_mask_hex": status,
        "sigint_ignored": sigint_ignored,
        "selected_signal": signal.Signals(selected).name,
        "selected_signal_number": int(selected),
    }


def validate_step200(
    checkpoint_root: Path, archive_root: Path, source_run: Path
) -> dict[str, Any]:
    step = 200
    tracker = _read(checkpoint_root / "checkpoint_tracker.json")
    if int(tracker.get("last_global_step", -1)) < step:
        raise RuntimeError("checkpoint tracker has not reached step 200")
    checkpoint = checkpoint_root / "global_step_200"
    actor = checkpoint / "actor"
    archive = archive_root / "global_step_200" / "actor"
    raw_marker = _read(actor / "RAW_STATE_RELOCATED.json")
    merged_marker = _read(actor / "MERGED_CHECKPOINT_RELOCATED.json")
    if (
        raw_marker.get("status") != "raw_training_state_relocated_due_to_shared_quota"
        or Path(str(raw_marker.get("archive_path", ""))).resolve() != archive.resolve()
    ):
        raise RuntimeError("step-200 raw relocation marker is invalid")
    merged_archive = archive / "huggingface"
    if (
        merged_marker.get("status") != "merged_checkpoint_relocated"
        or Path(str(merged_marker.get("archive_path", ""))).resolve()
        != merged_archive.resolve()
    ):
        raise RuntimeError("step-200 merged relocation marker is invalid")

    inventory = inventory_tree(archive)
    embedded = validate_embedded_checksum_manifests(archive, inventory)
    target_counts = sorted(item["target_count"] for item in embedded)
    if target_counts != [8, 14]:
        raise RuntimeError(f"step-200 checksum coverage differs: {target_counts}")
    extras = sorted(actor.glob("extra_state_world_size_4_rank_*.pt"))
    dataloader = checkpoint / "dataloader.pt"
    if len(extras) != 4 or any(path.stat().st_size <= 0 for path in extras):
        raise RuntimeError("step-200 extra-state ranks are incomplete")
    if not dataloader.is_file() or dataloader.stat().st_size <= 0:
        raise RuntimeError("step-200 dataloader state is incomplete")

    evaluation = _read(source_run / "evaluations/step200_evaluation_complete.json")
    index = merged_archive / "model.safetensors.index.json"
    if (
        evaluation.get("status") != "complete"
        or evaluation.get("global_step") != 200
        or evaluation.get("geo3k_status") != "complete"
        or evaluation.get("r19_status") != "complete"
        or evaluation.get("checkpoint_index_sha256") != _sha256(index)
    ):
        raise RuntimeError("step-200 registered evaluation marker is invalid")
    return {
        "status": "pass",
        "global_step": 200,
        "checkpoint_root": str(checkpoint_root),
        "archive_root": str(archive_root),
        "archive_file_count": len(inventory),
        "archive_total_bytes": sum(item["size_bytes"] for item in inventory),
        "embedded_checksum_target_counts": target_counts,
        "checkpoint_index_sha256": _sha256(index),
        "evaluation_marker_sha256": _sha256(
            source_run / "evaluations/step200_evaluation_complete.json"
        ),
        "extra_state_rank_count": len(extras),
        "dataloader_sha256": _sha256(dataloader),
    }


def execute(args: argparse.Namespace) -> dict[str, Any]:
    source_manifest = _read(args.source_run / "run_manifest.json")
    if (
        source_manifest.get("status") != "running"
        or source_manifest.get("job_type") != "m5_anchor_longhorizon_400"
        or source_manifest.get("node") != args.node
        or source_manifest.get("resumed_from_global_step") != 150
        or source_manifest.get("target_global_step") != 400
    ):
        raise RuntimeError("source is not the active registered M5 recovery run")
    checkpoint_root = Path(str(source_manifest["checkpoint_path"]))
    metric_log = checkpoint_root / "experiment_log.jsonl"
    rows = metric_memory_rows(metric_log)
    if not rows or rows[-1][0] < 200:
        raise RuntimeError("M5 has not logged the step-200 operational boundary")
    slope = recent_memory_slope(rows)
    wrapper_pid = int(
        (args.source_run / "pids" / f"{args.node}.pid").read_text().strip()
    )
    expected_config = ROOT / str(source_manifest["config_path"])
    identity = process_identity(args.node, wrapper_pid, expected_config)
    boundary = validate_step200(checkpoint_root, args.archive_root, args.source_run)
    reasons = []
    if slope > args.slope_threshold:
        reasons.append("recent_cpu_memory_slope_above_threshold")
    if identity["mem_available_kib"] < int(args.available_threshold_gib * 1024**2):
        reasons.append("host_mem_available_below_threshold")
    if not reasons:
        raise RuntimeError("mechanical step-200 handoff thresholds are not met")

    intent = {
        "schema_version": "blind-gains.m5-step200-handoff-intent.v1",
        "status": "authorized_by_mechanical_thresholds",
        "created_at_utc": _now(),
        "source_run": str(args.source_run),
        "boundary_evidence": boundary,
        "process_identity": identity,
        "recent_cpu_memory_slope_gib_per_step": slope,
        "slope_threshold_gib_per_step": args.slope_threshold,
        "available_threshold_gib": args.available_threshold_gib,
        "reasons": reasons,
        "scientific_stopping_decision": False,
    }
    _atomic_json(args.run_dir / "handoff_intent.json", intent)

    repeated = process_identity(args.node, wrapper_pid, expected_config)
    for key in ("wrapper_pid", "trainer_pid", "process_group_id", "user", "expected_config"):
        if repeated[key] != identity[key]:
            raise RuntimeError("M5 process identity changed before SIGINT")
    signal_selection = select_interrupt_signal(args.node, identity["trainer_pid"])
    _ssh(
        args.node,
        f"kill -{signal_selection['selected_signal_number']} {identity['trainer_pid']}",
    )
    deadline = time.monotonic() + args.wait_seconds
    wrapper_exited = False
    while time.monotonic() < deadline:
        alive = _ssh(
            args.node,
            f"if kill -0 {wrapper_pid} 2>/dev/null; then echo 1; else echo 0; fi",
        ).strip()
        if alive == "0":
            wrapper_exited = True
            break
        time.sleep(10)
    group_rows = _ssh(
        args.node,
        "ps -eo pid=,ppid=,pgid=,user=,args= | "
        f"awk '$3 == {identity['process_group_id']} {{print}}'",
    ).splitlines()
    return {
        **intent,
        "status": "handoff_complete" if wrapper_exited else "cleanup_required",
        "completed_at_utc": _now(),
        "signal_selection": signal_selection,
        "wrapper_exited": wrapper_exited,
        "remaining_process_group_rows": [row.strip() for row in group_rows if row.strip()],
        "resume_required_from_step": 200,
        "sigkill_used": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--source-run", type=Path, required=True)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--node", choices=("an12", "an29"), required=True)
    parser.add_argument("--slope-threshold", type=float, default=2.0)
    parser.add_argument("--available-threshold-gib", type=float, default=350.0)
    parser.add_argument("--wait-seconds", type=int, default=300)
    args = parser.parse_args()
    if args.wait_seconds < 60:
        parser.error("handoff wait must be at least 60 seconds")
    result = execute(args)
    _atomic_json(args.run_dir / "handoff_result.json", result)
    print(json.dumps(result, sort_keys=True))
    if result["status"] != "handoff_complete":
        raise SystemExit(4)


if __name__ == "__main__":
    main()
