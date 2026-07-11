#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.ops.run_placement import RunPlacement, record_run_placement


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--node", required=True)
    parser.add_argument("--gpu-ids", default="")
    parser.add_argument("--tensor-parallel-width", type=int, required=True)
    parser.add_argument("--replica-count", type=int, required=True)
    parser.add_argument("--justification", required=True)
    args = parser.parse_args()
    gpu_ids = tuple(
        int(value) for value in args.gpu_ids.replace(",", " ").split() if value
    )
    payload = record_run_placement(
        args.manifest,
        RunPlacement(
            node=args.node,
            gpu_ids=gpu_ids,
            tensor_parallel_width=args.tensor_parallel_width,
            replica_count=args.replica_count,
            justification=args.justification,
        ),
    )
    print(json.dumps({key: payload[key] for key in (
        "node",
        "gpu_ids",
        "tensor_parallel_width",
        "replica_count",
        "placement_justification",
        "placement_policy_version",
    )}, sort_keys=True))


if __name__ == "__main__":
    main()
