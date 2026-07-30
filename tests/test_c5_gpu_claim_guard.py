"""Adversarial fixture (I10) for the reservation-claim TOCTOU fix.

The defect: M7 arm 4's first attempt
(`m7_virl_a3_caption_seed1_an29_20260730T121906Z`) was granted its GPUs, was
still minutes deep in vLLM init holding NO GPU memory, and a second job was
started onto the same physical GPUs -- `nvidia-smi --query-compute-apps`
showed nothing and no trainer argv was resolvable yet, so every occupancy
source the old guard had reported the GPUs free.  The arm died in KV-cache
allocation.

The fix: launchers write reservation claim files BEFORE launching, and
`scripts/m7_gpu_occupancy_guard.py` treats a fresh claim (age < 30 min, or
recorded pid alive) as occupied.

This file demonstrates the old decision rule fails the scenario (test
`test_old_decision_rule_fails_the_toctou_scenario`) and the new one closes it,
at two levels:

  * pure-function tests on `evaluate_claims`, no ssh involved;
  * end-to-end subprocess runs of the real guard against a fake `ssh` binary
    that serves a canned node state, asserting the real exit codes
    (75 refuse / 0 allow).
"""
from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.m7_gpu_occupancy_guard import (
    CLAIM_FRESH_SECONDS,
    ClaimIndeterminate,
    evaluate_claims,
)

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts" / "m7_gpu_occupancy_guard.py"

NOW = 1_800_000_000.0


def claim(path="/dev/shm/blind-gains/gpu_claims/an12_gpu3.claim", mtime=NOW - 300,
          gpu=3, run_id="c5_a1_real_seed1_7b_an12_x", pid=None, payload_override=None):
    payload = {"run_id": run_id, "node": "an12", "gpu": gpu, "pid": pid}
    if payload_override is not None:
        payload = payload_override
    return {"path": path, "mtime": mtime, "payload": payload}


# ---------------------------------------------------------------------------
# The adversarial scenario itself: old rule allows, new rule refuses.
# ---------------------------------------------------------------------------

def test_old_decision_rule_fails_the_toctou_scenario() -> None:
    # Node state exactly as an29 presented it at 12:26Z on 2026-07-30: the
    # victim had been granted GPUs 4-7 seven minutes earlier and was still in
    # vLLM init, so there were no compute apps and no resolvable trainer argv.
    busy: dict = {}             # nvidia-smi --query-compute-apps: nothing
    trainer_claimed: dict = {}  # pgrep + manifest resolution: nothing
    fresh = claim(mtime=NOW - 7 * 60, gpu=4)

    # OLD rule (pre-claim guard): union of the two live sources only.
    old_occupied = set(busy) | set(trainer_claimed)
    assert 4 not in old_occupied, (
        "the scenario must be exactly the one the old guard allowed; "
        "if this fails the fixture no longer reproduces the defect"
    )

    # NEW rule: the reservation claim makes GPU 4 occupied.
    reserved = evaluate_claims(NOW, [fresh], pid_alive={})
    new_occupied = old_occupied | set(reserved)
    assert 4 in new_occupied
    assert "claim:" in reserved[4][0]


# ---------------------------------------------------------------------------
# Pure decision-rule behavior.
# ---------------------------------------------------------------------------

def test_fresh_claim_without_pid_is_occupied() -> None:
    occupied = evaluate_claims(NOW, [claim(mtime=NOW - 60)], pid_alive={})
    assert set(occupied) == {3}


def test_expired_claim_without_pid_is_ignored() -> None:
    expired = claim(mtime=NOW - CLAIM_FRESH_SECONDS - 60)
    assert evaluate_claims(NOW, [expired], pid_alive={}) == {}


def test_aged_claim_with_live_pid_stays_occupied() -> None:
    aged = claim(mtime=NOW - 2 * CLAIM_FRESH_SECONDS, pid=4242)
    occupied = evaluate_claims(NOW, [aged], pid_alive={4242: True})
    assert set(occupied) == {3}
    assert "pid 4242 alive" in occupied[3][0]


def test_aged_claim_with_dead_pid_is_ignored() -> None:
    aged = claim(mtime=NOW - 2 * CLAIM_FRESH_SECONDS, pid=4242)
    assert evaluate_claims(NOW, [aged], pid_alive={4242: False}) == {}


def test_future_mtime_counts_as_fresh_fail_closed() -> None:
    skewed = claim(mtime=NOW + 3600)
    assert set(evaluate_claims(NOW, [skewed], pid_alive={})) == {3}


def test_own_run_id_is_excluded_but_only_that_one() -> None:
    mine = claim(run_id="me", gpu=2)
    theirs = claim(run_id="them", gpu=5, path="/dev/shm/blind-gains/gpu_claims/an12_gpu5.claim")
    occupied = evaluate_claims(NOW, [mine, theirs], pid_alive={}, ignore_run_id="me")
    assert set(occupied) == {5}


# ---------------------------------------------------------------------------
# Fail-closed on anything unreadable.
# ---------------------------------------------------------------------------

def test_unparseable_claim_refuses() -> None:
    with pytest.raises(ClaimIndeterminate):
        evaluate_claims(NOW, [claim(payload_override="not-a-dict")], pid_alive={})


def test_missing_gpu_index_refuses() -> None:
    with pytest.raises(ClaimIndeterminate):
        evaluate_claims(NOW, [claim(payload_override={"run_id": "x", "pid": None})], pid_alive={})


def test_unknown_pid_liveness_refuses() -> None:
    with pytest.raises(ClaimIndeterminate):
        evaluate_claims(NOW, [claim(pid=777)], pid_alive={})


def test_bool_gpu_index_refuses() -> None:
    with pytest.raises(ClaimIndeterminate):
        evaluate_claims(
            NOW,
            [claim(payload_override={"run_id": "x", "gpu": True, "pid": None})],
            pid_alive={},
        )


# ---------------------------------------------------------------------------
# End to end: the real guard binary against a fake ssh serving canned state.
# ---------------------------------------------------------------------------

def make_fake_ssh(tmp_path: Path, now: int, claim_rows: list, claim_bodies: dict,
                  alive_pids: set) -> Path:
    """Build a fake `ssh` that answers the guard's five remote probes for a
    node with 8 GPUs, no compute apps and no live trainers."""
    listing = "\n".join(f"{path}\t{mtime}" for path, mtime in claim_rows)
    dump_lines = []
    for path, body in claim_bodies.items():
        dump_lines.append(f"===CLAIM=== {path}")
        dump_lines.append(body)
    dump = "\n".join(dump_lines)
    ps_lines = []
    for path, body in claim_bodies.items():
        try:
            pid = json.loads(body).get("pid")
        except ValueError:
            pid = None
        if isinstance(pid, int) and pid > 0:
            state = "alive" if pid in alive_pids else "dead"
            ps_lines.append(f"{pid} {state}")
    ps_out = "\n".join(dict.fromkeys(ps_lines))
    gpu_map = "\n".join(f"{i}, GPU-fake-{i}" for i in range(8))
    script = f"""#!/usr/bin/env bash
# fake ssh: last argument is the remote command
cmd="${{@: -1}}"
case "$cmd" in
  *query-gpu=index,uuid*) cat <<'EOF'
{gpu_map}
EOF
    exit 0;;
  *query-compute-apps*) exit 0;;
  *pgrep*) exit 1;;
  *"date +%s"*) cat <<'EOF'
{now}
{listing}
EOF
    exit 0;;
  *"===CLAIM==="*) cat <<'EOF'
{dump}
EOF
    exit 0;;
  *"ps -o pid="*) cat <<'EOF'
{ps_out}
EOF
    exit 0;;
  *) echo "fake ssh got unexpected command: $cmd" >&2; exit 97;;
esac
"""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir(exist_ok=True)
    ssh_path = fake_bin / "ssh"
    ssh_path.write_text(script, encoding="utf-8")
    ssh_path.chmod(ssh_path.stat().st_mode | stat.S_IXUSR)
    return fake_bin


def run_guard(fake_bin: Path, gpus: str, extra_args: tuple = ()) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    return subprocess.run(
        [sys.executable, str(GUARD), "--node", "anXX", "--gpus", gpus, *extra_args],
        capture_output=True,
        text=True,
        env=env,
        cwd=ROOT,
        timeout=120,
    )


CLAIM_PATH = "/dev/shm/blind-gains/gpu_claims/anXX_gpu2.claim"


def claim_body(pid=None, run_id="c5_probe_run") -> str:
    return json.dumps({"run_id": run_id, "node": "anXX", "gpu": 2, "pid": pid})


def test_guard_refuses_fresh_claim_end_to_end(tmp_path: Path) -> None:
    now = 1_800_000_000
    fake_bin = make_fake_ssh(
        tmp_path, now,
        claim_rows=[(CLAIM_PATH, f"{now - 300}.0")],
        claim_bodies={CLAIM_PATH: claim_body()},
        alive_pids=set(),
    )
    proc = run_guard(fake_bin, "2")
    assert proc.returncode == 75, proc.stdout + proc.stderr
    assert "claim:c5_probe_run" in proc.stdout + proc.stderr


def test_guard_allows_expired_claim_end_to_end(tmp_path: Path) -> None:
    now = 1_800_000_000
    fake_bin = make_fake_ssh(
        tmp_path, now,
        claim_rows=[(CLAIM_PATH, f"{now - 2 * CLAIM_FRESH_SECONDS}.0")],
        claim_bodies={CLAIM_PATH: claim_body()},
        alive_pids=set(),
    )
    proc = run_guard(fake_bin, "2")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "ALLOW" in proc.stdout


def test_guard_refuses_expired_claim_with_live_pid_end_to_end(tmp_path: Path) -> None:
    now = 1_800_000_000
    fake_bin = make_fake_ssh(
        tmp_path, now,
        claim_rows=[(CLAIM_PATH, f"{now - 2 * CLAIM_FRESH_SECONDS}.0")],
        claim_bodies={CLAIM_PATH: claim_body(pid=31337)},
        alive_pids={31337},
    )
    proc = run_guard(fake_bin, "2")
    assert proc.returncode == 75, proc.stdout + proc.stderr
    assert "pid 31337 alive" in proc.stdout + proc.stderr


def test_guard_refuses_unreadable_claim_end_to_end(tmp_path: Path) -> None:
    now = 1_800_000_000
    fake_bin = make_fake_ssh(
        tmp_path, now,
        claim_rows=[(CLAIM_PATH, f"{now - 60}.0")],
        claim_bodies={CLAIM_PATH: "{this is not json"},
        alive_pids=set(),
    )
    proc = run_guard(fake_bin, "2")
    assert proc.returncode == 75, proc.stdout + proc.stderr


def test_guard_ignores_own_claim_but_not_others_end_to_end(tmp_path: Path) -> None:
    now = 1_800_000_000
    other = "/dev/shm/blind-gains/gpu_claims/anXX_gpu5.claim"
    fake_bin = make_fake_ssh(
        tmp_path, now,
        claim_rows=[(CLAIM_PATH, f"{now - 60}.0"), (other, f"{now - 60}.0")],
        claim_bodies={
            CLAIM_PATH: claim_body(run_id="my_run"),
            other: json.dumps({"run_id": "their_run", "node": "anXX", "gpu": 5, "pid": None}),
        },
        alive_pids=set(),
    )
    # own claim on gpu 2 excluded -> allowed on 2
    proc = run_guard(fake_bin, "2", ("--ignore-claim-run-id", "my_run"))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    # a neighbour's claim on gpu 5 still refuses
    proc = run_guard(fake_bin, "5", ("--ignore-claim-run-id", "my_run"))
    assert proc.returncode == 75, proc.stdout + proc.stderr


def test_guard_allows_disjoint_gpu_despite_neighbour_claim(tmp_path: Path) -> None:
    # Node co-tenancy stays normal: a fresh claim on gpu 2 must not refuse a
    # request for gpu 6.
    now = 1_800_000_000
    fake_bin = make_fake_ssh(
        tmp_path, now,
        claim_rows=[(CLAIM_PATH, f"{now - 60}.0")],
        claim_bodies={CLAIM_PATH: claim_body()},
        alive_pids=set(),
    )
    proc = run_guard(fake_bin, "6")
    assert proc.returncode == 0, proc.stdout + proc.stderr
