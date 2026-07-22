#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

from scripts import build_pilot_4arm_seed1_readout as builder


ROOT = Path(__file__).resolve().parents[1]
TERMINAL_FAILURES = {"fail", "failed", "error", "cancelled", "canceled"}


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _atomic_state(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.partial")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def wait_for_lifecycle_gate(
    config: dict[str, Any],
    *,
    config_path: Path,
    expected_config_hash: str,
    state_path: Path,
    poll_seconds: int,
) -> dict[str, Any]:
    """Wait on structural state only; never open a prediction row here."""
    builder.validate_config_structure(config)
    lifecycle_path = builder._resolve(
        ROOT, str(config["evaluation_lifecycle_manifest"])
    )
    while True:
        if _sha256(config_path) != expected_config_hash:
            raise ValueError("readout config changed while queued")
        lifecycle = _read_json(lifecycle_path)
        status = str(lifecycle.get("status", "unknown"))
        state = {
            "schema_version": "blind-gains.pilot-fourarm-readout-queue-state.v1",
            "status": "waiting_lifecycle",
            "seed": config["seed"],
            "updated_utc": _now(),
            "lifecycle_manifest": str(lifecycle_path.relative_to(ROOT)),
            "lifecycle_status": status,
            "performance_values_opened": False,
            "scientific_gate_decision": None,
        }
        _atomic_state(state_path, state)
        if status in TERMINAL_FAILURES:
            raise RuntimeError(f"evaluation lifecycle failed closed: {status}")
        if status == "complete":
            gate = builder._validate_followup_lifecycle_gate(config, ROOT)
            if gate is None:
                raise ValueError("follow-up lifecycle gate unexpectedly absent")
            return gate
        time.sleep(poll_seconds)


def execute_readout(
    *,
    config_path: Path,
    expected_config_hash: str,
    state_path: Path,
    artifact_dir: Path,
    json_output: Path,
    markdown_output: Path,
    poll_seconds: int,
) -> dict[str, Any]:
    config = _read_json(config_path)
    config["config_path"] = str(config_path.relative_to(ROOT))
    if any(path.exists() for path in (artifact_dir, json_output, markdown_output)):
        raise FileExistsError("refusing to overwrite seed readout artifacts")
    performance_values_opened = False
    try:
        gate = wait_for_lifecycle_gate(
            config,
            config_path=config_path,
            expected_config_hash=expected_config_hash,
            state_path=state_path,
            poll_seconds=poll_seconds,
        )
        gate_record = {
            "schema_version": "blind-gains.pilot-fourarm-readout-open-gate.v1",
            "status": "pass",
            "seed": config["seed"],
            "validated_at_utc": _now(),
            "lifecycle_manifest": str(gate["manifest"].relative_to(ROOT)),
            "lifecycle_manifest_sha256": _sha256(gate["manifest"]),
            "lifecycle_output": str(gate["output"].relative_to(ROOT)),
            "lifecycle_output_sha256": _sha256(gate["output"]),
            "eight_endpoints_complete": True,
            "performance_values_opened_before_gate": False,
            "scientific_gate_decision": None,
        }
        gate_path = state_path.with_name("readout_open_gate.json")
        _atomic_state(gate_path, gate_record)
        performance_values_opened = True
        _atomic_state(
            state_path,
            {
                "schema_version": "blind-gains.pilot-fourarm-readout-queue-state.v1",
                "status": "building_unified_readout",
                "seed": config["seed"],
                "updated_utc": _now(),
                "readout_open_gate": str(gate_path.relative_to(ROOT)),
                "performance_values_opened": True,
                "scientific_gate_decision": None,
            },
        )
        payload = builder.build_readout(
            config,
            root=ROOT,
            artifact_dir=artifact_dir,
        )
        markdown = builder.render_markdown(payload, json_output.relative_to(ROOT))
        builder._write_text(
            json_output, json.dumps(payload, indent=2, sort_keys=True) + "\n"
        )
        builder._write_text(markdown_output, markdown)
        complete = {
            "schema_version": "blind-gains.pilot-fourarm-readout-queue-state.v1",
            "status": "complete",
            "seed": config["seed"],
            "updated_utc": _now(),
            "readout_open_gate": str(gate_path.relative_to(ROOT)),
            "json_output": str(json_output.relative_to(ROOT)),
            "json_sha256": _sha256(json_output),
            "markdown_output": str(markdown_output.relative_to(ROOT)),
            "markdown_sha256": _sha256(markdown_output),
            "artifact_dir": str(artifact_dir.relative_to(ROOT)),
            "performance_values_opened": True,
            "performance_values_opened_only_after_complete_lifecycle": True,
            "scientific_gate_decision": None,
        }
        _atomic_state(state_path, complete)
        return complete
    except Exception as error:
        _atomic_state(
            state_path,
            {
                "schema_version": "blind-gains.pilot-fourarm-readout-queue-state.v1",
                "status": "fail",
                "seed": config.get("seed"),
                "updated_utc": _now(),
                "error_type": type(error).__name__,
                "error": str(error),
                "performance_values_opened": performance_values_opened,
                "scientific_gate_decision": None,
            },
        )
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--config-sha256", required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--poll-seconds", type=int, default=60)
    args = parser.parse_args()
    if args.poll_seconds < 10:
        raise ValueError("poll interval must be at least 10 seconds")
    execute_readout(
        config_path=builder._resolve(ROOT, str(args.config)),
        expected_config_hash=args.config_sha256,
        state_path=builder._resolve(ROOT, str(args.state)),
        artifact_dir=builder._resolve(ROOT, str(args.artifact_dir)),
        json_output=builder._resolve(ROOT, str(args.json_output)),
        markdown_output=builder._resolve(ROOT, str(args.markdown_output)),
        poll_seconds=args.poll_seconds,
    )


if __name__ == "__main__":
    main()
