#!/usr/bin/env python3
"""Sequential X1 open-form realization campaign on one node's free GPUs.

Runs config models x openform_conditions cells; each cell shards the locked
R19 manifest four ways across the given GPUs, merges shard predictions, and
finalizes an immutable per-cell run manifest. Fail-closed on any shard error,
hash mismatch, or occupied GPU.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _ssh(node: str, command: str, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["ssh", node, command], capture_output=True, text=True, timeout=timeout
    )


def gpus_free(node: str, gpu_ids: list[int]) -> bool:
    ids = ",".join(str(gpu) for gpu in gpu_ids)
    result = _ssh(
        node,
        f"nvidia-smi -i {ids} --query-compute-apps=pid --format=csv,noheader,nounits",
    )
    if result.returncode != 0:
        raise RuntimeError(f"GPU query failed on {node}: {result.stderr.strip()}")
    return not result.stdout.strip()


def wait_for_free(node: str, gpu_ids: list[int], stable_polls: int, poll_seconds: int) -> None:
    streak = 0
    while streak < stable_polls:
        streak = streak + 1 if gpus_free(node, gpu_ids) else 0
        if streak < stable_polls:
            time.sleep(poll_seconds)


def completed_cells(prefix: str) -> set[tuple[str, str]]:
    done: set[tuple[str, str]] = set()
    runs_dir = ROOT / "experiments/runs"
    for manifest_path in runs_dir.glob(f"{prefix}_*/run_manifest.json"):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if (
            manifest.get("job_type") == "x1_openform_realization_cell"
            and manifest.get("status") == "complete"
            and manifest.get("exit_code") == 0
        ):
            done.add((str(manifest.get("model_key")), str(manifest.get("condition"))))
    return done


def run_cell(
    *,
    config: dict,
    config_path: Path,
    config_hash: str,
    node: str,
    gpu_ids: list[int],
    model_key: str,
    condition: str,
    git_hash: str,
    override_path: Path | None,
    stable_polls: int,
    poll_seconds: int,
) -> None:
    contract = config["openform_contract"]
    manifest_file = ROOT / str(contract["manifest"])
    if _sha256(manifest_file) != str(contract["manifest_sha256"]):
        raise RuntimeError("locked open-form manifest hash mismatch")
    model_spec = config["models"][model_key]
    model_path = ROOT / str(model_spec["path"])
    index_path = model_path / "model.safetensors.index.json"
    if _sha256(index_path) != str(model_spec["model_index_sha256"]):
        raise RuntimeError(f"model index hash mismatch for {model_key}")
    if condition == "mismatched_real":
        assert override_path is not None
        if _sha256(override_path) != str(config["image_override_map"]["sha256"]):
            raise RuntimeError("override map hash mismatch")

    wait_for_free(node, gpu_ids, stable_polls, poll_seconds)
    run_id = f"x1_openform_{model_key}_{condition}_{node}_{_stamp()}"
    run_dir = ROOT / "experiments/runs" / run_id
    (run_dir / "logs").mkdir(parents=True)
    (run_dir / "shards").mkdir()
    (run_dir / "pids").mkdir()
    num_shards = int(contract["num_shards"])
    override_arg = (
        f" --image-override-map '{override_path.relative_to(ROOT)}'"
        if condition == "mismatched_real"
        else ""
    )
    manifest = {
        "schema_version": "blind-gains.run-manifest.v1",
        "run_id": run_id,
        "job_type": "x1_openform_realization_cell",
        "registration": "docs/registered_x1_matrix_v1.md",
        "node": node,
        "gpu_ids": gpu_ids,
        "tensor_parallel_width": 1,
        "replica_count": num_shards,
        "placement_justification": "Four TP1 greedy open-form realization shards on the dispatch-approved free GPUs; trainer GPUs 0-3 are never touched.",
        "git_hash": git_hash,
        "config_path": str(config_path.relative_to(ROOT)),
        "config_hash": config_hash,
        "data_manifest": str(contract["manifest"]),
        "data_manifest_hash": str(contract["manifest_sha256"]),
        "model_key": model_key,
        "model_path": str(model_spec["path"]),
        "model_index_sha256": str(model_spec["model_index_sha256"]),
        "condition": condition,
        "max_new_tokens": int(contract["max_new_tokens"]),
        "decoding": str(contract["decoding"]),
        "seed": int(contract["seed"]),
        "command": f"scripts/run_x1_openform_queue.py cell {model_key}/{condition}",
        "start_time_utc": _now(),
        "end_time_utc": None,
        "status": "running",
        "expected_artifacts": [f"experiments/runs/{run_id}/predictions.jsonl"],
    }
    _write_json(run_dir / "run_manifest.json", manifest)

    for shard in range(num_shards):
        gpu = gpu_ids[shard]
        out = f"experiments/runs/{run_id}/shards/predictions_shard_{shard}.jsonl"
        log = f"experiments/runs/{run_id}/logs/shard_{shard}.log"
        pid = f"experiments/runs/{run_id}/pids/shard_{shard}.pid"
        command = (
            f"cd '{ROOT}' && source .venv/bin/activate && "
            f"(nohup env PYTHONUNBUFFERED=1 PYTHONHASHSEED={contract['seed']} TRANSFORMERS_OFFLINE=1 "
            f"HF_HOME='{ROOT}/artifacts/hf_home' CUDA_VISIBLE_DEVICES={gpu} "
            f"python scripts/eval_qwen_vl_fliptrack.py --model-path '{model_spec['path']}' "
            f"--manifest '{contract['manifest']}' --output '{out}' "
            f"--num-shards {num_shards} --shard-index {shard} --image-mode '{condition}' "
            f"--image-cache-dir 'experiments/runs/{run_id}/image_cache' "
            f"--seed {contract['seed']} --noise-seed {contract['seed']} "
            f"--max-new-tokens {contract['max_new_tokens']}{override_arg} "
            f"> '{log}' 2>&1 < /dev/null & echo $! > '{pid}')"
        )
        result = _ssh(node, command)
        if result.returncode != 0:
            raise RuntimeError(f"shard {shard} spawn failed: {result.stderr.strip()}")

    expected = [run_dir / "shards" / f"predictions_shard_{i}.jsonl" for i in range(num_shards)]
    while True:
        time.sleep(poll_seconds)
        if all(path.is_file() for path in expected):
            break
        pids = [
            (run_dir / "pids" / f"shard_{i}.pid").read_text().strip()
            for i in range(num_shards)
            if (run_dir / "pids" / f"shard_{i}.pid").is_file()
        ]
        if pids:
            alive = _ssh(node, f"ps -o pid= -p {','.join(pids)} | wc -l")
            missing = [
                i for i, path in enumerate(expected) if not path.is_file()
            ]
            if alive.returncode == 0 and int(alive.stdout.strip() or 0) == 0 and missing:
                manifest.update(
                    {"status": "fail", "exit_code": 1, "end_time_utc": _now(),
                     "failure": f"shards {missing} died without output"}
                )
                _write_json(run_dir / "run_manifest.json", manifest)
                raise RuntimeError(f"cell {run_id}: shards {missing} died without output")

    rows: list[str] = []
    for path in expected:
        rows.extend(path.read_text(encoding="utf-8").splitlines())
    if len(rows) != int(config["candidate_registry"]["pair_count"]):
        manifest.update({"status": "fail", "exit_code": 1, "end_time_utc": _now(),
                         "failure": f"merged rows {len(rows)} != 1200"})
        _write_json(run_dir / "run_manifest.json", manifest)
        raise RuntimeError(f"cell {run_id}: merged rows {len(rows)} != 1200")
    predictions = run_dir / "predictions.jsonl"
    predictions.write_text("\n".join(rows) + "\n", encoding="utf-8")
    manifest.update(
        {
            "status": "complete",
            "exit_code": 0,
            "end_time_utc": _now(),
            "artifacts_exist": True,
            "predictions_sha256": _sha256(predictions),
            "rows": len(rows),
        }
    )
    _write_json(run_dir / "run_manifest.json", manifest)
    print(json.dumps({"cell": run_id, "rows": len(rows), "status": "complete"}))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--node", choices=("an12", "an29"), required=True)
    parser.add_argument("--gpu-ids", nargs="+", type=int, required=True)
    parser.add_argument("--stable-polls", type=int, default=2)
    parser.add_argument("--poll-seconds", type=int, default=60)
    args = parser.parse_args()
    if sorted(args.gpu_ids) != [4, 5, 6, 7]:
        raise ValueError("dispatch restricts X1 open-form cells to GPUs 4-7")

    config_path = args.config.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config_hash = _sha256(config_path)
    git_hash = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()
    registration = ROOT / "docs/registered_x1_matrix_v1.md"
    if not registration.is_file():
        raise RuntimeError("X1 registration document is absent")
    override_path = ROOT / str(config["image_override_map"]["path"])

    done = completed_cells("x1_openform")
    cells = [
        (model_key, condition)
        for model_key in config["models"]
        for condition in config["openform_conditions"]
        if (model_key, condition) not in done
    ]
    print(json.dumps({"pending_cells": len(cells), "already_complete": len(done)}))
    for model_key, condition in cells:
        run_cell(
            config=config,
            config_path=config_path,
            config_hash=config_hash,
            node=args.node,
            gpu_ids=list(args.gpu_ids),
            model_key=model_key,
            condition=condition,
            git_hash=git_hash,
            override_path=override_path if condition == "mismatched_real" else None,
            stable_polls=args.stable_polls,
            poll_seconds=args.poll_seconds,
        )
    print(json.dumps({"status": "campaign_complete", "cells_run": len(cells)}))


if __name__ == "__main__":
    main()
