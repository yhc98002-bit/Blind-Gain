#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GPU_LIST = "0,1,2,3,4,5,6,7"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _atomic(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def node_gpu_snapshot(node: str) -> dict[int, dict[str, int]]:
    output = subprocess.run(
        [
            "ssh",
            node,
            "nvidia-smi --query-gpu=index,memory.used,utilization.gpu "
            "--format=csv,noheader,nounits",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout
    result: dict[int, dict[str, int]] = {}
    for line in output.splitlines():
        if not line.strip():
            continue
        fields = [int(value.strip()) for value in line.split(",")]
        if len(fields) != 3:
            raise ValueError(f"malformed nvidia-smi row from {node}: {line!r}")
        result[fields[0]] = {"memory_mib": fields[1], "utilization_pct": fields[2]}
    if set(result) != set(range(8)):
        raise ValueError(f"{node} did not report exactly GPUs 0-7")
    return result


def node_is_fully_free(snapshot: dict[int, dict[str, int]]) -> bool:
    return all(row["memory_mib"] < 1024 for row in snapshot.values())


def dependency_state(
    seed2_manifest: Path, m11_manifest: Path, m5_manifest: Path
) -> tuple[str, dict[str, str]]:
    statuses = {
        "seed2": str(_read(seed2_manifest).get("status")),
        "m11": str(_read(m11_manifest).get("status")),
        "m5": str(_read(m5_manifest).get("status")),
    }
    if statuses["seed2"] == "fail" or statuses["m11"] == "fail" or statuses["m5"] == "fail":
        return "fail", statuses
    if statuses["seed2"] == "complete" and statuses["m11"] == "complete" and statuses[
        "m5"
    ] in {"running", "complete"}:
        return "ready", statuses
    return "waiting", statuses


def _launch(mode: str, node: str) -> Path | None:
    result = subprocess.run(
        [
            "bash",
            "scripts/launch_mini_a5_plumbing_smoke.sh",
            mode,
            node,
            GPU_LIST,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode == 75:
        return None
    if result.returncode != 0:
        raise RuntimeError(
            f"{mode} smoke launcher failed rc={result.returncode}: "
            f"stdout={result.stdout!r} stderr={result.stderr!r}"
        )
    candidates = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not candidates:
        raise RuntimeError(f"{mode} smoke launcher returned no run directory")
    run_dir = Path(candidates[-1])
    if not (ROOT / run_dir / "run_manifest.json").is_file():
        raise RuntimeError(f"{mode} smoke manifest is absent after launch: {run_dir}")
    return run_dir


def run_queue(
    run_dir: Path,
    *,
    seed2_manifest: Path,
    m11_manifest: Path,
    m5_manifest: Path,
    poll_seconds: int,
    stable_polls: int,
) -> int:
    state_path = run_dir / "queue_state.json"
    state: dict[str, Any] = {
        "schema_version": "blind-gains.mini-a5-smoke-queue.v1",
        "status": "waiting_dependencies",
        "created_utc": _utc(),
        "updated_utc": _utc(),
        "dependencies": {
            "seed2": str(seed2_manifest),
            "m11": str(m11_manifest),
            "m5": str(m5_manifest),
        },
        "dependency_status": {},
        "free_streaks": {"an12": 0, "an29": 0},
        "node_snapshots": {},
        "selected_node": None,
        "smokes": {
            "cp": {"status": "pending", "run_dir": None},
            "member": {"status": "pending", "run_dir": None},
        },
        "audit": {"status": "pending"},
        "events": [],
        "performance_values_opened": False,
        "main_optimizer_steps_authorized": 0,
        "scientific_gate_decision": None,
    }
    _atomic(state_path, state)

    while True:
        dep_state, statuses = dependency_state(
            seed2_manifest, m11_manifest, m5_manifest
        )
        state["dependency_status"] = statuses
        state["updated_utc"] = _utc()
        if dep_state == "fail":
            state["status"] = "failed_dependency"
            state["events"].append(
                {"time_utc": _utc(), "event": "dependency_failed", "statuses": statuses}
            )
            _atomic(state_path, state)
            return 2
        if dep_state == "ready":
            break
        _atomic(state_path, state)
        time.sleep(poll_seconds)

    state["status"] = "waiting_full_node"
    _atomic(state_path, state)
    selected: str | None = None
    while selected is None:
        for node in ("an29", "an12"):
            try:
                snapshot = node_gpu_snapshot(node)
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                state["free_streaks"][node] = 0
                state["node_snapshots"][node] = {"error": str(error)}
                continue
            state["node_snapshots"][node] = snapshot
            state["free_streaks"][node] = (
                state["free_streaks"][node] + 1 if node_is_fully_free(snapshot) else 0
            )
            if state["free_streaks"][node] >= stable_polls:
                selected = node
                break
        state["updated_utc"] = _utc()
        _atomic(state_path, state)
        if selected is None:
            time.sleep(poll_seconds)

    state["selected_node"] = selected
    state["events"].append(
        {"time_utc": _utc(), "event": "full_node_selected", "node": selected}
    )
    _atomic(state_path, state)

    for mode in ("cp", "member"):
        while True:
            launched = _launch(mode, selected)
            if launched is not None:
                break
            state["events"].append(
                {"time_utc": _utc(), "event": "launch_race_retry", "mode": mode}
            )
            state["updated_utc"] = _utc()
            _atomic(state_path, state)
            time.sleep(poll_seconds)
        state["smokes"][mode] = {"status": "running", "run_dir": str(launched)}
        state["status"] = f"running_{mode}"
        state["events"].append(
            {
                "time_utc": _utc(),
                "event": "smoke_launched",
                "mode": mode,
                "run_dir": str(launched),
            }
        )
        _atomic(state_path, state)
        manifest_path = ROOT / launched / "run_manifest.json"
        while True:
            manifest = _read(manifest_path)
            status = manifest.get("status")
            if status == "complete":
                state["smokes"][mode]["status"] = "complete"
                state["events"].append(
                    {"time_utc": _utc(), "event": "smoke_completed", "mode": mode}
                )
                _atomic(state_path, state)
                break
            if status == "fail":
                state["smokes"][mode]["status"] = "fail"
                state["status"] = f"failed_{mode}"
                state["events"].append(
                    {"time_utc": _utc(), "event": "smoke_failed", "mode": mode}
                )
                _atomic(state_path, state)
                return 3
            time.sleep(poll_seconds)

    cp_manifest = ROOT / state["smokes"]["cp"]["run_dir"] / "run_manifest.json"
    member_manifest = (
        ROOT / state["smokes"]["member"]["run_dir"] / "run_manifest.json"
    )
    audit_json = ROOT / "reports/mini_a5_plumbing_smoke_audit_v1.json"
    audit_md = ROOT / "reports/mini_a5_plumbing_smoke_audit_v1.md"
    result = subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            "scripts/audit_mini_a5_plumbing_smoke.py",
            "--cp-manifest",
            str(cp_manifest),
            "--member-manifest",
            str(member_manifest),
            "--json-output",
            str(audit_json),
            "--markdown-output",
            str(audit_md),
        ],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": "."},
        capture_output=True,
        text=True,
    )
    state["audit"] = {
        "status": "complete" if result.returncode == 0 else "fail",
        "json": str(audit_json.relative_to(ROOT)),
        "markdown": str(audit_md.relative_to(ROOT)),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    state["status"] = "complete" if result.returncode == 0 else "failed_audit"
    state["updated_utc"] = _utc()
    _atomic(state_path, state)
    return 0 if result.returncode == 0 else 4


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--seed2-manifest", type=Path, required=True)
    parser.add_argument("--m11-manifest", type=Path, required=True)
    parser.add_argument("--m5-manifest", type=Path, required=True)
    parser.add_argument("--poll-seconds", type=int, default=60)
    parser.add_argument("--stable-polls", type=int, default=2)
    args = parser.parse_args()
    if args.poll_seconds < 1 or args.stable_polls < 1:
        raise ValueError("poll interval and stable poll count must be positive")
    raise SystemExit(
        run_queue(
            args.run_dir,
            seed2_manifest=args.seed2_manifest,
            m11_manifest=args.m11_manifest,
            m5_manifest=args.m5_manifest,
            poll_seconds=args.poll_seconds,
            stable_polls=args.stable_polls,
        )
    )


if __name__ == "__main__":
    main()
