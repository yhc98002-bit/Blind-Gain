#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import statistics
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
NODES = ("an12", "an29")
FATAL_PATTERNS = (
    "no space left on device",
    "cuda out of memory",
    "nccl error",
    "raytaskerror",
    "traceback (most recent call last)",
    "loss is nan",
    "reward is nan",
)


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_ssh(node: str, command: str) -> str:
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


def _csv_rows(text: str, width: int) -> list[list[str]]:
    rows = []
    for row in csv.reader(text.splitlines(), skipinitialspace=True):
        values = [value.strip() for value in row]
        if len(values) == width:
            rows.append(values)
    return rows


def collect_node(node: str) -> dict[str, Any]:
    gpu_text = _run_ssh(
        node,
        "nvidia-smi --query-gpu=index,uuid,utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu,power.draw,pstate --format=csv,noheader,nounits",
    )
    gpus = []
    for row in _csv_rows(gpu_text, 9):
        gpus.append(
            {
                "index": int(row[0]), "uuid": row[1], "gpu_util_pct": float(row[2]),
                "memory_util_pct": float(row[3]), "memory_used_mib": float(row[4]),
                "memory_total_mib": float(row[5]), "temperature_c": float(row[6]),
                "power_w": float(row[7]), "pstate": row[8],
            }
        )
    if [item["index"] for item in gpus] != list(range(8)):
        raise RuntimeError(f"{node} did not report exactly GPUs 0-7")

    process_text = _run_ssh(
        node,
        "nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_gpu_memory --format=csv,noheader,nounits 2>/dev/null || true",
    )
    processes = []
    for uuid, pid_text, process_name, used_text in _csv_rows(process_text, 4):
        if not pid_text.isdigit():
            continue
        pid = int(pid_text)
        details = _run_ssh(
            node,
            f"ps -o user=,stat=,etime=,pcpu=,pmem=,wchan:32=,args= -p {pid} 2>/dev/null || true",
        ).strip()
        processes.append(
            {
                "gpu_uuid": uuid, "gpu_index": next((g["index"] for g in gpus if g["uuid"] == uuid), None),
                "pid": pid, "nvidia_process_name": process_name, "gpu_memory_mib": float(used_text),
                "ps": details or None,
            }
        )

    storage_text = _run_ssh(
        node,
        "printf 'BLOCKS\\n'; df -Pk /tmp /dev/shm; printf 'INODES\\n'; df -Pi /tmp",
    )
    memory_text = _run_ssh(
        node,
        "awk '/^(MemTotal|MemAvailable|SwapTotal|SwapFree):/ {print $1, $2}' /proc/meminfo",
    )
    memory_kib = {}
    for line in memory_text.splitlines():
        key, value = line.rstrip(":").split()
        memory_kib[key.rstrip(":")] = int(value)
    required_memory = {"MemTotal", "MemAvailable", "SwapTotal", "SwapFree"}
    if set(memory_kib) != required_memory:
        raise RuntimeError(f"{node} returned incomplete host memory data: {memory_kib}")
    top_processes = _run_ssh(
        node,
        "ps -u \"$USER\" -o pid=,rss=,pcpu=,pmem=,etime=,args= --sort=-rss | head -n 16",
    )
    return {
        "node": node,
        "gpus": gpus,
        "processes": processes,
        "storage_raw": storage_text,
        "host_memory": {
            "mem_total_kib": memory_kib["MemTotal"],
            "mem_available_kib": memory_kib["MemAvailable"],
            "mem_available_pct": round(
                100 * memory_kib["MemAvailable"] / memory_kib["MemTotal"], 4
            ),
            "swap_total_kib": memory_kib["SwapTotal"],
            "swap_free_kib": memory_kib["SwapFree"],
        },
        "top_user_processes_by_rss": top_processes.splitlines(),
    }


def _max_step(log_path: Path) -> int | None:
    if not log_path.is_file():
        return None
    maximum: int | None = None
    with log_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                value = json.loads(line).get("step")
            except (json.JSONDecodeError, AttributeError):
                continue
            if isinstance(value, int):
                maximum = value if maximum is None else max(maximum, value)
    return maximum


def _tail_fatal_patterns(path: Path) -> list[str]:
    if not path.is_file():
        return []
    with path.open("rb") as handle:
        handle.seek(max(0, path.stat().st_size - 256 * 1024))
        text = handle.read().decode("utf-8", errors="replace").lower()
    return [pattern for pattern in FATAL_PATTERNS if pattern in text]


def collect_run(run_dir: Path) -> dict[str, Any]:
    manifest_path = run_dir / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checkpoint_root = Path(str(manifest["checkpoint_path"]))
    metric_log = checkpoint_root / "experiment_log.jsonl"
    stdout = ROOT / str(manifest["stdout_stderr_log"])
    pid_file = run_dir / "pids" / str(manifest["node"] + ".pid")
    wrapper_pid = int(pid_file.read_text(encoding="ascii").strip()) if pid_file.is_file() else None
    wrapper_alive = False
    if wrapper_pid is not None:
        wrapper_alive = bool(_run_ssh(str(manifest["node"]), f"ps -p {wrapper_pid} -o pid= 2>/dev/null || true").strip())
    return {
        "run_dir": str(run_dir), "run_id": manifest.get("run_id"), "arm": manifest.get("arm"),
        "node": manifest.get("node"), "gpu_ids": manifest.get("gpu_ids", []),
        "manifest_status": manifest.get("status"), "wrapper_pid": wrapper_pid,
        "wrapper_alive": wrapper_alive, "max_logged_step": _max_step(metric_log),
        "metric_log": str(metric_log), "metric_log_mtime_ns": metric_log.stat().st_mtime_ns if metric_log.exists() else None,
        "stdout_log": str(stdout), "stdout_log_mtime_ns": stdout.stat().st_mtime_ns if stdout.exists() else None,
        "fatal_patterns": _tail_fatal_patterns(stdout),
    }


def classify_run_sample(
    current: dict[str, Any], previous: dict[str, Any] | None, assigned_gpu_util: float
) -> dict[str, Any]:
    reasons: list[str] = []
    status = "healthy"
    if current.get("manifest_status") == "fail":
        return {"health": "unhealthy", "reasons": ["manifest_failed"]}
    if current.get("manifest_status") == "running" and not current.get("wrapper_alive"):
        return {"health": "unhealthy", "reasons": ["running_manifest_wrapper_missing"]}
    if current.get("fatal_patterns"):
        return {"health": "unhealthy", "reasons": [f"fatal_log_pattern:{value}" for value in current["fatal_patterns"]]}
    if previous is None:
        return {"health": "observing", "reasons": ["baseline_sample"]}
    if current.get("max_logged_step") != previous.get("max_logged_step"):
        reasons.append("optimizer_or_validation_step_advanced")
    if current.get("stdout_log_mtime_ns") != previous.get("stdout_log_mtime_ns"):
        reasons.append("stdout_advanced")
    if not reasons:
        status = "warning"
        reasons.append("no_progress_in_this_sampling_interval")
    if assigned_gpu_util < 5:
        reasons.append("assigned_gpu_util_below_5pct")
    return {"health": status, "reasons": reasons}


def cadence_sleep_seconds(
    *, sample_started: float, collection_finished: float, interval_seconds: float, deadline: float
) -> float:
    """Return sleep needed for start-to-start cadence without accumulating collection time."""
    next_start = min(sample_started + interval_seconds, deadline)
    return max(0.0, next_start - collection_finished)


def _atomic_write(path: Path, text: str) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite monitor output: {path}")
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def summarize(samples: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    gpu_summary = []
    for node in NODES:
        for index in range(8):
            values = [next(g for g in sample["nodes"][node]["gpus"] if g["index"] == index) for sample in samples]
            gpu_summary.append(
                {
                    "node": node, "gpu_index": index,
                    "mean_gpu_util_pct": round(statistics.fmean(v["gpu_util_pct"] for v in values), 3),
                    "min_gpu_util_pct": min(v["gpu_util_pct"] for v in values),
                    "max_gpu_util_pct": max(v["gpu_util_pct"] for v in values),
                    "max_memory_used_mib": max(v["memory_used_mib"] for v in values),
                    "max_temperature_c": max(v["temperature_c"] for v in values),
                    "samples_below_5pct": sum(v["gpu_util_pct"] < 5 for v in values),
                }
            )
    run_summary = []
    unhealthy = False
    for specification in config["runs"]:
        run_id = specification["run_id"]
        rows = [next(r for r in sample["runs"] if r["run_id"] == run_id) for sample in samples]
        health_values = [row["health"]["health"] for row in rows]
        unhealthy = unhealthy or "unhealthy" in health_values
        run_summary.append(
            {
                "run_id": run_id, "arm": rows[-1]["arm"], "node": rows[-1]["node"],
                "gpu_ids": rows[-1]["gpu_ids"], "first_step": rows[0]["max_logged_step"],
                "last_step": rows[-1]["max_logged_step"],
                "step_advanced": rows[-1]["max_logged_step"] != rows[0]["max_logged_step"],
                "stdout_advanced": rows[-1]["stdout_log_mtime_ns"] != rows[0]["stdout_log_mtime_ns"],
                "health_observations": {value: health_values.count(value) for value in sorted(set(health_values))},
                "final_manifest_status": rows[-1]["manifest_status"],
            }
        )
    all_processes = {(node, process["pid"], process["gpu_index"], process["nvidia_process_name"])
                     for sample in samples for node in NODES for process in sample["nodes"][node]["processes"]}
    host_memory_summary = []
    for node in NODES:
        values = [sample["nodes"][node]["host_memory"] for sample in samples]
        host_memory_summary.append(
            {
                "node": node,
                "min_mem_available_gib": round(
                    min(value["mem_available_kib"] for value in values) / 1024**2, 3
                ),
                "min_mem_available_pct": min(
                    value["mem_available_pct"] for value in values
                ),
                "max_swap_used_gib": round(
                    max(
                        value["swap_total_kib"] - value["swap_free_kib"]
                        for value in values
                    )
                    / 1024**2,
                    3,
                ),
                "samples_below_150_gib": sum(
                    value["mem_available_kib"] < 150 * 1024**2 for value in values
                ),
                "samples_below_75_gib": sum(
                    value["mem_available_kib"] < 75 * 1024**2 for value in values
                ),
            }
        )
    return {
        "schema_version": "blind-gains.gpu-health-summary.v1", "status": "unhealthy" if unhealthy else "complete",
        "scientific_gate_decision": None, "started_at_utc": samples[0]["observed_at_utc"],
        "ended_at_utc": samples[-1]["observed_at_utc"], "sample_count": len(samples),
        "interval_seconds": config["interval_seconds"], "requested_duration_seconds": config["duration_seconds"],
        "gpu_count": 16, "unique_gpu_processes": [
            {"node": item[0], "pid": item[1], "gpu_index": item[2], "process_name": item[3]}
            for item in sorted(all_processes)
        ],
        "gpu_summary": gpu_summary, "run_summary": run_summary,
        "host_memory_summary": host_memory_summary,
        "interpretation": "GPU idleness alone is not a failure; health combines process survival, logs, steps, and fatal-error evidence.",
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# 16-GPU Health Monitor", "", f"Status: `{summary['status']}`", "",
        f"Observed {summary['gpu_count']} GPUs in {summary['sample_count']} samples from "
        f"`{summary['started_at_utc']}` through `{summary['ended_at_utc']}`.", "",
        "## Tracked runs", "", "| Run | Arm | Node/GPUs | First step | Last step | Step advanced | Final status |", "|---|---|---|---:|---:|---|---|",
    ]
    for row in summary["run_summary"]:
        lines.append(f"| `{row['run_id']}` | `{row['arm']}` | `{row['node']}:{','.join(map(str,row['gpu_ids']))}` | {row['first_step']} | {row['last_step']} | {row['step_advanced']} | `{row['final_manifest_status']}` |")
    lines += [
        "", "## Host memory", "",
        "| Node | Minimum available GiB | Minimum available | Maximum swap used GiB | Samples <150 GiB | Samples <75 GiB |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary["host_memory_summary"]:
        lines.append(
            f"| `{row['node']}` | {row['min_mem_available_gib']:.1f} | "
            f"{row['min_mem_available_pct']:.1f}% | {row['max_swap_used_gib']:.1f} | "
            f"{row['samples_below_150_gib']} | {row['samples_below_75_gib']} |"
        )
    lines += ["", "## GPU summary", "", "| GPU | Mean util | Range | Max memory MiB | Max temp C | Samples <5% |", "|---|---:|---:|---:|---:|---:|"]
    for row in summary["gpu_summary"]:
        lines.append(f"| `{row['node']}:{row['gpu_index']}` | {row['mean_gpu_util_pct']:.1f}% | {row['min_gpu_util_pct']:.0f}-{row['max_gpu_util_pct']:.0f}% | {row['max_memory_used_mib']:.0f} | {row['max_temperature_c']:.0f} | {row['samples_below_5pct']} |")
    lines += ["", "No scientific gate decision is made. GPU idleness alone is not classified as failure.", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if config.get("schema_version") != "blind-gains.gpu-health-monitor-config.v1":
        raise ValueError("unsupported monitor config")
    raw_path = ROOT / config["samples_jsonl"]
    summary_json = ROOT / config["summary_json"]
    summary_md = ROOT / config["summary_markdown"]
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    if raw_path.exists() or summary_json.exists() or summary_md.exists():
        raise FileExistsError("monitor outputs must be immutable and new")
    samples: list[dict[str, Any]] = []
    deadline = time.monotonic() + config["duration_seconds"]
    previous_runs: dict[str, dict[str, Any]] = {}
    with raw_path.open("x", encoding="utf-8", buffering=1) as handle:
        while True:
            sample_started = time.monotonic()
            nodes = {node: collect_node(node) for node in NODES}
            runs = []
            for specification in config["runs"]:
                current = collect_run(ROOT / specification["run_dir"])
                assigned = [next(g for g in nodes[current["node"]]["gpus"] if g["index"] == index)["gpu_util_pct"] for index in current["gpu_ids"]]
                current["assigned_mean_gpu_util_pct"] = statistics.fmean(assigned)
                current["health"] = classify_run_sample(current, previous_runs.get(current["run_id"]), current["assigned_mean_gpu_util_pct"])
                previous_runs[current["run_id"]] = current
                runs.append(current)
            sample = {"schema_version": "blind-gains.gpu-health-sample.v1", "observed_at_utc": _now(), "nodes": nodes, "runs": runs}
            handle.write(json.dumps(sample, sort_keys=True) + "\n")
            samples.append(sample)
            collection_finished = time.monotonic()
            remaining = deadline - collection_finished
            if remaining <= 0:
                break
            time.sleep(
                cadence_sleep_seconds(
                    sample_started=sample_started,
                    collection_finished=collection_finished,
                    interval_seconds=config["interval_seconds"],
                    deadline=deadline,
                )
            )
    summary = summarize(samples, config)
    summary["samples_jsonl"] = str(raw_path.relative_to(ROOT))
    summary["samples_sha256"] = _sha256(raw_path)
    _atomic_write(summary_json, json.dumps(summary, indent=2, sort_keys=True) + "\n")
    _atomic_write(summary_md, render_markdown(summary))


if __name__ == "__main__":
    main()
