#!/usr/bin/env python3
from __future__ import annotations

import json
import os

import torch
import torch.distributed as dist


def main() -> None:
    dist.init_process_group(backend="nccl")
    rank = dist.get_rank()
    world = dist.get_world_size()
    local_rank = int(os.environ.get("LOCAL_RANK", rank % torch.cuda.device_count()))
    torch.cuda.set_device(local_rank)
    device = torch.device("cuda", local_rank)
    value = torch.ones(1, device=device) * (rank + 1)
    dist.all_reduce(value, op=dist.ReduceOp.SUM)
    expected = world * (world + 1) / 2
    ok = abs(value.item() - expected) < 1e-4
    if rank == 0:
        print(json.dumps({"world_size": world, "reduced_value": value.item(), "expected": expected, "ok": ok}))
    dist.barrier()
    dist.destroy_process_group()
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

