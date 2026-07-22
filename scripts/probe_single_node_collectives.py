#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import socket
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "blind-gains.single-node-collective-preflight.v1"


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def validate_rank_results(
    records: list[dict[str, Any]], *, world_size: int = 8
) -> dict[str, Any]:
    expected_ranks = list(range(world_size))
    expected_sum = sum(expected_ranks)
    ranks = sorted(record.get("rank") for record in records)
    local_ranks = sorted(record.get("local_rank") for record in records)
    checks = {
        "exact_rank_count": len(records) == world_size,
        "exact_global_ranks": ranks == expected_ranks,
        "exact_local_ranks": local_ranks == expected_ranks,
        "world_size_exact": all(
            record.get("world_size") == world_size for record in records
        ),
        "one_process_per_visible_gpu": sorted(
            record.get("cuda_device") for record in records
        )
        == expected_ranks,
        "nccl_all_reduce_exact": all(
            record.get("nccl_all_reduce_sum") == expected_sum for record in records
        ),
        "gloo_full_mesh_all_reduce_exact": all(
            record.get("gloo_all_reduce_sum") == expected_sum for record in records
        ),
        "both_barriers_completed": all(
            record.get("nccl_barrier_completed") is True
            and record.get("gloo_barrier_completed") is True
            for record in records
        ),
        "no_worker_error": all(not record.get("error") for record in records),
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "world_size": world_size,
        "expected_sum": expected_sum,
        "records": records,
    }


def combine_rounds(rounds: list[dict[str, Any]]) -> dict[str, Any]:
    names = [round_payload.get("round_name") for round_payload in rounds]
    worker_pids = [
        record.get("pid")
        for round_payload in rounds
        for record in round_payload.get("records", [])
    ]
    checks = {
        "default_and_ib0_rounds_present": names == ["default", "ib0"],
        "both_rounds_pass": len(rounds) == 2
        and all(round_payload.get("status") == "pass" for round_payload in rounds),
        "both_rounds_eight_rank": len(rounds) == 2
        and all(round_payload.get("world_size") == 8 for round_payload in rounds),
        "fresh_worker_processes_per_round": len(worker_pids) == 16
        and len(set(worker_pids)) == 16,
        "default_round_unpinned": len(rounds) >= 1
        and all(
            record.get("gloo_socket_ifname") is None
            and record.get("nccl_socket_ifname") is None
            for record in rounds[0].get("records", [])
        ),
        "ib0_round_explicitly_pinned": len(rounds) >= 2
        and all(
            record.get("gloo_socket_ifname") == "ib0"
            and record.get("nccl_socket_ifname") == "ib0"
            for record in rounds[1].get("records", [])
        ),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "rounds": rounds,
        "created_utc": _now(),
        "scientific_gate_decision": None,
    }


def run_worker(output_dir: Path, round_name: str) -> None:
    import torch
    import torch.distributed as dist

    rank = int(os.environ["RANK"])
    local_rank = int(os.environ["LOCAL_RANK"])
    world_size = int(os.environ["WORLD_SIZE"])
    if world_size != 8:
        raise ValueError(f"collective preflight requires WORLD_SIZE=8, got {world_size}")
    torch.cuda.set_device(local_rank)
    timeout = dt.timedelta(seconds=120)
    dist.init_process_group("nccl", timeout=timeout)
    gloo_group = None
    try:
        nccl_value = torch.tensor(float(rank), device=f"cuda:{local_rank}")
        dist.all_reduce(nccl_value)
        dist.barrier(device_ids=[local_rank])

        gloo_group = dist.new_group(ranks=list(range(world_size)), backend="gloo", timeout=timeout)
        gloo_value = torch.tensor(rank, dtype=torch.int64)
        dist.all_reduce(gloo_value, group=gloo_group)
        dist.barrier(group=gloo_group)
        record = {
            "rank": rank,
            "local_rank": local_rank,
            "world_size": world_size,
            "cuda_device": torch.cuda.current_device(),
            "nccl_all_reduce_sum": int(nccl_value.item()),
            "gloo_all_reduce_sum": int(gloo_value.item()),
            "nccl_barrier_completed": True,
            "gloo_barrier_completed": True,
            "hostname": socket.gethostname(),
            "pid": os.getpid(),
            "gloo_socket_ifname": os.environ.get("GLOO_SOCKET_IFNAME"),
            "nccl_socket_ifname": os.environ.get("NCCL_SOCKET_IFNAME"),
            "error": None,
        }
        _write_json(output_dir / f"rank_{rank}.json", record)
        dist.barrier(device_ids=[local_rank])
        if rank == 0:
            records = [
                json.loads((output_dir / f"rank_{index}.json").read_text(encoding="utf-8"))
                for index in range(world_size)
            ]
            payload = validate_rank_results(records, world_size=world_size)
            payload.update(
                {
                    "schema_version": SCHEMA_VERSION,
                    "round_name": round_name,
                    "created_utc": _now(),
                }
            )
            _write_json(output_dir / "round.json", payload)
    finally:
        if gloo_group is not None:
            dist.destroy_process_group(gloo_group)
        if dist.is_initialized():
            dist.destroy_process_group()


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    worker = subparsers.add_parser("worker")
    worker.add_argument("--output-dir", type=Path, required=True)
    worker.add_argument("--round-name", choices=("default", "ib0"), required=True)
    combine = subparsers.add_parser("combine")
    combine.add_argument("--round", type=Path, action="append", required=True)
    combine.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "worker":
        run_worker(args.output_dir, args.round_name)
        return
    rounds = [json.loads(path.read_text(encoding="utf-8")) for path in args.round]
    payload = combine_rounds(rounds)
    _write_json(args.output, payload)
    print(json.dumps({"status": payload["status"], "checks": payload["checks"]}))
    raise SystemExit(0 if payload["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
