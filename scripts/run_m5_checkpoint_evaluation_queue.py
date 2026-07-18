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

from scripts.watch_anchor_checkpoints import merged_checkpoint_complete
from scripts.watch_m5_merged_relocation import valid_evaluation_marker


ROOT = Path(__file__).resolve().parents[1]
REGISTERED_STEPS = (150, 200, 300, 400)
DEFAULT_R19_MANIFEST = Path(
    "experiments/runs/caption_qa_pair_build_fliptrack_v02r19_qwen25vl3b_384_20260710T140200Z/"
    "shards/captions_shard_0.jsonl"
)
MIN_MEM_AVAILABLE_KIB = 471_859_200


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _atomic_update(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f".{path.name}.{os.getpid()}.partial")
    partial.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(partial, path)


def parse_gpu_snapshot(output: str) -> list[int]:
    free: list[int] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        fields = [field.strip() for field in line.split(",")]
        if len(fields) != 3 or not all(field.isdigit() for field in fields):
            raise ValueError(f"invalid nvidia-smi capacity row: {line!r}")
        index, memory_mib, utilization = map(int, fields)
        if memory_mib <= 1024 and utilization <= 10:
            free.append(index)
    return free


def node_capacity(node: str) -> dict[str, Any]:
    command = (
        "nvidia-smi --query-gpu=index,memory.used,utilization.gpu "
        "--format=csv,noheader,nounits; "
        "printf 'MEM_AVAILABLE='; grep '^MemAvailable:' /proc/meminfo | tr -cd '0-9'; printf '\\n'; "
        "if pgrep -af '[p]ython.*Qwen2.5-VL-72B' >/dev/null; then echo HAS_72B=1; else echo HAS_72B=0; fi"
    )
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", node, command],
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if result.returncode != 0:
        return {"node": node, "available": False, "reason": "ssh_failed"}
    gpu_lines = [line for line in result.stdout.splitlines() if not line.startswith(("MEM_AVAILABLE=", "HAS_72B="))]
    mem_line = next((line for line in result.stdout.splitlines() if line.startswith("MEM_AVAILABLE=")), "")
    has_72b = next((line for line in result.stdout.splitlines() if line.startswith("HAS_72B=")), "HAS_72B=1")
    try:
        free_gpus = parse_gpu_snapshot("\n".join(gpu_lines))
        mem_available = int(mem_line.split("=", 1)[1])
    except (ValueError, IndexError):
        return {"node": node, "available": False, "reason": "capacity_parse_failed"}
    available = len(free_gpus) >= 4 and mem_available >= MIN_MEM_AVAILABLE_KIB and has_72b == "HAS_72B=0"
    return {
        "node": node,
        "available": available,
        "free_gpus": free_gpus,
        "mem_available_kib": mem_available,
        "has_project_72b": has_72b == "HAS_72B=1",
        "reason": "capacity_available" if available else "insufficient_stable_capacity",
    }


def choose_capacity(nodes: list[str]) -> dict[str, Any] | None:
    snapshots = [node_capacity(node) for node in nodes]
    candidates = [snapshot for snapshot in snapshots if snapshot.get("available")]
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-int(item["mem_available_kib"]), str(item["node"])))
    selected = dict(candidates[0])
    selected["selected_gpus"] = list(selected["free_gpus"][:4])
    return selected


def run_checked(command: list[str]) -> str:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(command)}\n{result.stderr.strip()}"
        )
    return result.stdout


def manifest_complete(run: Path) -> bool:
    manifest_path = run / "run_manifest.json"
    if not manifest_path.is_file():
        return False
    manifest = _read(manifest_path)
    status = manifest.get("status")
    if status == "complete":
        return bool(manifest.get("artifacts_exist") is True)
    if status == "running":
        return False
    raise RuntimeError(f"M5 evaluation child reached non-complete status: {run}: {status!r}")


def launch_geo_cell(
    *,
    source_run: Path,
    checkpoint: Path,
    step: int,
    node: str,
    gpu: int,
) -> Path:
    geo_stdout = run_checked(
        [
            "bash", "scripts/launch_m5_geo3k_checkpoint_eval.sh", node, str(gpu),
            str(source_run), str(step), str(checkpoint), "-", "4",
        ]
    )
    geo_paths = [
        line.strip()
        for line in geo_stdout.splitlines()
        if line.strip().startswith("experiments/runs/m5_geo3k_step")
    ]
    if len(geo_paths) != 1:
        raise RuntimeError(f"ambiguous M5 Geometry3K launch path: {geo_stdout!r}")
    return Path(geo_paths[0])


def launch_r19_cell(
    *,
    source_run: Path,
    checkpoint: Path,
    step: int,
    r19_manifest: Path,
    node: str,
    gpus: list[int],
    image_mode: str,
    stamp: str,
) -> Path:
    run = Path(f"experiments/runs/m5_r19_step{step}_{image_mode}_{node}_{stamp}")
    run_checked(
        [
            "bash", "scripts/launch_m5_fliptrack_checkpoint_eval.sh", node, str(step),
            str(source_run), str(checkpoint), str(r19_manifest), str(run), str(len(gpus)),
            " ".join(str(gpu) for gpu in gpus), image_mode,
        ]
    )
    return run


def discover_evaluation_run(
    *,
    source_run: Path,
    checkpoint: Path,
    step: int,
    job_type: str,
    image_mode: str | None = None,
) -> Path | None:
    matches: list[Path] = []
    for manifest_path in (ROOT / "experiments/runs").glob("*/run_manifest.json"):
        try:
            manifest = _read(manifest_path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if manifest.get("job_type") != job_type or manifest.get("global_step") != step:
            continue
        if image_mode is not None and manifest.get("image_mode") != image_mode:
            continue
        if Path(str(manifest.get("source_training_run", ""))).resolve() != source_run.resolve():
            continue
        if Path(str(manifest.get("model_revision", ""))).resolve() != checkpoint.resolve():
            continue
        if manifest.get("status") not in {"running", "complete"}:
            continue
        matches.append(manifest_path.parent.relative_to(ROOT))
    if len(matches) > 1:
        raise RuntimeError(
            f"multiple immutable M5 evaluation children match step {step} {job_type} {image_mode}: {matches}"
        )
    return matches[0] if matches else None


def discover_watcher_run(*, source_run: Path, checkpoint: Path, step: int) -> Path | None:
    matches: list[Path] = []
    for manifest_path in (ROOT / "experiments/runs").glob("m5_step*_evaluation_watch_login_*/run_manifest.json"):
        try:
            manifest = _read(manifest_path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if manifest.get("job_type") != "m5_step_evaluation_watch" or manifest.get("global_step") != step:
            continue
        if Path(str(manifest.get("source_training_run", ""))).resolve() != source_run.resolve():
            continue
        if Path(str(manifest.get("checkpoint_path", ""))).resolve() != checkpoint.resolve():
            continue
        if manifest.get("status") not in {"running", "complete"}:
            continue
        matches.append(manifest_path.parent.relative_to(ROOT))
    if len(matches) > 1:
        raise RuntimeError(f"multiple M5 step-{step} evaluation watchers match: {matches}")
    return matches[0] if matches else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--source-run", type=Path, required=True)
    parser.add_argument("--steps", default="200,300,400")
    parser.add_argument("--nodes", default="an12,an29")
    parser.add_argument("--r19-manifest", type=Path, default=DEFAULT_R19_MANIFEST)
    parser.add_argument("--poll-seconds", type=int, default=60)
    parser.add_argument("--stable-polls", type=int, default=2)
    args = parser.parse_args()
    if args.poll_seconds < 10 or args.stable_polls < 2:
        raise ValueError("M5 evaluation queue requires >=10-second polling and >=2 stable polls")
    steps = tuple(int(value) for value in args.steps.split(",") if value)
    if not steps or any(step not in REGISTERED_STEPS for step in steps) or len(set(steps)) != len(steps):
        raise ValueError("invalid or duplicate M5 evaluation steps")
    nodes = [value for value in args.nodes.split(",") if value]
    if not nodes or any(node not in {"an12", "an29"} for node in nodes):
        raise ValueError("M5 evaluation nodes must be an12 and/or an29")
    if not args.r19_manifest.is_file():
        raise FileNotFoundError(args.r19_manifest)
    source_manifest = args.source_run / "run_manifest.json"
    if not source_manifest.is_file():
        raise FileNotFoundError(source_manifest)
    source = _read(source_manifest)
    if source.get("job_type") != "m5_anchor_longhorizon_400":
        raise ValueError("M5 evaluation queue source has the wrong job type")

    state_path = args.run_dir / "queue_state.json"
    if state_path.exists():
        state = _read(state_path)
    else:
        state = {
            "schema_version": "blind-gains.m5-checkpoint-evaluation-queue.v1",
            "status": "running",
            "source_training_run": str(args.source_run),
            "steps": {str(step): {"status": "waiting_for_merge"} for step in steps},
            "performance_values_opened": False,
            "scientific_gate_decision": None,
            "created_at_utc": _now(),
        }
        _atomic_update(state_path, state)

    for step in steps:
        step_state = state["steps"][str(step)]
        checkpoint = Path(str(source["checkpoint_path"])) / f"global_step_{step}/actor/huggingface"
        actor = checkpoint.parent
        marker = args.source_run / "evaluations" / f"step{step}_evaluation_complete.json"
        if valid_evaluation_marker(marker, step=step, actor_dir=actor):
            step_state["status"] = "complete"
            step_state["marker"] = str(marker)
            _atomic_update(state_path, state)
            continue
        while not merged_checkpoint_complete(checkpoint):
            current_source = _read(source_manifest)
            if step != 150 and current_source.get("status") not in {"running", "complete"}:
                raise RuntimeError(
                    f"M5 source terminated before registered step {step}: "
                    f"{current_source.get('status')!r}"
                )
            step_state.update({"status": "waiting_for_merge", "updated_at_utc": _now()})
            _atomic_update(state_path, state)
            time.sleep(args.poll_seconds)

        geo = (
            Path(str(step_state["geo3k_run"]))
            if step_state.get("geo3k_run")
            else discover_evaluation_run(
                source_run=args.source_run,
                checkpoint=checkpoint,
                step=step,
                job_type="m5_geo3k_checkpoint_eval",
            )
        )
        r19 = (
            Path(str(step_state["r19_real_run"]))
            if step_state.get("r19_real_run")
            else discover_evaluation_run(
                source_run=args.source_run,
                checkpoint=checkpoint,
                step=step,
                job_type="fliptrack_v02_image_evaluation",
                image_mode="real",
            )
        )
        if geo is None or r19 is None:
            stable = 0
            capacity: dict[str, Any] | None = None
            while stable < args.stable_polls:
                observed = choose_capacity(nodes)
                if observed is None:
                    stable = 0
                    step_state.update({"status": "waiting_for_capacity", "updated_at_utc": _now()})
                elif capacity and observed["node"] == capacity["node"] and observed["selected_gpus"] == capacity["selected_gpus"]:
                    stable += 1
                    capacity = observed
                    step_state.update({"status": "capacity_stabilizing", "stable_polls": stable, "capacity": capacity, "updated_at_utc": _now()})
                else:
                    capacity = observed
                    stable = 1
                    step_state.update({"status": "capacity_stabilizing", "stable_polls": stable, "capacity": capacity, "updated_at_utc": _now()})
                _atomic_update(state_path, state)
                if stable < args.stable_polls:
                    time.sleep(args.poll_seconds)
            assert capacity is not None
            node = str(capacity["node"])
            gpus = [int(value) for value in capacity["selected_gpus"]]
            stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            if geo is None:
                geo = launch_geo_cell(
                    source_run=args.source_run,
                    checkpoint=checkpoint,
                    step=step,
                    node=node,
                    gpu=gpus[0],
                )
                step_state.update({"status": "geo3k_running", "geo3k_run": str(geo), "updated_at_utc": _now()})
                _atomic_update(state_path, state)
            if r19 is None:
                r19_gpus = gpus[1:] if step_state.get("geo3k_run") == str(geo) else gpus[:3]
                r19 = launch_r19_cell(
                    source_run=args.source_run,
                    checkpoint=checkpoint,
                    step=step,
                    r19_manifest=args.r19_manifest,
                    node=node,
                    gpus=r19_gpus,
                    image_mode="real",
                    stamp=stamp,
                )
                step_state.update({"status": "primary_cells_running", "r19_real_run": str(r19), "updated_at_utc": _now()})
                _atomic_update(state_path, state)
        assert geo is not None and r19 is not None
        step_state.update({"geo3k_run": str(geo), "r19_real_run": str(r19), "updated_at_utc": _now()})
        _atomic_update(state_path, state)

        gray = Path(str(step_state["r19_gray_run"])) if step_state.get("r19_gray_run") else None
        noise = Path(str(step_state["r19_noise_run"])) if step_state.get("r19_noise_run") else None
        if step == 400:
            gray = gray or discover_evaluation_run(
                source_run=args.source_run,
                checkpoint=checkpoint,
                step=step,
                job_type="fliptrack_v02_image_evaluation",
                image_mode="gray",
            )
            noise = noise or discover_evaluation_run(
                source_run=args.source_run,
                checkpoint=checkpoint,
                step=step,
                job_type="fliptrack_v02_image_evaluation",
                image_mode="noise",
            )
            while not (manifest_complete(geo) and manifest_complete(r19)):
                time.sleep(args.poll_seconds)
            if gray is None or noise is None:
                capacity = None
                stable = 0
                while stable < args.stable_polls:
                    observed = choose_capacity(nodes)
                    if observed is not None and capacity and observed["node"] == capacity["node"] and observed["selected_gpus"] == capacity["selected_gpus"]:
                        stable += 1
                        capacity = observed
                    elif observed is not None:
                        capacity = observed
                        stable = 1
                    else:
                        capacity = None
                        stable = 0
                    step_state.update({"status": "waiting_for_blind_floor_capacity", "stable_polls": stable, "capacity": capacity, "updated_at_utc": _now()})
                    _atomic_update(state_path, state)
                    if stable < args.stable_polls:
                        time.sleep(args.poll_seconds)
                assert capacity is not None
                blind_stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                blind_gpus = [int(value) for value in capacity["selected_gpus"]]
                if gray is None:
                    gray = launch_r19_cell(
                        source_run=args.source_run,
                        checkpoint=checkpoint,
                        step=400,
                        r19_manifest=args.r19_manifest,
                        node=str(capacity["node"]),
                        gpus=blind_gpus[:2],
                        image_mode="gray",
                        stamp=blind_stamp,
                    )
                    step_state.update({"status": "gray_cell_running", "r19_gray_run": str(gray), "updated_at_utc": _now()})
                    _atomic_update(state_path, state)
                if noise is None:
                    noise_gpus = blind_gpus[2:] if step_state.get("r19_gray_run") == str(gray) else blind_gpus[:2]
                    noise = launch_r19_cell(
                        source_run=args.source_run,
                        checkpoint=checkpoint,
                        step=400,
                        r19_manifest=args.r19_manifest,
                        node=str(capacity["node"]),
                        gpus=noise_gpus,
                        image_mode="noise",
                        stamp=blind_stamp,
                    )
                    step_state.update({"status": "blind_floor_cells_running", "r19_noise_run": str(noise), "updated_at_utc": _now()})
                    _atomic_update(state_path, state)

        watch_command = [
            "bash", "scripts/launch_m5_step_evaluation_watch.sh", str(args.source_run), str(step),
            str(checkpoint), str(geo), str(r19), str(marker),
        ]
        if step == 400:
            assert gray is not None and noise is not None
            watch_command.extend([str(gray), str(noise)])
        watcher = (
            Path(str(step_state["watcher_run"]))
            if step_state.get("watcher_run")
            else discover_watcher_run(source_run=args.source_run, checkpoint=checkpoint, step=step)
        )
        if watcher is None:
            result = subprocess.run(watch_command, cwd=ROOT, text=True, capture_output=True, check=False)
            if result.returncode != 0:
                raise RuntimeError(f"M5 evaluation watcher launch failed: {result.stderr.strip()}")
            watcher_paths = [line.strip() for line in result.stdout.splitlines() if line.strip().startswith("experiments/runs/")]
            if len(watcher_paths) != 1:
                raise RuntimeError(f"ambiguous M5 watcher run path: {result.stdout!r}")
            watcher = Path(watcher_paths[0])
            step_state.update({"status": "watcher_running", "watcher_run": str(watcher), "updated_at_utc": _now()})
            _atomic_update(state_path, state)
        while not valid_evaluation_marker(marker, step=step, actor_dir=actor):
            watcher_manifest = watcher / "run_manifest.json"
            if watcher_manifest.is_file() and _read(watcher_manifest).get("status") == "fail":
                raise RuntimeError(f"M5 step evaluation watcher failed: {watcher}")
            time.sleep(args.poll_seconds)
        step_state.update({"status": "complete", "marker": str(marker), "completed_at_utc": _now()})
        _atomic_update(state_path, state)

    state.update({"status": "complete", "completed_at_utc": _now()})
    _atomic_update(state_path, state)


if __name__ == "__main__":
    main()
