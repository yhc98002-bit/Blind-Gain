#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_GLOO_SIGNATURE = "Gloo connectFullMesh failed"


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _parse_time(value: Any) -> dt.datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def validate_inputs(
    cp_manifest_path: Path,
    failed_member_manifest_path: Path,
    preflight_manifest_path: Path,
) -> dict[str, Any]:
    cp = _read(cp_manifest_path)
    failed_member = _read(failed_member_manifest_path)
    preflight = _read(preflight_manifest_path)
    failed_log_path = ROOT / str(failed_member.get("stdout_stderr_log", ""))
    failed_log = (
        failed_log_path.read_text(encoding="utf-8", errors="replace")
        if failed_log_path.is_file()
        else ""
    )
    failed_checkpoint = Path(str(failed_member.get("checkpoint_path", "")))
    preflight_artifacts = preflight.get("expected_artifacts")
    preflight_output_path = (
        ROOT / str(preflight_artifacts[0])
        if isinstance(preflight_artifacts, list) and preflight_artifacts
        else Path()
    )
    preflight_output = (
        _read(preflight_output_path) if preflight_output_path.is_file() else {}
    )
    preflight_end = _parse_time(preflight.get("end_time_utc"))
    preflight_age_seconds = (
        (dt.datetime.now(dt.timezone.utc) - preflight_end).total_seconds()
        if preflight_end is not None
        else None
    )
    checks = {
        "cp_smoke_completed": cp.get("status") == "complete"
        and cp.get("exit_code") == 0
        and cp.get("artifacts_exist") is True
        and cp.get("smoke_mode") == "cp"
        and cp.get("job_type") == "m6_mini_a5_registered_plumbing_smoke",
        "failed_member_identity_exact": failed_member.get("status") == "fail"
        and failed_member.get("exit_code") != 0
        and failed_member.get("smoke_mode") == "member"
        and failed_member.get("job_type") == "m6_mini_a5_registered_plumbing_smoke",
        "failed_member_has_exact_gloo_signature": EXPECTED_GLOO_SIGNATURE in failed_log,
        "failed_member_has_no_checkpoint": not failed_checkpoint.exists(),
        "same_node_and_gpu_set": cp.get("node") == failed_member.get("node") == preflight.get("node")
        and sorted(cp.get("gpu_ids", [])) == list(range(8))
        and sorted(failed_member.get("gpu_ids", [])) == list(range(8))
        and sorted(preflight.get("gpu_ids", [])) == list(range(8)),
        "collective_preflight_complete": preflight.get("status") == "complete"
        and preflight.get("exit_code") == 0
        and preflight.get("artifacts_exist") is True
        and preflight.get("job_type") == "m6_single_node_collective_preflight",
        "collective_preflight_fresh": preflight_age_seconds is not None
        and 0 <= preflight_age_seconds <= 900,
        "collective_preflight_all_checks_pass": preflight_output.get("status") == "pass"
        and isinstance(preflight_output.get("checks"), dict)
        and bool(preflight_output.get("checks"))
        and all(preflight_output["checks"].values()),
        "collective_preflight_includes_default_and_ib0": [
            item.get("round_name") for item in preflight_output.get("rounds", [])
        ]
        == ["default", "ib0"],
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "cp_manifest": str(cp_manifest_path),
        "failed_member_manifest": str(failed_member_manifest_path),
        "preflight_manifest": str(preflight_manifest_path),
        "preflight_age_seconds": preflight_age_seconds,
    }


def node_ready(node: str) -> tuple[bool, dict[str, Any]]:
    command = r'''set -euo pipefail
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader,nounits
echo __MEM__ $(awk '/MemAvailable:/{print $2}' /proc/meminfo)
echo __SHM__ $(df -Pk /dev/shm | awk 'NR==2 {print $4}')
if ps -eo args= | awk -v root='__BLIND_GAINS_ROOT__' '$0 ~ /[p]ython.*verl[.]trainer[.]main/ && index($0, root) {found=1} END {exit found ? 0 : 1}'; then exit 42; fi
'''.replace("__BLIND_GAINS_ROOT__", str(ROOT))
    result = subprocess.run(
        ["ssh", node, command],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    lines = result.stdout.splitlines()
    gpu_rows = [line for line in lines if line and line[0].isdigit() and "," in line]
    gpus: list[dict[str, int]] = []
    for row in gpu_rows:
        index, memory, utilization = [int(item.strip()) for item in row.split(",")]
        gpus.append({"index": index, "memory_mib": memory, "utilization_pct": utilization})
    mem = next((int(line.split()[1]) for line in lines if line.startswith("__MEM__")), 0)
    shm = next((int(line.split()[1]) for line in lines if line.startswith("__SHM__")), 0)
    ready = (
        result.returncode == 0
        and [gpu["index"] for gpu in gpus] == list(range(8))
        and all(gpu["memory_mib"] < 1024 and gpu["utilization_pct"] <= 10 for gpu in gpus)
        and mem >= 681574400
        and shm >= 41943040
    )
    return ready, {
        "returncode": result.returncode,
        "gpus": gpus,
        "mem_available_kib": mem,
        "dev_shm_available_kib": shm,
        "stderr": result.stderr.strip(),
    }


def run_recovery(
    run_dir: Path,
    *,
    cp_manifest: Path,
    failed_member_manifest: Path,
    preflight_manifest: Path,
    node: str,
    poll_seconds: int,
    stable_polls: int,
) -> int:
    state_path = run_dir / "recovery_state.json"
    input_audit = validate_inputs(cp_manifest, failed_member_manifest, preflight_manifest)
    state: dict[str, Any] = {
        "schema_version": "blind-gains.m6-member-smoke-recovery.v1",
        "status": "validating_inputs",
        "input_audit": input_audit,
        "main_optimizer_steps_authorized": 0,
        "scientific_gate_decision": None,
        "events": [],
        "created_utc": _now(),
    }
    if input_audit["status"] != "pass":
        state["status"] = "failed_input_audit"
        _write(state_path, state)
        return 2

    for index in range(stable_polls):
        ready, snapshot = node_ready(node)
        state["events"].append(
            {"event": "quiet_preflight", "poll": index + 1, "time_utc": _now(), "snapshot": snapshot}
        )
        state["status"] = "waiting_node_quiet"
        _write(state_path, state)
        if not ready:
            state["status"] = "failed_node_not_quiet"
            _write(state_path, state)
            return 75
        if index + 1 < stable_polls:
            time.sleep(poll_seconds)

    launch = subprocess.run(
        ["bash", "scripts/launch_mini_a5_plumbing_smoke.sh", "member", node, "0,1,2,3,4,5,6,7"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    state["events"].append(
        {
            "event": "member_launch",
            "time_utc": _now(),
            "returncode": launch.returncode,
            "stdout": launch.stdout.strip(),
            "stderr": launch.stderr.strip(),
        }
    )
    if launch.returncode != 0:
        state["status"] = "failed_member_launch"
        _write(state_path, state)
        return 3
    recovered_run = Path(launch.stdout.strip().splitlines()[-1])
    recovered_manifest = ROOT / recovered_run / "run_manifest.json"
    state["recovered_member_run"] = str(recovered_run)
    state["status"] = "member_running"
    _write(state_path, state)

    deadline = time.monotonic() + 2400
    while time.monotonic() < deadline:
        if recovered_manifest.is_file():
            recovered = _read(recovered_manifest)
            status = recovered.get("status")
            if status == "complete":
                break
            if status in {"fail", "failed", "error", "blocked"}:
                state["status"] = "failed_recovered_member"
                state["recovered_member_manifest"] = str(recovered_manifest.relative_to(ROOT))
                _write(state_path, state)
                return 4
        time.sleep(20)
    else:
        state["status"] = "failed_recovered_member_timeout"
        _write(state_path, state)
        return 5

    audit_json = ROOT / "reports/mini_a5_plumbing_smoke_audit_v1.json"
    audit_md = ROOT / "reports/mini_a5_plumbing_smoke_audit_v1.md"
    audit = subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            "scripts/audit_mini_a5_plumbing_smoke.py",
            "--cp-manifest",
            str(cp_manifest),
            "--member-manifest",
            str(recovered_manifest),
            "--json-output",
            str(audit_json),
            "--markdown-output",
            str(audit_md),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    state["events"].append(
        {
            "event": "combined_smoke_audit",
            "time_utc": _now(),
            "returncode": audit.returncode,
            "stdout": audit.stdout.strip(),
            "stderr": audit.stderr.strip(),
        }
    )
    if audit.returncode != 0:
        state["status"] = "failed_combined_audit"
        _write(state_path, state)
        return 6
    state.update(
        {
            "status": "complete",
            "recovered_member_manifest": str(recovered_manifest.relative_to(ROOT)),
            "audit_json": str(audit_json.relative_to(ROOT)),
            "audit_markdown": str(audit_md.relative_to(ROOT)),
            "completed_utc": _now(),
        }
    )
    _write(state_path, state)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--cp-manifest", type=Path, required=True)
    parser.add_argument("--failed-member-manifest", type=Path, required=True)
    parser.add_argument("--preflight-manifest", type=Path, required=True)
    parser.add_argument("--node", choices=("an12", "an29"), required=True)
    parser.add_argument("--poll-seconds", type=int, default=30)
    parser.add_argument("--stable-polls", type=int, default=4)
    args = parser.parse_args()
    if args.poll_seconds < 10 or args.stable_polls < 3:
        raise ValueError("member recovery requires at least three quiet polls, >=10 seconds apart")
    raise SystemExit(
        run_recovery(
            args.run_dir,
            cp_manifest=args.cp_manifest,
            failed_member_manifest=args.failed_member_manifest,
            preflight_manifest=args.preflight_manifest,
            node=args.node,
            poll_seconds=args.poll_seconds,
            stable_polls=args.stable_polls,
        )
    )


if __name__ == "__main__":
    main()
