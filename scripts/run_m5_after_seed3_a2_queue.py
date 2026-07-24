#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
SEGMENT_STARTS = (200, 250, 300, 350)
TERMINAL_FAILURES = {"fail", "failed", "error", "blocked", "cancelled", "canceled"}
SHARED_ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289")
MIN_M5_HOST_MEMORY_KIB = 650 * 1024 * 1024
MIN_SHARED_FREE_BYTES = 80 * 1024**3

CONTRACT_PATHS = (
    "scripts/run_m5_after_seed3_a2_queue.py",
    "scripts/launch_m5_after_seed3_a2_queue.sh",
    "scripts/measure_storage_usage.py",
    "scripts/launch_m5_step_restore.sh",
    "scripts/restore_easyr1_raw_checkpoint.py",
    "scripts/audit_easyr1_resume_checkpoint.py",
    "src/ops/checkpoint_restore.py",
    "src/ops/storage_guard.py",
    "scripts/launch_m5_ray_startup_preflight.sh",
    "scripts/probe_m5_ray_startup.py",
    "scripts/build_m5_segment_config.py",
    "scripts/launch_m5_anchor_segment.sh",
    "scripts/watch_m5_checkpoints.py",
    "scripts/watch_m5_merged_relocation.py",
    "scripts/launch_m5_checkpoint_watch.sh",
    "scripts/launch_m5_merged_relocation_watch.sh",
    "scripts/run_m5_checkpoint_evaluation_queue.py",
    "scripts/launch_m5_checkpoint_evaluation_queue.sh",
    "scripts/launch_m5_geo3k_checkpoint_eval.sh",
    "scripts/launch_m5_fliptrack_checkpoint_eval.sh",
    "scripts/watch_m5_step_evaluation.py",
    "scripts/finalize_m5_step_evaluation.py",
    "scripts/launch_m5_step_evaluation_watch.sh",
    "scripts/run_manifest_job.py",
    "scripts/finalize_run_manifest.py",
    "configs/train/m5_anchor_longhorizon_400.yaml",
    "docs/registered_extensions_v1.md",
    "reports/registered_extensions_authorization_v4.json",
)


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def contract_hash(root: Path = ROOT) -> str:
    digest = hashlib.sha256()
    for relative in CONTRACT_PATHS:
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(f"M5 queue contract file is absent: {relative}")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(_sha256(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def assert_contract_unchanged(expected_hash: str) -> None:
    observed = contract_hash()
    if observed != expected_hash:
        raise RuntimeError(
            f"M5 queue contract changed while active: expected {expected_hash}, got {observed}"
        )
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", *CONTRACT_PATHS],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if tracked.returncode != 0:
        raise RuntimeError(f"M5 queue contract is not fully tracked: {tracked.stderr.strip()}")
    dirty = subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--", *CONTRACT_PATHS],
        cwd=ROOT,
        check=False,
    )
    if dirty.returncode != 0:
        raise RuntimeError("M5 queue contract differs from HEAD")


def _safe_run_dir(value: str, *, allowed_prefixes: tuple[str, ...]) -> Path:
    relative = Path(value)
    expected_root = (ROOT / "experiments/runs").resolve()
    resolved = (ROOT / relative).resolve()
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or not any(value.startswith(prefix) for prefix in allowed_prefixes)
        or not resolved.is_relative_to(expected_root)
        or resolved.parent != expected_root
    ):
        raise ValueError(f"run path is outside the immutable run namespace: {value}")
    if not (resolved / "run_manifest.json").is_file():
        raise FileNotFoundError(f"run manifest is absent: {resolved}")
    return resolved


def validate_a2_identity(training_run: str, watcher_run: str) -> tuple[Path, Path]:
    training_path = _safe_run_dir(training_run, allowed_prefixes=("experiments/runs/mech_",))
    watcher_path = _safe_run_dir(
        watcher_run,
        allowed_prefixes=("experiments/runs/pilot_checkpoint_watch_",),
    )
    training = _read(training_path / "run_manifest.json")
    watcher = _read(watcher_path / "run_manifest.json")
    pointer = training_path / "checkpoint_watcher_run.txt"
    pointer_value = pointer.read_text(encoding="utf-8").strip() if pointer.is_file() else None
    checks = {
        "training_job": training.get("job_type") == "m3_mechanical_pilot_arm",
        "seed": training.get("seed") == 3,
        "arm": training.get("arm") == "a2_gray",
        "condition": training.get("image_condition") == "gray",
        "node": training.get("node") == "an12",
        "gpu_ids": training.get("gpu_ids") == [0, 1, 2, 3],
        "tp1_replicas4": training.get("tensor_parallel_width") == 1
        and training.get("replica_count") == 4,
        "watcher_pointer": pointer_value == watcher_run,
        "watcher_job": watcher.get("job_type") == "pilot_checkpoint_retention_watch",
        "watcher_parent": watcher.get("parent_training_run") == training_run,
        "watcher_node": watcher.get("compute_node") == "an12",
    }
    if not all(checks.values()):
        raise ValueError(f"seed-3 A2/watcher identity mismatch: {checks}")
    return training_path, watcher_path


def a2_release_state(training_run: str, watcher_run: str) -> tuple[str, dict[str, Any]]:
    training_path, watcher_path = validate_a2_identity(training_run, watcher_run)
    training = _read(training_path / "run_manifest.json")
    watcher = _read(watcher_path / "run_manifest.json")
    training_status = str(training.get("status"))
    watcher_status = str(watcher.get("status"))
    evidence: dict[str, Any] = {
        "training_status": training_status,
        "watcher_status": watcher_status,
        "checked_utc": _now(),
    }
    if training_status in TERMINAL_FAILURES or watcher_status in TERMINAL_FAILURES:
        return "fail", evidence
    if training_status != "complete":
        return "waiting", evidence
    completion_checks = {
        "training_exit_zero": training.get("exit_code") == 0,
        "training_artifacts_verified": training.get("artifacts_exist") is True,
        "watcher_nonterminal": watcher_status in {"running", "complete"},
    }
    if watcher_status == "complete":
        completion_checks["watcher_exit_zero"] = watcher.get("exit_code") == 0
        completion_checks["watcher_artifacts_verified"] = (
            watcher.get("artifacts_exist") is True
        )
    checkpoint_root = Path(str(training.get("checkpoint_path", "")))
    index = checkpoint_root / "global_step_100/actor/huggingface/model.safetensors.index.json"
    raw_marker = checkpoint_root / "global_step_100/actor/RAW_STATE_RELOCATED.json"
    tracker = checkpoint_root / "checkpoint_tracker.json"
    completion_checks.update(
        {
            "step100_index": index.is_file(),
            "step100_raw_marker": raw_marker.is_file(),
            "tracker_step100": tracker.is_file()
            and _read(tracker).get("last_global_step") == 100,
        }
    )
    if raw_marker.is_file():
        marker = _read(raw_marker)
        completion_checks["raw_marker_status"] = (
            marker.get("status") == "raw_training_state_relocated_due_to_shared_quota"
            and isinstance(marker.get("files"), list)
            and len(marker["files"]) == 8
        )
    else:
        completion_checks["raw_marker_status"] = False
    evidence["completion_checks"] = completion_checks
    return ("ready" if all(completion_checks.values()) else "fail"), evidence


def validate_initial_m5(source_run: str, handoff_run: str) -> tuple[Path, Path]:
    source_path = _safe_run_dir(
        source_run,
        allowed_prefixes=("experiments/runs/m5_anchor_longhorizon_400_",),
    )
    handoff_path = _safe_run_dir(
        handoff_run,
        allowed_prefixes=("experiments/runs/m5_step200_handoff_",),
    )
    source = _read(source_path / "run_manifest.json")
    handoff = _read(handoff_path / "handoff_result.json")
    checks = {
        "source_job": source.get("job_type") == "m5_anchor_longhorizon_400",
        "source_status": source.get("status") == "fail" and source.get("exit_code") == -6,
        "registered_terminal": source.get("target_global_step") == 400
        and source.get("terminal_no_extension") is True,
        "step200_evaluated": (
            source_path / "evaluations/step200_evaluation_complete.json"
        ).is_file(),
        "handoff_status": handoff.get("status") == "handoff_complete",
        "handoff_source": handoff.get("source_run") == source_run,
        "handoff_boundary": handoff.get("resume_required_from_step") == 200,
        "no_sigkill": handoff.get("sigkill_used") is False,
    }
    if not all(checks.values()):
        raise ValueError(f"M5 step-200 source/handoff identity mismatch: {checks}")
    return source_path, handoff_path


def _parse_run(output: str, prefix: str) -> str:
    rows = [line.strip() for line in output.splitlines() if line.strip().startswith(prefix)]
    if len(rows) != 1:
        raise RuntimeError(f"ambiguous child launcher output for {prefix}: {output!r}")
    _safe_run_dir(rows[0], allowed_prefixes=(prefix,))
    return rows[0]


def _run_launcher(arguments: list[str], *, prefix: str, timeout: int | None = None) -> str:
    result = subprocess.run(
        arguments,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"child launcher failed ({result.returncode}): {arguments!r}; "
            f"stdout={result.stdout!r}; stderr={result.stderr!r}"
        )
    return _parse_run(result.stdout, prefix)


def _run_liveness(run_path: Path, manifest: dict[str, Any]) -> tuple[bool, str]:
    if manifest.get("status") != "running":
        return True, "not_running"
    node = str(manifest.get("node", ""))
    run_id = str(manifest.get("run_id", ""))
    manifest_path = (run_path / "run_manifest.json").resolve()
    manifest_arguments = {str(manifest_path)}
    if manifest_path.is_relative_to(ROOT.resolve()):
        manifest_arguments.add(str(manifest_path.relative_to(ROOT.resolve())))
    if node in {"an12", "an29"}:
        pid_file = run_path / "pids" / f"{node}.pid"
        if not pid_file.is_file() or not pid_file.read_text(encoding="ascii").strip().isdigit():
            return False, "remote_pid_file_absent"
        pid = pid_file.read_text(encoding="ascii").strip()
        result = subprocess.run(
            ["ssh", node, f"ps -p {pid} -o args="],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        alive = (
            result.returncode == 0
            and "run_manifest_job.py" in result.stdout
            and any(value in result.stdout for value in manifest_arguments)
        )
        return alive, "remote_wrapper_identity_match" if alive else "remote_wrapper_absent"
    if node == "login":
        pid_file = run_path / "pids/login.pid"
        if pid_file.is_file() and pid_file.read_text(encoding="ascii").strip().isdigit():
            pid = pid_file.read_text(encoding="ascii").strip()
            result = subprocess.run(
                ["ps", "-p", pid, "-o", "args="],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            alive = (
                result.returncode == 0
                and "run_manifest_job.py" in result.stdout
                and any(value in result.stdout for value in manifest_arguments)
            )
            return alive, "login_wrapper_identity_match" if alive else "login_wrapper_absent"
        if not run_id or not run_id.replace("_", "").isalnum():
            return False, "invalid_tmux_run_id"
        result = subprocess.run(
            ["tmux", "has-session", "-t", run_id],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        return (
            result.returncode == 0,
            "tmux_session_present" if result.returncode == 0 else "tmux_session_absent",
        )
    return False, f"unsupported_run_node:{node}"


def _wait_complete(
    run: str,
    *,
    poll_seconds: int,
    on_wait: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    run_path = _safe_run_dir(run, allowed_prefixes=("experiments/runs/",))
    missing_liveness_streak = 0
    while True:
        manifest = _read(run_path / "run_manifest.json")
        status = str(manifest.get("status"))
        if status == "complete":
            if manifest.get("exit_code") != 0 or manifest.get("artifacts_exist") is not True:
                raise RuntimeError(f"child completion is not artifact-verified: {run}")
            return manifest
        if status in TERMINAL_FAILURES:
            raise RuntimeError(f"child reached terminal failure {status}: {run}")
        if status != "running":
            raise RuntimeError(f"child has unexpected status {status}: {run}")
        alive, liveness_reason = _run_liveness(run_path, manifest)
        missing_liveness_streak = 0 if alive else missing_liveness_streak + 1
        if missing_liveness_streak >= 3:
            refreshed = _read(run_path / "run_manifest.json")
            if refreshed.get("status") != "complete":
                raise RuntimeError(
                    f"child manifest remained running without its exact wrapper for "
                    f"three polls ({liveness_reason}): {run}"
                )
            continue
        if on_wait is not None:
            on_wait(manifest)
        time.sleep(poll_seconds)


def _refresh_storage_snapshot(run_dir: Path, label: str) -> dict[str, Any]:
    if not label.replace("-", "").replace("_", "").isalnum():
        raise ValueError(f"invalid storage snapshot label: {label}")
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    history = run_dir / f"storage_snapshot_{label}_{stamp}.json"
    result = subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            "scripts/measure_storage_usage.py",
            "--root",
            str(SHARED_ROOT),
            "--output",
            str(history),
        ],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": "."},
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(f"storage snapshot refresh failed: {result.stderr.strip()}")
    payload = _read(history)
    if payload.get("status") != "pass" or int(payload.get("free_bytes", -1)) < MIN_SHARED_FREE_BYTES:
        raise RuntimeError(f"shared storage below M5 restore safety floor: {payload}")
    canonical = ROOT / "reports/storage_usage_snapshot.json"
    temporary = canonical.with_name(f".{canonical.name}.partial.{os.getpid()}")
    shutil.copyfile(history, temporary)
    os.replace(temporary, canonical)
    return {
        "path": str(history.relative_to(ROOT)),
        "sha256": _sha256(history),
        "free_bytes": payload["free_bytes"],
        "measured_at_utc": payload["measured_at_utc"],
    }


def _storage_heartbeat(
    state: dict[str, Any],
    state_path: Path,
    run_dir: Path,
    *,
    segment_label: str,
    interval_seconds: int = 7200,
) -> Callable[[dict[str, Any]], None]:
    last_refresh = time.monotonic()

    def heartbeat(_manifest: dict[str, Any]) -> None:
        nonlocal last_refresh
        if time.monotonic() - last_refresh >= interval_seconds:
            snapshot = _refresh_storage_snapshot(
                run_dir, f"heartbeat_{segment_label.replace('-', '_')}"
            )
            state["segments"][segment_label].setdefault(
                "storage_heartbeat_snapshots", []
            ).append(snapshot)
            last_refresh = time.monotonic()
        state["updated_utc"] = _now()
        _atomic_write(state_path, state)

    return heartbeat


def _node_snapshot(node: str, gpu_ids: tuple[int, ...]) -> dict[str, Any]:
    trainer = subprocess.run(
        ["ssh", node, "pgrep -af '[p]ython.*verl.trainer.main.*BlindGain'"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    gpu = subprocess.run(
        [
            "ssh",
            node,
            "nvidia-smi --query-gpu=index,memory.used,utilization.gpu "
            "--format=csv,noheader,nounits",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    values: dict[int, dict[str, int]] = {}
    for row in gpu.stdout.splitlines():
        index, memory, utilization = (int(value.strip()) for value in row.split(","))
        values[index] = {"memory_mib": memory, "utilization_pct": utilization}
    memory = subprocess.run(
        ["ssh", node, "grep '^MemAvailable:' /proc/meminfo | tr -cd '0-9'"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    mem_available_kib = int(memory.stdout.strip())
    checks = {
        "no_project_trainer": trainer.returncode == 1,
        "selected_gpus_reported": all(index in values for index in gpu_ids),
        "selected_gpus_free": all(
            values.get(index, {}).get("memory_mib", 10**9) <= 1024
            and values.get(index, {}).get("utilization_pct", 100) <= 10
            for index in gpu_ids
        ),
        "host_memory_650gib": mem_available_kib >= MIN_M5_HOST_MEMORY_KIB,
    }
    return {
        "node": node,
        "gpu_ids": list(gpu_ids),
        "gpus": {str(index): values.get(index) for index in gpu_ids},
        "mem_available_kib": mem_available_kib,
        "checks": checks,
        "ready": all(checks.values()),
        "checked_utc": _now(),
    }


def _wait_node_ready(
    state: dict[str, Any],
    state_path: Path,
    *,
    node: str,
    gpu_ids: tuple[int, ...],
    poll_seconds: int,
    stable_polls: int = 2,
) -> None:
    streak = 0
    while streak < stable_polls:
        snapshot = _node_snapshot(node, gpu_ids)
        streak = streak + 1 if snapshot["ready"] else 0
        state.update(
            {
                "status": "waiting_m5_node_capacity",
                "node_snapshot": snapshot,
                "capacity_streak": streak,
                "updated_utc": _now(),
            }
        )
        _atomic_write(state_path, state)
        if streak < stable_polls:
            time.sleep(poll_seconds)


def _child_pointer(
    segment_run: str,
    filename: str,
    prefix: str,
    *,
    parent_field: str = "parent_training_run",
) -> str:
    segment_path = _safe_run_dir(
        segment_run,
        allowed_prefixes=("experiments/runs/m5_anchor_longhorizon_segment",),
    )
    pointer = segment_path / filename
    if not pointer.is_file():
        raise FileNotFoundError(f"M5 child pointer is absent: {pointer}")
    value = pointer.read_text(encoding="utf-8").strip()
    child_path = _safe_run_dir(value, allowed_prefixes=(prefix,))
    child = _read(child_path / "run_manifest.json")
    if child.get(parent_field) != segment_run:
        raise ValueError(f"M5 child pointer parent mismatch: {value}")
    return value


def _validate_segment_completion(segment_run: str, end_step: int) -> dict[str, Any]:
    segment_path = _safe_run_dir(
        segment_run,
        allowed_prefixes=("experiments/runs/m5_anchor_longhorizon_segment",),
    )
    manifest = _read(segment_path / "run_manifest.json")
    checkpoint_root = Path(str(manifest["checkpoint_path"]))
    actor = checkpoint_root / f"global_step_{end_step}/actor"
    raw_marker = actor / "RAW_STATE_RELOCATED.json"
    checks = {
        "segment_status": manifest.get("status") == "complete"
        and manifest.get("exit_code") == 0
        and manifest.get("artifacts_exist") is True,
        "segment_boundary": manifest.get("operational_segment") is True
        and manifest.get("segment_end_step") == end_step,
        "raw_marker": raw_marker.is_file()
        and _read(raw_marker).get("status")
        == "raw_training_state_relocated_due_to_shared_quota",
    }
    if end_step < 400:
        checks["merged_relocated"] = (actor / "MERGED_CHECKPOINT_RELOCATED.json").is_file()
    else:
        checks["final_merged_retained"] = (
            actor / "huggingface/model.safetensors.index.json"
        ).is_file()
    if end_step in {300, 400}:
        marker = segment_path / f"evaluations/step{end_step}_evaluation_complete.json"
        checks["registered_evaluation"] = marker.is_file() and _read(marker).get("status") == "complete"
    if not all(checks.values()):
        raise RuntimeError(f"M5 segment completion evidence failed: {checks}")
    return checks


def _segment_launch_args(
    *,
    node: str,
    gpu_ids: tuple[int, ...],
    start_step: int,
    restore_run: str,
    preflight_run: str,
    prior_run: str,
    handoff_run: str | None,
) -> list[str]:
    return [
        "bash",
        "scripts/launch_m5_anchor_segment.sh",
        node,
        ",".join(str(index) for index in gpu_ids),
        str(start_step),
        restore_run,
        preflight_run,
        prior_run,
        handoff_run if handoff_run is not None else "-",
    ]


def run_queue(
    run_dir: Path,
    *,
    a2_training_run: str,
    a2_watcher_run: str,
    initial_m5_run: str,
    handoff_run: str,
    expected_contract_hash: str,
    node: str,
    gpu_ids: tuple[int, ...],
    poll_seconds: int,
) -> int:
    if node != "an12" or gpu_ids != (0, 1, 2, 3):
        raise ValueError("registered M5 recovery placement is exactly an12 GPUs 0-3")
    validate_a2_identity(a2_training_run, a2_watcher_run)
    validate_initial_m5(initial_m5_run, handoff_run)
    assert_contract_unchanged(expected_contract_hash)

    state_path = run_dir / "queue_state.json"
    state: dict[str, Any] = {
        "schema_version": "blind-gains.m5-after-seed3-a2-lifecycle.v1",
        "status": "waiting_seed3_a2_release",
        "created_utc": _now(),
        "updated_utc": _now(),
        "a2_training_run": a2_training_run,
        "a2_watcher_run": a2_watcher_run,
        "initial_m5_run": initial_m5_run,
        "handoff_run": handoff_run,
        "node": node,
        "gpu_ids": list(gpu_ids),
        "contract_hash": expected_contract_hash,
        "segments": {
            f"{start}-{start + 50}": {"status": "pending"}
            for start in SEGMENT_STARTS
        },
        "performance_values_opened": False,
        "scientific_gate_decision": None,
    }
    _atomic_write(state_path, state)

    a2_missing_liveness_streak = {"training": 0, "watcher": 0}
    while True:
        release, evidence = a2_release_state(a2_training_run, a2_watcher_run)
        if release == "waiting":
            for name, run in (
                ("training", a2_training_run),
                ("watcher", a2_watcher_run),
            ):
                run_path = _safe_run_dir(run, allowed_prefixes=("experiments/runs/",))
                manifest = _read(run_path / "run_manifest.json")
                alive, reason = _run_liveness(run_path, manifest)
                a2_missing_liveness_streak[name] = (
                    0 if alive else a2_missing_liveness_streak[name] + 1
                )
                evidence[f"{name}_liveness"] = {
                    "alive": alive,
                    "reason": reason,
                    "missing_streak": a2_missing_liveness_streak[name],
                }
            if max(a2_missing_liveness_streak.values()) >= 3:
                release = "fail"
                evidence["failure_reason"] = (
                    "running manifest lacks its exact wrapper for three polls"
                )
        state.update({"a2_release": evidence, "updated_utc": _now()})
        if release == "fail":
            state["status"] = "failed_seed3_a2_release"
            _atomic_write(state_path, state)
            raise RuntimeError(f"seed-3 A2 release evidence failed: {evidence}")
        if release == "ready":
            state["status"] = "seed3_a2_released"
            _atomic_write(state_path, state)
            break
        state["status"] = "waiting_seed3_a2_release"
        _atomic_write(state_path, state)
        time.sleep(poll_seconds)

    prior_run = initial_m5_run
    boundary_run: str | None = handoff_run
    for start_step in SEGMENT_STARTS:
        end_step = start_step + 50
        label = f"{start_step}-{end_step}"
        assert_contract_unchanged(expected_contract_hash)
        state["status"] = f"refreshing_storage_before_{label}"
        state["updated_utc"] = _now()
        _atomic_write(state_path, state)
        snapshot = _refresh_storage_snapshot(run_dir, f"before_restore_step{start_step}")
        state["segments"][label]["storage_snapshot"] = snapshot

        restore_run = _run_launcher(
            ["bash", "scripts/launch_m5_step_restore.sh", prior_run, str(start_step)],
            prefix="experiments/runs/m5_step",
        )
        state["segments"][label].update(
            {"status": "restoring", "restore_run": restore_run, "updated_utc": _now()}
        )
        state["status"] = f"restoring_step_{start_step}"
        _atomic_write(state_path, state)
        _wait_complete(
            restore_run,
            poll_seconds=poll_seconds,
            on_wait=lambda _manifest: _atomic_write(state_path, {**state, "updated_utc": _now()}),
        )

        assert_contract_unchanged(expected_contract_hash)
        _wait_node_ready(
            state,
            state_path,
            node=node,
            gpu_ids=gpu_ids,
            poll_seconds=poll_seconds,
        )
        preflight_run = _run_launcher(
            [
                "bash",
                "scripts/launch_m5_ray_startup_preflight.sh",
                node,
                ",".join(str(index) for index in gpu_ids),
            ],
            prefix="experiments/runs/m5_ray_startup_preflight_",
            timeout=1800,
        )
        state["segments"][label]["preflight_run"] = preflight_run
        state["segments"][label]["prelaunch_storage_snapshot"] = (
            _refresh_storage_snapshot(run_dir, f"before_launch_{label.replace('-', '_')}")
        )
        state["status"] = f"launching_segment_{label}"
        state["updated_utc"] = _now()
        _atomic_write(state_path, state)

        assert_contract_unchanged(expected_contract_hash)
        segment_run = _run_launcher(
            _segment_launch_args(
                node=node,
                gpu_ids=gpu_ids,
                start_step=start_step,
                restore_run=restore_run,
                preflight_run=preflight_run,
                prior_run=prior_run,
                handoff_run=boundary_run,
            ),
            prefix="experiments/runs/m5_anchor_longhorizon_segment",
            timeout=1200,
        )
        checkpoint_watch = _child_pointer(
            segment_run,
            "checkpoint_watcher_run.txt",
            "experiments/runs/m5_checkpoint_watch_",
        )
        relocation_watch = _child_pointer(
            segment_run,
            "relocation_watcher_run.txt",
            "experiments/runs/m5_merged_relocation_watch_",
        )
        evaluation_queue = None
        if end_step in {300, 400}:
            evaluation_queue = _child_pointer(
                segment_run,
                "evaluation_queue_run.txt",
                "experiments/runs/m5_checkpoint_evaluation_queue_",
                parent_field="source_training_run",
            )
        state["segments"][label].update(
            {
                "status": "training",
                "segment_run": segment_run,
                "checkpoint_watcher_run": checkpoint_watch,
                "relocation_watcher_run": relocation_watch,
                "evaluation_queue_run": evaluation_queue,
                "launched_utc": _now(),
            }
        )
        state["status"] = f"training_segment_{label}"
        _atomic_write(state_path, state)

        heartbeat = _storage_heartbeat(
            state,
            state_path,
            run_dir,
            segment_label=label,
        )

        _wait_complete(
            segment_run,
            poll_seconds=poll_seconds,
            on_wait=heartbeat,
        )
        state["status"] = f"finalizing_segment_{label}"
        state["updated_utc"] = _now()
        _atomic_write(state_path, state)
        _wait_complete(checkpoint_watch, poll_seconds=poll_seconds, on_wait=heartbeat)
        _wait_complete(relocation_watch, poll_seconds=poll_seconds, on_wait=heartbeat)
        if evaluation_queue is not None:
            _wait_complete(evaluation_queue, poll_seconds=poll_seconds, on_wait=heartbeat)
        completion_checks = _validate_segment_completion(segment_run, end_step)
        state["segments"][label].update(
            {
                "status": "complete",
                "completion_checks": completion_checks,
                "completed_utc": _now(),
            }
        )
        state["updated_utc"] = _now()
        _atomic_write(state_path, state)
        prior_run = segment_run
        boundary_run = None

    state.update(
        {
            "status": "m5_terminal_step400_complete",
            "final_training_run": prior_run,
            "completed_utc": _now(),
            "updated_utc": _now(),
        }
    )
    _atomic_write(state_path, state)
    return 0


def _record_queue_failure(run_dir: Path, error: Exception) -> None:
    state_path = run_dir / "queue_state.json"
    if not state_path.is_file():
        return
    state = _read(state_path)
    state.update(
        {
            "status": "failed_closed",
            "failure": {
                "error_type": type(error).__name__,
                "message": str(error),
                "recorded_utc": _now(),
            },
            "updated_utc": _now(),
        }
    )
    _atomic_write(state_path, state)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--a2-training-run", required=True)
    parser.add_argument("--a2-watcher-run", required=True)
    parser.add_argument("--initial-m5-run", required=True)
    parser.add_argument("--handoff-run", required=True)
    parser.add_argument("--expected-contract-hash", required=True)
    parser.add_argument("--node", choices=("an12",), default="an12")
    parser.add_argument("--gpu-ids", default="0,1,2,3")
    parser.add_argument("--poll-seconds", type=int, default=60)
    args = parser.parse_args()
    gpu_ids = tuple(int(value) for value in args.gpu_ids.split(","))
    if args.poll_seconds < 30:
        raise ValueError("M5 lifecycle queue requires poll_seconds >= 30")
    try:
        exit_code = run_queue(
            args.run_dir,
            a2_training_run=args.a2_training_run,
            a2_watcher_run=args.a2_watcher_run,
            initial_m5_run=args.initial_m5_run,
            handoff_run=args.handoff_run,
            expected_contract_hash=args.expected_contract_hash,
            node=args.node,
            gpu_ids=gpu_ids,
            poll_seconds=args.poll_seconds,
        )
    except Exception as error:
        _record_queue_failure(args.run_dir, error)
        raise
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
