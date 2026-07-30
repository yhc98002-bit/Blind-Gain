#!/usr/bin/env python3
"""Run E1c blind Layer-1 cells sequentially on one GPU, one manifested run per config.

Each cell reuses scripts/eval_layer1_blind.py unchanged, so the vision-token guard
that makes a blind column trustworthy still fires per row.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_manifest_job import run_manifest_job  # noqa: E402

STANDARD_PROTOCOL = (
    "remove image message, image token, and image tensor; "
    "retain question text and options verbatim"
)
# MMMUDataset.build_prompt runs split_MMMU, which consumes the "<image N>" markers
# as it interleaves the real images, so the with-image text never contains them.
MMMU_PROTOCOL = (
    "remove image message, image token, and image tensor; retain question text and "
    "options verbatim except the '<image N>' markers that VLMEvalKit "
    "MMMUDataset.split_MMMU consumes when interleaving images"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--node", required=True)
    parser.add_argument("--gpu", required=True)
    parser.add_argument("--queue-log", required=True)
    parser.add_argument(
        "--cell", action="append", required=True, help="RUN_TAG=configs/eval/<config>.json"
    )
    args = parser.parse_args()

    git_hash = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()

    queue_log = Path(args.queue_log)
    queue_log.parent.mkdir(parents=True, exist_ok=True)

    def say(message: str) -> None:
        with queue_log.open("a", encoding="utf-8") as handle:
            handle.write(f"[{utc()}] {message}\n")
            handle.flush()

    say(f"QUEUE START node={args.node} gpu={args.gpu} git={git_hash} cells={len(args.cell)}")
    for cell in args.cell:
        tag, config_rel = cell.split("=", 1)
        config = json.loads((ROOT / config_rel).read_text(encoding="utf-8"))
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_id = f"layer1_blind_{tag}_{args.node}_{stamp}"
        run_dir = ROOT / "experiments" / "runs" / run_id
        (run_dir / "logs").mkdir(parents=True, exist_ok=True)
        output = f"experiments/runs/{run_id}/predictions.jsonl"
        metrics = f"experiments/runs/{run_id}/metrics.json"
        command = (
            f"TRANSFORMERS_OFFLINE=1 HF_HOME={ROOT}/artifacts/hf_home "
            f"CUDA_VISIBLE_DEVICES={args.gpu} artifacts/envs/vlmevalkit/bin/python "
            f"scripts/eval_layer1_blind.py --config {config_rel} "
            f"--output {output} --metrics-output {metrics}"
        )
        manifest = {
            "run_id": run_id,
            "job_type": "p1_2_layer1_image_removed_evaluation",
            "experiment": "E1c_f0_visual_necessity_blind_columns",
            "node": args.node,
            "gpu_allocation": [args.gpu],
            "gpu_ids": [int(args.gpu)],
            "git_hash": git_hash,
            "config_path": config_rel,
            "config_hash": sha256(ROOT / config_rel),
            "data_manifest": config["input_tsv"],
            "data_manifest_hash": sha256(ROOT / config["input_tsv"]),
            "dataset_type": config["dataset_type"],
            "model_path": config["model_path"],
            "seed": config["seed"],
            "image_protocol": (
                MMMU_PROTOCOL if config["dataset_type"] == "mmmu" else STANDARD_PROTOCOL
            ),
            "command": command,
            "start_time_utc": utc(),
            "end_time_utc": None,
            "status": "running",
            "expected_artifacts": [output, metrics],
        }
        manifest_path = run_dir / "run_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        say(f"START {run_id} config={config_rel} dataset_type={config['dataset_type']}")
        code = run_manifest_job(manifest_path, run_dir / "logs" / f"{args.node}_gpu{args.gpu}.log")
        say(f"END   {run_id} exit={code}")
    say("QUEUE COMPLETE")


if __name__ == "__main__":
    main()
