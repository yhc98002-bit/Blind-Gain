#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os

import torch
import torch.distributed as dist
from torch import nn
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=5)
    parser.add_argument("--dim", type=int, default=1024)
    parser.add_argument("--hidden", type=int, default=4096)
    parser.add_argument("--batch", type=int, default=8)
    args = parser.parse_args()

    dist.init_process_group("nccl")
    rank = dist.get_rank()
    world = dist.get_world_size()
    local_rank = int(os.environ.get("LOCAL_RANK", rank % torch.cuda.device_count()))
    torch.cuda.set_device(local_rank)
    device = torch.device("cuda", local_rank)

    torch.manual_seed(1000 + rank)
    model = nn.Sequential(
        nn.Linear(args.dim, args.hidden),
        nn.GELU(),
        nn.Linear(args.hidden, args.dim),
    ).to(device)
    model = FSDP(model)
    optim = torch.optim.AdamW(model.parameters(), lr=1e-4)

    last_loss = None
    for _ in range(args.steps):
        x = torch.randn(args.batch, args.dim, device=device, dtype=torch.float32)
        y = torch.randn(args.batch, args.dim, device=device, dtype=torch.float32)
        pred = model(x)
        loss = torch.nn.functional.mse_loss(pred, y)
        optim.zero_grad(set_to_none=True)
        loss.backward()
        optim.step()
        torch.cuda.synchronize(device)
        last_loss = loss.detach()

    assert last_loss is not None
    reduced = last_loss.clone()
    dist.all_reduce(reduced, op=dist.ReduceOp.AVG)
    if rank == 0:
        print(json.dumps({"world_size": world, "steps": args.steps, "avg_last_loss": float(reduced.item()), "ok": True}))
    dist.barrier()
    torch.cuda.synchronize(device)
    dist.destroy_process_group()


if __name__ == "__main__":
    main()
