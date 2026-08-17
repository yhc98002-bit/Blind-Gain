#!/usr/bin/env python3
"""Make the cell orchestrator survive transient ssh failures.

Root cause of three orchestrator deaths: gpu_free() raised RuntimeError on any
non-zero ssh exit. The login node intermittently fails to launch ssh at all
("libkrb5.so.3: failed to map segment from shared object" under memory
pressure), so a purely transient infrastructure hiccup killed a multi-hour run.
Transient failures are now retried with backoff and, if still failing, treated
as "GPU not free" — conservative, never fatal.
"""
from pathlib import Path
import sys

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
p = ROOT / "scripts/run_d2_testtime_ablation.py"
t = p.read_text()

if "_ssh_retry" in t:
    print("already patched")
    sys.exit(0)

old_ssh = '''def _ssh(node: str, command: str, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(["ssh", node, command], capture_output=True, text=True, timeout=timeout)'''
new_ssh = '''def _ssh(node: str, command: str, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(["ssh", node, command], capture_output=True, text=True, timeout=timeout)


def _ssh_retry(node: str, command: str, attempts: int = 5, timeout: int = 120):
    """ssh with backoff. Returns None if every attempt failed.

    The login node intermittently cannot exec ssh at all (shared-library mmap
    failures under memory pressure). Such failures are transient and must never
    terminate a long-running orchestration.
    """
    delay = 5
    for attempt in range(attempts):
        try:
            result = _ssh(node, command, timeout=timeout)
            if result.returncode == 0:
                return result
        except Exception:
            result = None
        if attempt < attempts - 1:
            time.sleep(delay)
            delay = min(delay * 2, 60)
    return None'''
assert t.count(old_ssh) == 1, "ssh anchor"
t = t.replace(old_ssh, new_ssh)

old_free = '''def gpu_free(node: str, gpu: int) -> bool:
    result = _ssh(node, f"nvidia-smi -i {gpu} --query-compute-apps=pid --format=csv,noheader,nounits")
    if result.returncode != 0:
        raise RuntimeError(f"GPU query failed {node}:{gpu}: {result.stderr.strip()}")
    return not result.stdout.strip()'''
new_free = '''def gpu_free(node: str, gpu: int) -> bool:
    result = _ssh_retry(node, f"nvidia-smi -i {gpu} --query-compute-apps=pid --format=csv,noheader,nounits")
    if result is None:
        # Transient infrastructure failure: assume busy and try again next poll.
        print(json.dumps({"warning": "gpu_query_unavailable", "node": node, "gpu": gpu}))
        return False
    return not result.stdout.strip()'''
assert t.count(old_free) == 1, "gpu_free anchor"
t = t.replace(old_free, new_free)

# liveness probe must not crash the loop either
old_alive = '''                alive = _ssh(args.node, f"ps -o pid= -p {pid} | wc -l")
                if alive.returncode == 0 and int(alive.stdout.strip() or 0) == 0:'''
new_alive = '''                alive = _ssh_retry(args.node, f"ps -o pid= -p {pid} | wc -l", attempts=3)
                if alive is not None and int(alive.stdout.strip() or 0) == 0:'''
assert t.count(old_alive) == 1, "liveness anchor"
t = t.replace(old_alive, new_alive)

# cell spawn should retry rather than abort the campaign
old_spawn = '''    result = _ssh(node, command)
    if result.returncode != 0:
        raise RuntimeError(f"cell spawn failed {model_key}/{condition}: {result.stderr.strip()}")'''
new_spawn = '''    result = _ssh_retry(node, command, attempts=3)
    if result is None:
        raise RuntimeError(f"cell spawn failed after retries {model_key}/{condition}")'''
assert t.count(old_spawn) == 1, "spawn anchor"
t = t.replace(old_spawn, new_spawn)

p.write_text(t)
print("patched: transient ssh failures retried, never fatal")
