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
  3. RESERVATION CLAIM FILES under /dev/shm/blind-gains/gpu_claims on the
     node.  A launcher that has passed this guard writes one
     `<node>_gpu<N>.claim` per claimed GPU BEFORE starting its trainer and
     stamps the runner pid into the claim once the runner is up.  A claim
     counts as occupied while it is fresh (mtime younger than 30 minutes) or
     while its recorded pid is alive on the node.  This closes the TOCTOU
     window that killed M7 arm 4's first attempt
     (m7_virl_a3_caption_seed1_an29_20260730T121906Z): sources (1) and (2)
     cannot see a job that has been granted its GPUs but is still minutes away
     from holding memory on them (vLLM init), so a second launch in that
     window passed the guard and OOM-killed the first.  Claims are visible the
     instant they are written, before any process exists.  A launcher may pass
     `--ignore-claim-run-id <run_id>` so its OWN claims, written between its
     first guard pass and its post-claim re-check, do not read as a
     neighbour's (self-match protection for source (3); stale claims expire by
     age/pid so a crashed launcher cannot wedge the node for longer than 30
     minutes).

FAIL-CLOSED: any occupancy that cannot be determined -- ssh failure, an
unparseable nvidia-smi row, a live trainer whose GPU set cannot be resolved
from its own artifacts, a claim file that cannot be read or parsed, a claim
pid whose liveness cannot be established -- refuses.

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
import shlex
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

# Reservation claim files (occupancy source 3). /dev/shm is node-local, so the
# directory on the target node is authoritative for that node alone.
CLAIMS_DIR = "/dev/shm/blind-gains/gpu_claims"
CLAIM_FRESH_SECONDS = 30 * 60
CLAIM_MARKER = "===CLAIM==="


class ClaimIndeterminate(Exception):
    """A claim file exists but cannot be interpreted; the guard must refuse."""


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


LH2_PID_LINE_RE = re.compile(r"^pid (pending|\d+)$")
LH2_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


def parse_lh2_plaintext_claim(path: str, body: str):
    """The LH2 segment chain (scripts/lh2_segment_chain.sh write_claims) writes
    3-line plain-text claims: run_id / 'pid pending' / epoch. Recognize exactly
    that shape, derive the GPU index from the claim filename, and mark the
    claim ALWAYS occupied — an LH2 claim guards a live multi-day trainer, so
    the 30-minute age-based release must not apply to it. Anything else
    remains unparseable and keeps the fail-closed refusal. Returns a payload
    dict or None."""
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    if len(lines) != 3:
        return None
    run_id, pid_line, epoch = lines
    if not LH2_RUN_ID_RE.fullmatch(run_id):
        return None
    if not LH2_PID_LINE_RE.fullmatch(pid_line):
        return None
    if not epoch.isdigit():
        return None
    match = re.search(r"_gpu(\d)\.claim$", path)
    if not match:
        return None
    gpu = int(match.group(1))
    if not 0 <= gpu <= 7:
        return None
    return {"claim_format": "lh2_plaintext", "gpu": gpu, "run_id": run_id,
            "pid": None, "always_occupied": True}


def evaluate_claims(
    now_epoch: float,
    claims: list,
    pid_alive: dict,
    ignore_run_id: str = "",
    fresh_seconds: float = CLAIM_FRESH_SECONDS,
) -> dict:
    """Pure decision rule for reservation claims; separated so the adversarial
    fixture in tests/test_c5_gpu_claim_guard.py can exercise it without ssh.

    `claims` is a list of {"path": str, "mtime": float, "payload": dict|None};
    `pid_alive` maps pid -> bool for every pid any claim names.
    Returns {gpu_index: [description, ...]} for claims that count as occupied.
    Raises ClaimIndeterminate for anything unreadable (FAIL-CLOSED upstream).
    """
    occupied: dict = {}
    for claim in claims:
        path = claim.get("path", "<unknown-claim>")
        payload = claim.get("payload")
        if not isinstance(payload, dict):
            raise ClaimIndeterminate(f"claim {path} is not a JSON object")
        gpu = payload.get("gpu")
        if not isinstance(gpu, int) or isinstance(gpu, bool) or not 0 <= gpu <= 7:
            raise ClaimIndeterminate(f"claim {path} has no usable gpu index: {gpu!r}")
        mtime = claim.get("mtime")
        if not isinstance(mtime, (int, float)) or isinstance(mtime, bool):
            raise ClaimIndeterminate(f"claim {path} has no usable mtime: {mtime!r}")
        run_id = payload.get("run_id")
        if not isinstance(run_id, str) or not run_id:
            raise ClaimIndeterminate(f"claim {path} has no usable run_id: {run_id!r}")
        if ignore_run_id and run_id == ignore_run_id:
            continue  # the caller's own reservation, written after its first guard pass
        if payload.get("claim_format") == "lh2_plaintext":
            occupied.setdefault(gpu, []).append(
                f"claim:{run_id} (lh2 plaintext, always occupied) [{path}]")
            continue
        pid = payload.get("pid")
        alive = False
        if pid is not None:
            if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
                raise ClaimIndeterminate(f"claim {path} has non-integer pid: {pid!r}")
            if pid not in pid_alive:
                raise ClaimIndeterminate(f"claim {path}: liveness of pid {pid} was not established")
            alive = bool(pid_alive[pid])
        age = now_epoch - mtime
        fresh = age < fresh_seconds  # a negative age (future mtime) is fresh: fail-closed
        if fresh or alive:
            reasons = []
            if fresh:
                reasons.append(f"age {int(age)}s < {int(fresh_seconds)}s")
            if alive:
                reasons.append(f"pid {pid} alive")
            occupied.setdefault(gpu, []).append(f"claim:{run_id} ({', '.join(reasons)}) [{path}]")
    return occupied


def claim_occupancy(node: str, ignore_run_id: str = "") -> dict:
    """index -> descriptions, from reservation claim files on the node."""
    listing = run_ssh(
        node,
        "date +%s && { [ ! -d " + shlex.quote(CLAIMS_DIR) + " ] || "
        "find " + shlex.quote(CLAIMS_DIR) + " -maxdepth 1 -name '*.claim' "
        "-printf '%p\\t%T@\\n'; }",
    )
    lines = [line.strip() for line in listing.splitlines() if line.strip()]
    if not lines:
        refuse(f"claim listing on {node} returned no clock line")
    if not lines[0].isdigit():
        refuse(f"claim listing on {node} has an unparseable clock line: {lines[0]!r}")
    now_epoch = float(lines[0])
    entries = []
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) != 2:
            refuse(f"unparseable claim listing row on {node}: {line!r}")
        path, mtime_raw = parts
        try:
            mtime = float(mtime_raw)
        except ValueError:
            refuse(f"unparseable claim mtime on {node}: {line!r}")
        entries.append({"path": path, "mtime": mtime})
    if not entries:
        return {}
    dump_cmd = "for f in " + " ".join(shlex.quote(e["path"]) for e in entries) + "; do " \
        "printf '%s %s\\n' '" + CLAIM_MARKER + "' \"$f\"; cat \"$f\"; printf '\\n'; done"
    raw = run_ssh(node, dump_cmd)
    bodies: dict = {}
    current = None
    for line in raw.splitlines():
        if line.startswith(CLAIM_MARKER):
            current = line[len(CLAIM_MARKER):].strip()
            bodies[current] = []
        elif current is not None:
            bodies[current].append(line)
    claims = []
    for entry in entries:
        body = "\n".join(bodies.get(entry["path"], [])).strip()
        try:
            payload = json.loads(body) if body else None
        except ValueError:
            payload = None
        if payload is None and body:
            payload = parse_lh2_plaintext_claim(entry["path"], body)
        claims.append({"path": entry["path"], "mtime": entry["mtime"], "payload": payload})
    pids = set()
    for claim in claims:
        payload = claim["payload"]
        if isinstance(payload, dict):
            pid = payload.get("pid")
            if isinstance(pid, int) and not isinstance(pid, bool) and pid > 0:
                pids.add(pid)
    pid_alive: dict = {}
    if pids:
        probe = "; ".join(
            f"if ps -o pid= -p {pid} >/dev/null 2>&1; "
            f"then echo '{pid} alive'; else echo '{pid} dead'; fi"
            for pid in sorted(pids)
        )
        raw = run_ssh(node, probe)
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 2 or not parts[0].isdigit() or parts[1] not in ("alive", "dead"):
                refuse(f"unparseable pid-liveness row on {node}: {line!r}")
            pid_alive[int(parts[0])] = parts[1] == "alive"
    try:
        return evaluate_claims(now_epoch, claims, pid_alive, ignore_run_id=ignore_run_id)
    except ClaimIndeterminate as exc:
        refuse(str(exc))
    return {}  # unreachable; refuse() exits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--node", required=True)
    ap.add_argument("--gpus", required=True, help="comma-separated visible-device list")
    ap.add_argument(
        "--ignore-claim-run-id",
        default="",
        help="reservation-claim run_id to treat as the caller's own (self-match "
        "protection for a launcher re-checking after it wrote its claims); "
        "affects claim files only, never compute-app or trainer occupancy",
    )
    args = ap.parse_args()

    if not GPU_CSV_RE.match(args.gpus):
        print(f"[m7-gpu-guard] bad --gpus {args.gpus!r}", file=sys.stderr)
        return EXIT_USAGE
    requested = sorted({int(g) for g in args.gpus.split(",")})

    index_of = gpu_index_map(args.node)
    busy = compute_app_occupancy(args.node, index_of)
    claimed = trainer_occupancy(args.node)
    reserved = claim_occupancy(args.node, ignore_run_id=args.ignore_claim_run_id)

    occupied = sorted(set(busy) | set(claimed) | set(reserved))
    overlap = sorted(set(requested) & set(occupied))

    print(f"[m7-gpu-guard] node={args.node} requested={requested}")
    print(f"[m7-gpu-guard] compute-app occupancy: {{{', '.join(f'{k}: {v}' for k, v in sorted(busy.items()))}}}")
    print(f"[m7-gpu-guard] trainer-manifest occupancy: {{{', '.join(f'{k}: {v}' for k, v in sorted(claimed.items()))}}}")
    print(f"[m7-gpu-guard] claim-file occupancy: {{{', '.join(f'{k}: {v}' for k, v in sorted(reserved.items()))}}}")
    print(f"[m7-gpu-guard] occupied={occupied} overlap={overlap}")

    if overlap:
        holders = []
        for gpu in overlap:
            who = busy.get(gpu, []) + claimed.get(gpu, []) + reserved.get(gpu, [])
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
