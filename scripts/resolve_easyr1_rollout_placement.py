#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


def resolve_rollout_placement(
    config: dict[str, Any],
    gpu_ids: list[int],
    *,
    required_tensor_parallel_width: int = 1,
) -> dict[str, int]:
    trainer = config.get("trainer")
    rollout = config.get("worker", {}).get("rollout")
    if not isinstance(trainer, dict) or not isinstance(rollout, dict):
        raise ValueError("EasyR1 config must define trainer and worker.rollout mappings")

    nnodes = trainer.get("nnodes")
    configured_gpus = trainer.get("n_gpus_per_node")
    tensor_parallel_width = rollout.get("tensor_parallel_size")
    if nnodes != 1:
        raise ValueError(f"pilot smoke must be single-node, found trainer.nnodes={nnodes!r}")
    if configured_gpus != len(gpu_ids):
        raise ValueError(
            "GPU allocation does not match trainer.n_gpus_per_node: "
            f"{len(gpu_ids)} != {configured_gpus!r}"
        )
    if len(set(gpu_ids)) != len(gpu_ids):
        raise ValueError("GPU allocation contains duplicate IDs")
    if any(not isinstance(gpu, int) or gpu < 0 or gpu > 7 for gpu in gpu_ids):
        raise ValueError("GPU IDs must be unique integers in [0, 7]")
    if not isinstance(tensor_parallel_width, int) or tensor_parallel_width < 1:
        raise ValueError("worker.rollout.tensor_parallel_size must be a positive integer")
    if tensor_parallel_width != required_tensor_parallel_width:
        raise ValueError(
            "pilot smoke placement policy requires "
            f"TP{required_tensor_parallel_width}, found TP{tensor_parallel_width}"
        )
    if configured_gpus % tensor_parallel_width != 0:
        raise ValueError(
            "trainer.n_gpus_per_node must be divisible by rollout tensor-parallel width"
        )

    return {
        "tensor_parallel_width": tensor_parallel_width,
        "replica_count": configured_gpus // tensor_parallel_width,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve and enforce EasyR1 rollout placement from a frozen config."
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--gpu-list", required=True)
    parser.add_argument("--require-tp", type=int, default=1)
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    gpu_ids = [int(value) for value in args.gpu_list.split(",")]
    resolved = resolve_rollout_placement(
        config,
        gpu_ids,
        required_tensor_parallel_width=args.require_tp,
    )
    print(json.dumps(resolved, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
