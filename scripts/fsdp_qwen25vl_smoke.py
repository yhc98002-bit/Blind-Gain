#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import time
from pathlib import Path

import torch
import torch.distributed as dist
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
from torch.distributed.fsdp import MixedPrecision, ShardingStrategy
from transformers import Qwen2_5_VLForConditionalGeneration


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = Path(f"{path}.partial")
    if path.exists() or partial.exists():
        raise FileExistsError(f"refusing to overwrite FSDP smoke artifact: {path}")
    partial.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(partial, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--steps", type=int, choices=(1, 2), default=1)
    parser.add_argument("--sequence-length", type=int, default=64)
    parser.add_argument("--expected-world-size", type=int, default=16)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.sequence_length < 8:
        raise ValueError("sequence length must be at least 8")
    config_path = args.model_path / "config.json"
    if not config_path.is_file():
        raise FileNotFoundError(f"missing model config: {config_path}")

    dist.init_process_group("nccl")
    try:
        rank = dist.get_rank()
        world_size = dist.get_world_size()
        if world_size != args.expected_world_size:
            raise RuntimeError(f"expected world size {args.expected_world_size}, got {world_size}")
        local_rank = int(os.environ["LOCAL_RANK"])
        torch.cuda.set_device(local_rank)
        device = torch.device("cuda", local_rank)
        torch.manual_seed(20260710 + rank)

        model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            args.model_path,
            torch_dtype=torch.bfloat16,
            attn_implementation="sdpa",
            low_cpu_mem_usage=True,
        )
        model.config.use_cache = False
        model.train()
        model = FSDP(
            model,
            device_id=device,
            sharding_strategy=ShardingStrategy.FULL_SHARD,
            mixed_precision=MixedPrecision(
                param_dtype=torch.bfloat16,
                reduce_dtype=torch.bfloat16,
                buffer_dtype=torch.bfloat16,
            ),
            use_orig_params=True,
            limit_all_gathers=True,
        )
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-6)
        vocab_size = int(model.module.config.text_config.vocab_size)
        losses: list[float] = []
        step_seconds: list[float] = []
        for _ in range(args.steps):
            input_ids = torch.randint(100, vocab_size - 1, (1, args.sequence_length), device=device)
            attention_mask = torch.ones_like(input_ids)
            labels = input_ids.clone()
            optimizer.zero_grad(set_to_none=True)
            torch.cuda.synchronize(device)
            started = time.perf_counter()
            output = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            output.loss.backward()
            optimizer.step()
            torch.cuda.synchronize(device)
            step_seconds.append(time.perf_counter() - started)
            losses.append(float(output.loss.detach().float().item()))

        loss_tensor = torch.tensor(losses[-1], device=device)
        dist.all_reduce(loss_tensor, op=dist.ReduceOp.AVG)
        peak_memory = torch.tensor(
            torch.cuda.max_memory_allocated(device), dtype=torch.float64, device=device
        )
        dist.all_reduce(peak_memory, op=dist.ReduceOp.MAX)
        hosts: list[str | None] = [None] * world_size
        dist.all_gather_object(hosts, socket.gethostname())
        if rank == 0:
            payload: dict[str, object] = {
                "schema_version": "blind-gains.fsdp-qwen25vl-smoke.v1",
                "model_path": str(args.model_path),
                "model_config_sha256": _sha256(config_path),
                "world_size": world_size,
                "hosts": sorted({str(host) for host in hosts}),
                "steps": args.steps,
                "sequence_length": args.sequence_length,
                "input_mode": "synthetic_text_only",
                "attention_implementation": "sdpa",
                "sharding_strategy": "FULL_SHARD",
                "average_last_loss": float(loss_tensor.item()),
                "max_rank_peak_memory_bytes": int(peak_memory.item()),
                "rank0_step_seconds": step_seconds,
                "finite_loss": bool(torch.isfinite(loss_tensor).item()),
            }
            if not payload["finite_loss"]:
                raise RuntimeError("FSDP smoke produced a non-finite loss")
            _atomic_json(args.output, payload)
            print(json.dumps(payload, sort_keys=True))
    finally:
        dist.destroy_process_group()


if __name__ == "__main__":
    main()
