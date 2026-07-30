#!/usr/bin/env python3
"""GPU-scope colocation guard for M7 arm launches.

Implements the placement policy stated verbatim in CLAUDE.md:

    "Single-node placement for every job unless it genuinely requires >8 GPUs.
     Never split one training or serving job across an12/an29.
     Colocating disjoint-GPU jobs on one node is normal; the researcher's own
     processes are normal neighbors, never anomalies."

Node co-tenancy is therefore EXPLICITLY NORMAL and is *not* a refusal
condition.  The single refusal condition is overlap between the GPU set this
launch requests and a GPU set already occupied on that node.  The predecessor
of this guard refused whenever any verl trainer ran anywhere on the target
node, which capped M7 at one arm per node and left 10 GPUs idle; this file is
the narrowing.

Occupancy is derived from actual state on the node, never from a process-name
regex alone:

  1. `nvidia-smi --query-compute-apps` -> the GPUs that currently hold a
     compute context, whatever process owns it (a neighbour eval counts).
  2. For every live verl trainer, the `gpu_ids` recorded in the run manifest
     that sits beside the `config=` path in its own argv, cross-checked
     against `n_gpus_per_node` in that same effective config.  This closes the
     startup window in which a trainer owns its GPUs by contract but has not
     yet allocated memory on them, so (1) cannot see it.

FAIL-CLOSED: any occupancy that cannot be determined -- ssh failure, an
unparseable nvidia-smi row, a live trainer whose GPU set cannot be resolved
from its own artifacts -- refuses.

SELF-MATCH PROTECTION (a defect that bit this project before): the pgrep
pattern is bracketed as "verl.trainer.mai[n]".  The probe's own remote command
line carries that literal text, which the regex does not match, while a real
trainer argv does.  Rows whose command line carries the bracket marker or
`pgrep` are additionally dropped.

Exit codes: 0 allow, 75 refuse (overlap or indeterminate), 2 bad usage.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

EXIT_ALLOW = 0
EXIT_REFUSE = 75
EXIT_USAGE = 2

# bracketed on purpose -- see the SELF-MATCH PROTECTION note in the docstring
TRAINER_PATTERN = "verl.trainer.mai[n]"
SELF_MARKERS = ("mai[n]", "pgrep")
GPU_CSV_RE = re.compile(r"^[0-7](,[0-7])*$")


def refuse(message: str) -> None:
    print(f"[m7-gpu-guard] REFUSE: {message}", file=sys.stderr)
    sys.exit(EXIT_REFUSE)


def run_ssh(node: str, command: str, ok_codes=(0,)) -> str:
    proc = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=25", node, command],
        capture_output=True,
        text=True,
    )
    if proc.returncode not in ok_codes:
        refuse(
            f"occupancy on {node} is indeterminate: `{command}` exited "
            f"{proc.returncode}: {proc.stderr.strip()[:400]}"
        )
    return proc.stdout


def gpu_index_map(node: str) -> dict:
    raw = run_ssh(node, "nvidia-smi --query-gpu=index,uuid --format=csv,noheader,nounits")
    mapping = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1]:
            refuse(f"unparseable nvidia-smi GPU row on {node}: {line!r}")
        mapping[parts[1]] = int(parts[0])
    if not mapping:
        refuse(f"nvidia-smi reported no GPUs on {node}")
    return mapping


def compute_app_occupancy(node: str, index_of: dict) -> dict:
    """index -> list of 'pid=<pid> mem=<MiB>' strings, from live compute contexts."""
    raw = run_ssh(
        node,
        "nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory "
        "--format=csv,noheader,nounits",
    )
    busy: dict = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 3:
            refuse(f"unparseable nvidia-smi compute-app row on {node}: {line!r}")
        uuid, pid, mem = parts
        if uuid not in index_of:
            refuse(f"compute app on {node} reports unknown GPU uuid {uuid!r}")
        busy.setdefault(index_of[uuid], []).append(f"pid={pid} mem={mem}MiB")
    return busy


def trainer_occupancy(node: str) -> dict:
    """index -> list of 'run_id' strings, from each live trainer's own manifest."""
    raw = run_ssh(node, f"pgrep -a -f '{TRAINER_PATTERN}'", ok_codes=(0, 1))
    claimed: dict = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if any(marker in line for marker in SELF_MARKERS):
            continue  # the probe itself, never a neighbour
        pid, _, cmdline = line.partition(" ")
        config_path = None
        for token in cmdline.split():
            if token.startswith("config="):
                config_path = token[len("config=") :]
        if not config_path:
            refuse(
                f"live trainer pid {pid} on {node} carries no `config=` argument, "
                "so its GPU set cannot be derived"
            )
        run_dir = Path(config_path).parent
        manifest_path = run_dir / "run_manifest.json"
        if not manifest_path.is_file():
            refuse(
                f"live trainer pid {pid} on {node} has no run manifest at "
                f"{manifest_path}, so its GPU set cannot be derived"
            )
        try:
            manifest = json.loads(manifest_path.read_text())
        except (OSError, ValueError) as exc:
            refuse(f"cannot read {manifest_path}: {exc}")
        gpu_ids = manifest.get("gpu_ids")
        if not isinstance(gpu_ids, list) or not gpu_ids or not all(
            isinstance(g, int) for g in gpu_ids
        ):
            refuse(f"{manifest_path} has no usable gpu_ids: {gpu_ids!r}")
        manifest_node = manifest.get("node")
        if manifest_node != node:
            refuse(
                f"live trainer pid {pid} runs on {node} but its manifest "
                f"{manifest_path} records node {manifest_node!r}"
            )
        if Path(config_path).is_file():
            try:
                effective = yaml.safe_load(Path(config_path).read_text()) or {}
            except (OSError, ValueError) as exc:
                refuse(f"cannot read {config_path}: {exc}")
            width = (effective.get("trainer") or {}).get("n_gpus_per_node")
            if width is not None and int(width) != len(set(gpu_ids)):
                refuse(
                    f"live trainer pid {pid}: manifest claims {sorted(set(gpu_ids))} "
                    f"but {config_path} sets n_gpus_per_node={width}"
                )
        run_id = manifest.get("run_id", str(run_dir))
        for gpu in sorted(set(gpu_ids)):
            claimed.setdefault(gpu, []).append(f"{run_id} (pid={pid})")
    return claimed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--node", required=True)
    ap.add_argument("--gpus", required=True, help="comma-separated visible-device list")
    args = ap.parse_args()

    if not GPU_CSV_RE.match(args.gpus):
        print(f"[m7-gpu-guard] bad --gpus {args.gpus!r}", file=sys.stderr)
        return EXIT_USAGE
    requested = sorted({int(g) for g in args.gpus.split(",")})

    index_of = gpu_index_map(args.node)
    busy = compute_app_occupancy(args.node, index_of)
    claimed = trainer_occupancy(args.node)

    occupied = sorted(set(busy) | set(claimed))
    overlap = sorted(set(requested) & set(occupied))

    print(f"[m7-gpu-guard] node={args.node} requested={requested}")
    print(f"[m7-gpu-guard] compute-app occupancy: {{{', '.join(f'{k}: {v}' for k, v in sorted(busy.items()))}}}")
    print(f"[m7-gpu-guard] trainer-manifest occupancy: {{{', '.join(f'{k}: {v}' for k, v in sorted(claimed.items()))}}}")
    print(f"[m7-gpu-guard] occupied={occupied} overlap={overlap}")

    if overlap:
        holders = []
        for gpu in overlap:
            who = busy.get(gpu, []) + claimed.get(gpu, [])
            holders.append(f"gpu{gpu}<-{who}")
        refuse(
            f"requested GPUs {requested} on {args.node} overlap occupied GPUs "
            f"{overlap}: {'; '.join(holders)}"
        )

    print(
        f"[m7-gpu-guard] ALLOW: {args.node}:{requested} is disjoint from all "
        "occupied GPUs; node co-tenancy is normal per CLAUDE.md placement policy"
    )
    return EXIT_ALLOW


if __name__ == "__main__":
    sys.exit(main())
