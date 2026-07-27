#!/usr/bin/env python3
"""D2 test-time image-access ablation campaign (docs/registered_d2_testtime_ablation_v1.md).

Runs the eight registered model x condition cells four-at-a-time on the given
node's free GPUs, using the same evaluation entry point and decoding contract
as the registered pilot Geometry3K evaluations, with the condition supplied
explicitly (the matched-arm launcher deliberately refuses cross-condition
evaluation, so this campaign builds its own fail-closed cell manifests).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
MANIFEST = "data/geometry3k_caption_images_manifest.jsonl"
FORMAT_PROMPT = "artifacts/repos/EasyR1/examples/format_prompt/r1v.jinja"
EXPECTED_ROWS = 601
SEED = 20260710
MAX_TOKENS = 2048

MODELS = {
    "a1_seed1_step100": {
        "checkpoint": "checkpoints/pilot/mech_a1_real_resume60/global_step_100/actor/huggingface",
        "training_run": "experiments/runs/mech_a1_real_resume60_an12_20260714T080855Z",
        "arm": "a1_real",
    },
    "a1_seed2_step100": {
        "checkpoint": "checkpoints/pilot/mech_a1_real_seed2/global_step_100/actor/huggingface",
        "training_run": "experiments/runs/mech_a1_real_seed2_an29_20260716T164827Z",
        "arm": "a1_real",
    },
    "a2b_seed1_step100": {
        "checkpoint": "checkpoints/pilot/mech_a2b_noimage_retry4/global_step_100/actor/huggingface",
        "training_run": "experiments/runs/mech_a2b_noimage_retry4_an29_20260713T113556Z",
        "arm": "a2b_noimage",
    },
    "a2b_seed2_step100": {
        "checkpoint": "checkpoints/pilot/mech_a2b_noimage_seed2_resume20/global_step_100/actor/huggingface",
        "training_run": "experiments/runs/mech_a2b_noimage_seed2_resume20_an29_20260719T125447Z",
        "arm": "a2b_noimage",
    },
    "a1_seed3_step100": {
        "checkpoint": "checkpoints/pilot/mech_a1_real_seed3/global_step_100/actor/huggingface",
        "training_run": "experiments/runs/mech_a1_real_seed3_an29_20260722T050330Z",
        "arm": "a1_real",
    },
    "a2b_seed3_step100": {
        "checkpoint": "checkpoints/pilot/mech_a2b_noimage_seed3/global_step_100/actor/huggingface",
        "training_run": "experiments/runs/mech_a2b_noimage_seed3_an29_20260724T033754Z",
        "arm": "a2b_noimage",
    },
    "a2_seed1_step100": {
        "checkpoint": "checkpoints/pilot/mech_a2_gray_resume60_retry2/global_step_100/actor/huggingface",
        "training_run": "experiments/runs/mech_a2_gray_resume60_retry2_an12_20260715T165701Z",
        "arm": "a2_gray",
    },
    "a2_seed2_step100": {
        "checkpoint": "checkpoints/pilot/mech_a2_gray_seed2_resume20/global_step_100/actor/huggingface",
        "training_run": "experiments/runs/mech_a2_gray_seed2_resume20_an12_20260719T125918Z",
        "arm": "a2_gray",
    },
    "a2_seed3_step100": {
        "checkpoint": "checkpoints/pilot/mech_a2_gray_seed3/global_step_100/actor/huggingface",
        "training_run": "experiments/runs/mech_a2_gray_seed3_an12_20260722T145916Z",
        "arm": "a2_gray",
    },
    "a3_seed1_step100": {
        "checkpoint": "checkpoints/pilot/mech_a3_caption_resume20/global_step_100/actor/huggingface",
        "training_run": "experiments/runs/mech_a3_caption_resume20_an29_20260713T144233Z",
        "arm": "a3_caption",
    },
    "a3_seed2_step100": {
        "checkpoint": "checkpoints/pilot/mech_a3_caption_seed2/global_step_100/actor/huggingface",
        "training_run": "experiments/runs/mech_a3_caption_seed2_an29_20260720T125144Z",
        "arm": "a3_caption",
    },
    "a3_seed3_step100": {
        "checkpoint": "checkpoints/pilot/mech_a3_caption_seed3/global_step_100/actor/huggingface",
        "training_run": "experiments/runs/mech_a3_caption_seed3_an29_20260725T092128Z",
        "arm": "a3_caption",
    },
}
CELLS = [
    (f"{arm}_seed{seed}_step100", condition)
    for arm in ("a1", "a2", "a2b", "a3")
    for seed in (1, 2, 3)
    for condition in ("real", "gray", "none")
]


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


def _write(path: Path, payload: dict[str, Any]) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _ssh(node: str, command: str, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(["ssh", node, command], capture_output=True, text=True, timeout=timeout)


def gpu_free(node: str, gpu: int) -> bool:
    result = _ssh(node, f"nvidia-smi -i {gpu} --query-compute-apps=pid --format=csv,noheader,nounits")
    if result.returncode != 0:
        raise RuntimeError(f"GPU query failed {node}:{gpu}: {result.stderr.strip()}")
    return not result.stdout.strip()


def completed_cells() -> set[tuple[str, str]]:
    done: set[tuple[str, str]] = set()
    for manifest_path in (ROOT / "experiments/runs").glob("d2_testtime_*/run_manifest.json"):
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("job_type") == "d2_testtime_ablation_cell" and payload.get("status") == "complete":
            done.add((str(payload.get("model_key")), str(payload.get("condition"))))
    return done


def launch_cell(node: str, gpu: int, model_key: str, condition: str, git_hash: str) -> Path:
    spec = MODELS[model_key]
    checkpoint = ROOT / spec["checkpoint"]
    index_sha = _sha256(checkpoint / "model.safetensors.index.json")
    training_manifest = ROOT / spec["training_run"] / "run_manifest.json"
    if not training_manifest.is_file():
        raise RuntimeError(f"training manifest absent for {model_key}")
    run_id = f"d2_testtime_{model_key}_{condition}_{node}_gpu{gpu}_{_stamp()}"
    run_dir = ROOT / "experiments/runs" / run_id
    (run_dir / "logs").mkdir(parents=True)
    output = f"experiments/runs/{run_id}/predictions.jsonl"
    manifest_path = run_dir / "run_manifest.json"
    _write(
        manifest_path,
        {
            "schema_version": "blind-gains.run-manifest.v1",
            "run_id": run_id,
            "job_type": "d2_testtime_ablation_cell",
            "registration": "docs/registered_d2_testtime_ablation_v1.md",
            "node": node,
            "gpu_ids": [gpu],
            "tensor_parallel_width": 1,
            "replica_count": 1,
            "placement_justification": "One TP1 inference cell on a free non-trainer GPU; trainer GPUs are never touched.",
            "git_hash": git_hash,
            "model_key": model_key,
            "arm": spec["arm"],
            "condition": condition,
            "global_step": 100,
            "model_path": spec["checkpoint"],
            "checkpoint_index_sha256": index_sha,
            "source_training_run": spec["training_run"],
            "data_manifest": MANIFEST,
            "data_manifest_hash": _sha256(ROOT / MANIFEST),
            "expected_row_count": EXPECTED_ROWS,
            "prompt_contract": DEFAULT_PROMPT_CONTRACT.to_dict(),
            "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
            "decoding": "greedy",
            "max_tokens": MAX_TOKENS,
            "seed": SEED,
            "command": f"run_pilot_geo3k_step100_eval.py --arm {spec['arm']} --condition {condition}",
            "start_time_utc": _now(),
            "end_time_utc": None,
            "status": "running",
            "expected_artifacts": [output],
            "performance_values_opened": False,
        },
    )
    command = (
        f"cd '{ROOT}' && "
        f"(nohup env TRANSFORMERS_OFFLINE=1 HF_HOME={ROOT}/artifacts/hf_home "
        f"CUDA_VISIBLE_DEVICES={gpu} VLLM_WORKER_MULTIPROC_METHOD=spawn PYTHONHASHSEED=0 "
        f"PYTHONPATH={ROOT}:{ROOT}/artifacts/repos/EasyR1 "
        f".venv/bin/python scripts/run_pilot_geo3k_step100_eval.py "
        f"--arm {spec['arm']} --condition {condition} --model-path {spec['checkpoint']} "
        f"--manifest {MANIFEST} --format-prompt {FORMAT_PROMPT} --output {output} "
        f"--cache-dir experiments/runs/{run_id}/cache "
        f"--run-manifest experiments/runs/{run_id}/run_manifest.json "
        f"--source-training-manifest {spec['training_run']}/run_manifest.json "
        f"--checkpoint-index-sha256 {index_sha} --batch-size 4 --max-model-len 8192 "
        f"--max-tokens {MAX_TOKENS} --seed {SEED} --global-step 100 "
        f"> experiments/runs/{run_id}/logs/cell.log 2>&1 & echo $! > experiments/runs/{run_id}/logs/pid)"
    )
    result = _ssh(node, command)
    if result.returncode != 0:
        raise RuntimeError(f"cell spawn failed {model_key}/{condition}: {result.stderr.strip()}")
    return run_dir


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--node", choices=("an12", "an29"), required=True)
    parser.add_argument("--gpu-ids", nargs="+", type=int, required=True)
    parser.add_argument("--poll-seconds", type=int, default=60)
    args = parser.parse_args()
    if sorted(args.gpu_ids) != [4, 5, 6, 7]:
        raise ValueError("D2 cells run on GPUs 4-7 only")
    if not (ROOT / "docs/registered_d2_testtime_ablation_v1.md").is_file():
        raise RuntimeError("D2 registration is absent")
    git_hash = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()

    done = completed_cells()
    pending = [cell for cell in CELLS if cell not in done]
    print(json.dumps({"pending": len(pending), "already_complete": len(done)}))
    queue = list(pending)
    active: dict[int, tuple[Path, str, str]] = {}
    while queue or active:
        for gpu in list(args.gpu_ids):
            if gpu in active or not queue:
                continue
            if not gpu_free(args.node, gpu):
                continue
            model_key, condition = queue.pop(0)
            run_dir = launch_cell(args.node, gpu, model_key, condition, git_hash)
            active[gpu] = (run_dir, model_key, condition)
            print(json.dumps({"launched": f"{model_key}/{condition}", "gpu": gpu}))
            time.sleep(20)
        time.sleep(args.poll_seconds)
        for gpu, (run_dir, model_key, condition) in list(active.items()):
            predictions = run_dir / "predictions.jsonl"
            manifest_path = run_dir / "run_manifest.json"
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            if predictions.is_file():
                rows = sum(1 for line in predictions.read_text(encoding="utf-8").splitlines() if line.strip())
                if rows >= EXPECTED_ROWS:
                    payload.update(
                        {
                            "status": "complete",
                            "exit_code": 0,
                            "end_time_utc": _now(),
                            "artifacts_exist": True,
                            "rows": rows,
                            "predictions_sha256": _sha256(predictions),
                        }
                    )
                    _write(manifest_path, payload)
                    del active[gpu]
                    print(json.dumps({"complete": f"{model_key}/{condition}", "rows": rows}))
                    continue
            pid_file = run_dir / "logs/pid"
            if pid_file.is_file():
                pid = pid_file.read_text().strip()
                alive = _ssh(args.node, f"ps -o pid= -p {pid} | wc -l")
                if alive.returncode == 0 and int(alive.stdout.strip() or 0) == 0:
                    payload.update(
                        {"status": "fail", "exit_code": 1, "end_time_utc": _now(),
                         "failure": "cell process exited without complete output"}
                    )
                    _write(manifest_path, payload)
                    del active[gpu]
                    print(json.dumps({"failed": f"{model_key}/{condition}"}))
    print(json.dumps({"status": "campaign_complete"}))


if __name__ == "__main__":
    main()
