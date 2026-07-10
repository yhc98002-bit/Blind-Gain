#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import socket
import statistics
from pathlib import Path

import torch
import torch.distributed as dist


def bus_bandwidth_gbps(nbytes: int, seconds: float, world_size: int) -> float:
    if nbytes <= 0 or seconds <= 0 or world_size < 2:
        raise ValueError("bandwidth inputs must be positive and world_size must be at least 2")
    algorithm_gbps = nbytes / seconds / 1e9
    return algorithm_gbps * (2 * (world_size - 1) / world_size)


def _percentile(values: list[float], fraction: float) -> float:
    if not values or not 0.0 < fraction <= 1.0:
        raise ValueError("percentile requires values and a fraction in (0, 1]")
    ordered = sorted(values)
    index = math.ceil(fraction * len(ordered)) - 1
    return ordered[index]


def _atomic_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = Path(f"{path}.partial")
    if path.exists() or partial.exists():
        raise FileExistsError(f"refusing to overwrite benchmark artifact: {path}")
    partial.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(partial, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tensor-mib", type=int, default=256)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--expected-world-size", type=int, default=16)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if min(args.tensor_mib, args.warmup, args.iterations) <= 0:
        raise ValueError("tensor size, warmup, and iteration count must be positive")

    dist.init_process_group("nccl")
    try:
        rank = dist.get_rank()
        world_size = dist.get_world_size()
        if world_size != args.expected_world_size:
            raise RuntimeError(f"expected world size {args.expected_world_size}, got {world_size}")
        local_rank = int(os.environ["LOCAL_RANK"])
        torch.cuda.set_device(local_rank)
        device = torch.device("cuda", local_rank)
        nbytes = args.tensor_mib * 1024 * 1024
        element_size = torch.empty((), dtype=torch.float32).element_size()
        tensor = torch.empty(nbytes // element_size, device=device)
        hostnames: list[str | None] = [None] * world_size
        dist.all_gather_object(hostnames, socket.gethostname())

        def run_once() -> float:
            tensor.fill_(1.0)
            dist.barrier()
            torch.cuda.synchronize(device)
            started = torch.cuda.Event(enable_timing=True)
            finished = torch.cuda.Event(enable_timing=True)
            started.record()
            dist.all_reduce(tensor)
            finished.record()
            finished.synchronize()
            local_seconds = started.elapsed_time(finished) / 1000.0
            duration = torch.tensor(local_seconds, dtype=torch.float64, device=device)
            dist.all_reduce(duration, op=dist.ReduceOp.MAX)
            if tensor[0].item() != float(world_size):
                raise RuntimeError("all-reduce correctness check failed")
            return float(duration.item())

        for _ in range(args.warmup):
            run_once()
        durations = [run_once() for _ in range(args.iterations)]
        if rank == 0:
            median_seconds = statistics.median(durations)
            payload: dict[str, object] = {
                "schema_version": "blind-gains.nccl-allreduce-bench.v1",
                "backend": "nccl",
                "world_size": world_size,
                "hosts": sorted({str(host) for host in hostnames}),
                "tensor_mib": args.tensor_mib,
                "tensor_bytes": nbytes,
                "warmup": args.warmup,
                "iterations": args.iterations,
                "max_rank_seconds_median": median_seconds,
                "max_rank_seconds_p95": _percentile(durations, 0.95),
                "algorithm_bandwidth_gbps": nbytes / median_seconds / 1e9,
                "bus_bandwidth_gbps": bus_bandwidth_gbps(nbytes, median_seconds, world_size),
                "correct": True,
            }
            _atomic_json(args.output, payload)
            print(json.dumps(payload, sort_keys=True))
    finally:
        dist.destroy_process_group()


if __name__ == "__main__":
    main()
