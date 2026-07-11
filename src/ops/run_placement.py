from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PLACEMENT_POLICY_VERSION = "pi-2026-07-11"
COMPUTE_NODES = frozenset({"an12", "an29"})


@dataclass(frozen=True)
class RunPlacement:
    node: str
    gpu_ids: tuple[int, ...]
    tensor_parallel_width: int
    replica_count: int
    justification: str

    def validate(self) -> None:
        if self.node not in COMPUTE_NODES | {"login"}:
            raise ValueError(f"placement node must be one host, found {self.node!r}")
        if len(set(self.gpu_ids)) != len(self.gpu_ids):
            raise ValueError("placement GPU IDs must be unique")
        if any(gpu < 0 or gpu > 7 for gpu in self.gpu_ids):
            raise ValueError("placement GPU IDs must be in [0, 7]")
        if not self.justification.strip():
            raise ValueError("placement justification must be nonempty")
        if self.node == "login":
            if self.gpu_ids or self.tensor_parallel_width != 0 or self.replica_count != 0:
                raise ValueError("login-node placement must record no GPUs, TP0, and zero replicas")
            return
        if not self.gpu_ids:
            raise ValueError("compute-node placement requires at least one GPU")
        if self.tensor_parallel_width < 1:
            raise ValueError("GPU placement requires tensor_parallel_width >= 1")
        if self.replica_count < 1:
            raise ValueError("GPU placement requires replica_count >= 1")
        if self.tensor_parallel_width > len(self.gpu_ids):
            raise ValueError("tensor-parallel width exceeds the registered GPU allocation")

    def fields(self) -> dict[str, Any]:
        self.validate()
        return {
            "node": self.node,
            "gpu_ids": list(self.gpu_ids),
            "tensor_parallel_width": self.tensor_parallel_width,
            "replica_count": self.replica_count,
            "placement_justification": self.justification.strip(),
            "placement_policy_version": PLACEMENT_POLICY_VERSION,
        }


def record_run_placement(path: Path, placement: RunPlacement) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    fields = placement.fields()
    existing_node = payload.get("node")
    if existing_node is not None and existing_node != placement.node:
        raise ValueError(
            f"manifest node conflicts with placement: {existing_node!r} != {placement.node!r}"
        )
    for key, value in fields.items():
        if key in payload and payload[key] != value:
            raise ValueError(f"manifest placement field conflicts: {key}")
    payload.update(fields)

    temporary = path.with_name(f".{path.name}.placement.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    return payload
