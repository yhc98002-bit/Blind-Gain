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
TERMINAL_FAILURES = {"fail", "failed", "error", "cancelled", "canceled"}


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def terminal_outcome(manifest: dict[str, Any]) -> str:
    status = manifest.get("status")
    if status == "complete":
        return "complete" if (
            manifest.get("exit_code") == 0
            and manifest.get("artifacts_exist") is True
            and manifest.get("end_time_utc")
        ) else "failed"
    if status in TERMINAL_FAILURES:
        return "failed"
    if status == "running" and manifest.get("exit_code") is None:
        return "running"
    return "invalid"


def release_candidates(outcomes: dict[str, str]) -> list[str]:
    candidates = []
    if outcomes["a1_real"] == "complete":
        candidates.append("an12")
    if outcomes["a2b_noimage"] == "complete" and outcomes["a3_caption"] == "complete":
        candidates.append("an29")
    return candidates


def impossible(outcomes: dict[str, str]) -> bool:
    an12_impossible = outcomes["a1_real"] in {"failed", "invalid"}
    an29_impossible = any(
        outcomes[arm] in {"failed", "invalid"} for arm in ("a2b_noimage", "a3_caption")
    )
    return an12_impossible and an29_impossible


def run(config_path: Path, *, once: bool = False) -> int:
    config = _load(config_path)
    if config.get("schema_version") != "blind-gains.a2-resume60-release-queue.v1":
        raise ValueError("unsupported A2 release queue config")
    state_path = ROOT / config["state_path"]
    terminal_path = ROOT / config["terminal_path"]
    launch_log = ROOT / config["launch_log"]
    while True:
        manifests = {
            arm: _load(ROOT / relative) for arm, relative in config["upstream_manifests"].items()
        }
        outcomes = {arm: terminal_outcome(manifest) for arm, manifest in manifests.items()}
        candidates = release_candidates(outcomes)
        state = {
            "schema_version": "blind-gains.a2-resume60-release-state.v1",
            "observed_at_utc": _now(),
            "status": "ready" if candidates else ("failed" if impossible(outcomes) else "waiting"),
            "upstream_outcomes": outcomes,
            "release_candidates": candidates,
            "metric_access": False,
            "note": "Release decisions use run lifecycle state only; no training or validation metric is read.",
        }
        _atomic_json(state_path, state)
        if impossible(outcomes):
            _atomic_json(terminal_path, {**state, "result": "no_release_path"})
            return 1
        for node in candidates:
            command = [
                "bash",
                "scripts/launch_mech_pilot_resume60.sh",
                "a2_gray",
                node,
                "0,1,2,3",
                config["a2_failed_source_run"],
            ]
            result = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            launch_log.parent.mkdir(parents=True, exist_ok=True)
            with launch_log.open("a", encoding="utf-8") as handle:
                handle.write(
                    json.dumps(
                        {
                            "time_utc": _now(), "node": node, "returncode": result.returncode,
                            "stdout": result.stdout, "stderr": result.stderr,
                        },
                        sort_keys=True,
                    )
                    + "\n"
                )
            if result.returncode == 75:
                continue
            if result.returncode != 0:
                _atomic_json(
                    terminal_path,
                    {**state, "result": "launcher_failed", "node": node, "returncode": result.returncode},
                )
                return 1
            launched = next(
                (line for line in result.stdout.splitlines() if line.startswith("experiments/runs/mech_a2_gray_resume60_")),
                None,
            )
            if launched is None:
                _atomic_json(terminal_path, {**state, "result": "launcher_output_invalid", "node": node})
                return 1
            watchdog = subprocess.run(
                [
                    "bash", "scripts/launch_m2_completion_watchdog.sh",
                    config["a1_resume_run"], launched,
                    config["a2b_run"], config["a3_run"],
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            result_payload = {
                **state,
                "status": "complete",
                "result": "a2_launched",
                "node": node,
                "a2_run": launched,
                "completion_watchdog_returncode": watchdog.returncode,
                "completion_watchdog_stdout": watchdog.stdout,
                "completion_watchdog_stderr": watchdog.stderr,
            }
            _atomic_json(terminal_path, result_payload)
            return 0 if watchdog.returncode == 0 else 1
        if once:
            return 3
        time.sleep(int(config["poll_interval_seconds"]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    raise SystemExit(run(args.config, once=args.once))


if __name__ == "__main__":
    main()
