#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any


REQUIRED_CELLS = {
    ("3b", "image", "real"),
    ("3b", "image", "gray"),
    ("3b", "image", "noise"),
    ("3b", "caption", "caption"),
    ("7b", "image", "real"),
    ("7b", "image", "gray"),
    ("7b", "image", "noise"),
    ("7b", "caption", "caption"),
    ("3b", "image", "mild"),
    ("3b", "image", "medium"),
    ("3b", "image", "severe"),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_config(config: dict[str, Any], root: Path) -> None:
    required = {
        "node",
        "shard_offset",
        "num_shards",
        "gpu_list",
        "max_new_tokens",
        "image_manifest",
        "models",
        "caption_inputs",
        "cells",
    }
    missing = required - set(config)
    if missing:
        raise ValueError(f"R20 queue config missing fields: {sorted(missing)}")
    cells = config["cells"]
    if not isinstance(cells, list) or not cells:
        raise ValueError("R20 queue cells must be a nonempty list")
    observed = {(cell.get("model"), cell.get("kind"), cell.get("mode")) for cell in cells}
    if observed != REQUIRED_CELLS or len(cells) != len(REQUIRED_CELLS):
        missing_cells = sorted(REQUIRED_CELLS - observed)
        extra_cells = sorted(observed - REQUIRED_CELLS)
        raise ValueError(f"R20 queue matrix mismatch: missing={missing_cells}, extra={extra_cells}")
    ids = [str(cell.get("id", "")) for cell in cells]
    if any(not cell_id for cell_id in ids) or len(ids) != len(set(ids)):
        raise ValueError("R20 queue cell ids must be nonempty and unique")
    if set(config["models"]) != {"3b", "7b"} or set(config["caption_inputs"]) != {"3b", "7b"}:
        raise ValueError("R20 queue must define 3b and 7b model/caption paths")
    required_paths = [config["image_manifest"], *config["models"].values(), *config["caption_inputs"].values()]
    for value in required_paths:
        if not (root / value).exists():
            raise FileNotFoundError(root / value)


def build_launch_command(config: dict[str, Any], cell: dict[str, Any], run_dir: str) -> list[str]:
    common = [
        str(config["node"]),
        str(config["shard_offset"]),
        str(config["num_shards"]),
        str(config["models"][cell["model"]]),
    ]
    if cell["kind"] == "image":
        return [
            "scripts/launch_fliptrack_eval_shards.sh",
            *common,
            str(config["image_manifest"]),
            run_dir,
            str(config["max_new_tokens"]),
            str(config["gpu_list"]),
            str(cell["mode"]),
        ]
    if cell["kind"] == "caption":
        return [
            "scripts/launch_caption_qa_shards.sh",
            *common,
            str(config["caption_inputs"][cell["model"]]),
            run_dir,
            str(config["gpu_list"]),
            str(config["max_new_tokens"]),
        ]
    raise ValueError(f"unsupported R20 cell kind: {cell['kind']}")


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _manifest_status(root: Path, run_dir: str) -> str:
    manifest = root / run_dir / "run_manifest.json"
    if not manifest.is_file():
        return "missing"
    return str(json.loads(manifest.read_text(encoding="utf-8")).get("status", "missing"))


def _gpu_memory(root: Path, config: dict[str, Any]) -> dict[int, int]:
    completed = subprocess.run(
        [
            "ssh",
            str(config["node"]),
            "nvidia-smi --query-gpu=index,memory.used --format=csv,noheader,nounits",
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    result = {}
    for line in completed.stdout.splitlines():
        index, memory = (part.strip() for part in line.split(",", maxsplit=1))
        result[int(index)] = int(memory)
    return result


def _wait_for_free_gpus(root: Path, config: dict[str, Any], poll_seconds: int) -> None:
    selected = [int(value) for value in str(config["gpu_list"]).split()]
    threshold = int(config.get("free_memory_threshold_mib", 1024))
    while True:
        memory = _gpu_memory(root, config)
        occupied = {index: memory.get(index) for index in selected if memory.get(index, threshold + 1) > threshold}
        if not occupied:
            return
        print(f"gpu_wait node={config['node']} occupied={occupied}", flush=True)
        time.sleep(poll_seconds)


def _new_run_dir(cell_id: str) -> str:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"experiments/runs/fliptrack_r20_{cell_id}_an12_{stamp}"


def _launch_cell(root: Path, config: dict[str, Any], cell: dict[str, Any], state: dict[str, Any]) -> None:
    run_dir = _new_run_dir(str(cell["id"]))
    command = build_launch_command(config, cell, run_dir)
    print("launch " + " ".join(command), flush=True)
    subprocess.run(command, cwd=root, check=True)
    state["cells"][cell["id"]] = {"run_dir": run_dir, "aggregate_run": None}


def _wait_for_cell(root: Path, cell: dict[str, Any], state: dict[str, Any], poll_seconds: int) -> None:
    run_dir = state["cells"][cell["id"]]["run_dir"]
    while True:
        status = _manifest_status(root, run_dir)
        if status == "complete":
            print(f"cell_complete id={cell['id']} run={run_dir}", flush=True)
            return
        if status == "fail":
            raise RuntimeError(f"R20 cell failed: {cell['id']} at {run_dir}")
        if status == "missing":
            raise FileNotFoundError(root / run_dir / "run_manifest.json")
        print(f"cell_wait id={cell['id']} status={status}", flush=True)
        time.sleep(poll_seconds)


def _aggregate(root: Path, cell: dict[str, Any], state: dict[str, Any]) -> None:
    record = state["cells"][cell["id"]]
    existing = record.get("aggregate_run")
    if existing and _manifest_status(root, existing) == "complete":
        return
    completed = subprocess.run(
        ["scripts/launch_fliptrack_aggregate.sh", record["run_dir"], str(cell["id"])],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if not lines or not lines[-1].startswith("experiments/runs/"):
        raise RuntimeError(f"could not identify aggregate run for {cell['id']}: {completed.stdout!r}")
    record["aggregate_run"] = lines[-1]
    print(f"aggregate_complete id={cell['id']} run={record['aggregate_run']}", flush=True)


def run_queue(config_path: Path, state_path: Path, poll_seconds: int) -> None:
    root = Path(__file__).resolve().parents[1]
    config = json.loads(config_path.read_text(encoding="utf-8"))
    validate_config(config, root)
    config_hash = sha256_file(config_path)
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("config_sha256") != config_hash:
            raise ValueError("R20 queue state/config hash mismatch")
    else:
        state = {
            "schema_version": "blind-gains.fliptrack-r20-queue.v1",
            "status": "running",
            "config": str(config_path),
            "config_sha256": config_hash,
            "cells": {},
        }
        for cell in config["cells"]:
            if cell.get("existing_run"):
                state["cells"][cell["id"]] = {
                    "run_dir": cell["existing_run"],
                    "aggregate_run": None,
                }
        _atomic_write(state_path, state)

    cells = config["cells"]
    for index, cell in enumerate(cells):
        if cell["id"] not in state["cells"]:
            _wait_for_free_gpus(root, config, poll_seconds)
            _launch_cell(root, config, cell, state)
            _atomic_write(state_path, state)
        _wait_for_cell(root, cell, state, poll_seconds)
        if index + 1 < len(cells):
            next_cell = cells[index + 1]
            if next_cell["id"] not in state["cells"]:
                _wait_for_free_gpus(root, config, poll_seconds)
                _launch_cell(root, config, next_cell, state)
                _atomic_write(state_path, state)
        _aggregate(root, cell, state)
        _atomic_write(state_path, state)

    state["status"] = "complete"
    state["completed_at_utc"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _atomic_write(state_path, state)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--poll-seconds", type=int, default=60)
    args = parser.parse_args()
    if args.poll_seconds < 1:
        raise ValueError("poll seconds must be positive")
    run_queue(args.config, args.state, args.poll_seconds)


if __name__ == "__main__":
    main()
