#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import time

import torch


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=float, default=20.0)
    parser.add_argument("--matrix-size", type=int, default=4096)
    args = parser.parse_args()

    assert torch.cuda.is_available(), "CUDA is not available"
    device_count = torch.cuda.device_count()
    results = {
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
        "device_count": device_count,
        "pid": os.getpid(),
        "seconds": args.seconds,
        "matrix_size": args.matrix_size,
        "devices": [],
    }

    tensors = []
    for idx in range(device_count):
        device = torch.device(f"cuda:{idx}")
        props = torch.cuda.get_device_properties(device)
        a = torch.randn(args.matrix_size, args.matrix_size, device=device, dtype=torch.bfloat16)
        b = torch.randn(args.matrix_size, args.matrix_size, device=device, dtype=torch.bfloat16)
        tensors.append((device, a, b))
        results["devices"].append({"index": idx, "name": props.name, "memory_total": props.total_memory})

    torch.cuda.synchronize()
    start = time.time()
    iters = 0
    while time.time() - start < args.seconds:
        for device, a, b in tensors:
            with torch.cuda.device(device):
                _ = a @ b
        iters += 1
    torch.cuda.synchronize()
    results["iterations"] = iters
    results["elapsed"] = time.time() - start
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

