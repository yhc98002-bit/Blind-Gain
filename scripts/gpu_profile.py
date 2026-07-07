#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import time
from pathlib import Path


def worker(device_id: int, seconds: int, size: int, output_dir: str) -> None:
    import torch

    torch.cuda.set_device(device_id)
    a = torch.randn((size, size), device=f"cuda:{device_id}", dtype=torch.bfloat16)
    b = torch.randn((size, size), device=f"cuda:{device_id}", dtype=torch.bfloat16)
    torch.cuda.synchronize(device_id)
    start = time.time()
    iters = 0
    while time.time() - start < seconds:
        c = a @ b
        a = c * 0.999 + a * 0.001
        iters += 1
        if iters % 10 == 0:
            torch.cuda.synchronize(device_id)
    torch.cuda.synchronize(device_id)
    elapsed = time.time() - start
    result = {"device": device_id, "seconds": elapsed, "iterations": iters, "matrix_size": size}
    out_path = Path(output_dir) / f"gpu_{device_id}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=int, default=600)
    parser.add_argument("--size", type=int, default=8192)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    import torch

    count = torch.cuda.device_count()
    processes = []
    for device_id in range(count):
        process = mp.Process(target=worker, args=(device_id, args.seconds, args.size, args.output_dir))
        process.start()
        processes.append(process)
    for process in processes:
        process.join()
        if process.exitcode != 0:
            raise SystemExit(process.exitcode)


if __name__ == "__main__":
    main()
