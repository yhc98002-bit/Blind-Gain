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


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ARMS = ("a1_real", "a2_gray", "a2b_noimage", "a3_caption")
TERMINAL_FAILURE_STATUSES = {"fail", "failed", "error", "cancelled", "canceled"}


def _now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _resolve_within_root(root: Path, value: str) -> Path:
    candidate = Path(value)
    resolved = (candidate if candidate.is_absolute() else root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as error:
        raise ValueError(f"path escapes repository root: {value}") from error
    return resolved


def validate_config(config: dict[str, Any], root: Path = ROOT) -> None:
    if config.get("schema_version") != "blind-gains.m2-completion-watchdog-config.v1":
        raise ValueError("unsupported M2 watchdog config schema")
    arms = config.get("arms")
    if not isinstance(arms, list) or len(arms) != len(EXPECTED_ARMS):
        raise ValueError("M2 watchdog requires exactly four pinned arm manifests")
    if not all(isinstance(item, dict) for item in arms):
        raise ValueError("M2 watchdog arm entries must be JSON objects")
    names = [str(item.get("arm")) for item in arms]
    if sorted(names) != sorted(EXPECTED_ARMS) or len(set(names)) != len(names):
        raise ValueError("M2 watchdog arm registry is incomplete or duplicated")
    for item in arms:
        required = {"arm", "node", "run_id", "manifest"}
        if not required.issubset(item):
            raise ValueError(f"M2 watchdog arm entry lacks fields: {item}")
        if item["node"] not in {"an12", "an29"}:
            raise ValueError(f"invalid compute node: {item['node']}")
        _resolve_within_root(root, str(item["manifest"]))
    interval = config.get("poll_interval_seconds")
    if not isinstance(interval, int) or interval < 10:
        raise ValueError("poll_interval_seconds must be an integer >= 10")
    for key in ("state_path", "terminal_json", "terminal_markdown"):
        if not isinstance(config.get(key), str):
            raise ValueError(f"M2 watchdog config lacks {key}")
        _resolve_within_root(root, str(config[key]))


def inspect_arm(specification: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    manifest_path = _resolve_within_root(root, str(specification["manifest"]))
    relative_path = str(manifest_path.relative_to(root.resolve()))
    result: dict[str, Any] = {
        "arm": specification["arm"],
        "expected_node": specification["node"],
        "expected_run_id": specification["run_id"],
        "manifest": relative_path,
        "observed_utc": _now_utc(),
        "outcome": "observation_error",
        "errors": [],
    }
    try:
        manifest = _load_json(manifest_path)
        result["manifest_sha256"] = _sha256(manifest_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        result["errors"] = [f"manifest_unreadable:{type(error).__name__}:{error}"]
        return result

    expected = {
        "job_type": "l13_mechanical_pilot_arm",
        "arm": specification["arm"],
        "node": specification["node"],
        "run_id": specification["run_id"],
    }
    errors = [
        f"{field}_mismatch:expected={value!r}:observed={manifest.get(field)!r}"
        for field, value in expected.items()
        if manifest.get(field) != value
    ]
    status = manifest.get("status")
    exit_code = manifest.get("exit_code")
    result.update(
        {
            "observed_status": status,
            "exit_code": exit_code,
            "start_time_utc": manifest.get("start_time_utc"),
            "end_time_utc": manifest.get("end_time_utc"),
            "artifacts_exist": manifest.get("artifacts_exist"),
            "checkpoint_path": manifest.get("checkpoint_path"),
            "gpu_ids": manifest.get("gpu_ids"),
        }
    )
    if errors:
        result["outcome"] = "invalid"
        result["errors"] = errors
        return result

    if status == "complete":
        completion_errors = []
        if exit_code != 0:
            completion_errors.append(f"nonzero_or_missing_exit_code:{exit_code!r}")
        if manifest.get("artifacts_exist") is not True:
            completion_errors.append(
                f"expected_artifacts_not_verified:{manifest.get('artifacts_exist')!r}"
            )
        if not manifest.get("end_time_utc"):
            completion_errors.append("missing_end_time_utc")
        result["outcome"] = "complete" if not completion_errors else "invalid"
        result["errors"] = completion_errors
        return result

    if status in TERMINAL_FAILURE_STATUSES:
        result["outcome"] = "failed"
        result["errors"] = [f"terminal_parent_status:{status}:exit_code={exit_code!r}"]
        return result

    if status == "running" and exit_code is None and not manifest.get("end_time_utc"):
        result["outcome"] = "running"
        return result

    result["outcome"] = "invalid"
    result["errors"] = [
        f"inconsistent_parent_state:status={status!r}:exit_code={exit_code!r}:"
        f"end_time_utc={manifest.get('end_time_utc')!r}"
    ]
    return result


def observe(config: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    validate_config(config, root)
    arms = [inspect_arm(specification, root) for specification in config["arms"]]
    outcomes = {item["outcome"] for item in arms}
    if outcomes == {"complete"}:
        status = "complete"
    elif outcomes.intersection({"failed", "invalid"}):
        status = "failed"
    else:
        status = "watching"
    return {
        "schema_version": "blind-gains.m2-completion-watchdog-observation.v1",
        "observed_utc": _now_utc(),
        "status": status,
        "complete_arm_count": sum(item["outcome"] == "complete" for item in arms),
        "required_arm_count": len(EXPECTED_ARMS),
        "arms": arms,
        "scientific_gate_decision": None,
        "note": "Mechanical run completion only; this watchdog never declares a scientific gate.",
    }


def _update_state(
    previous: dict[str, Any] | None,
    observation: dict[str, Any],
    config_sha256: str,
) -> dict[str, Any]:
    state = previous or {
        "schema_version": "blind-gains.m2-completion-watchdog-state.v1",
        "created_utc": _now_utc(),
        "poll_count": 0,
        "events": [],
        "last_outcomes": {},
    }
    old_outcomes = dict(state.get("last_outcomes", {}))
    new_outcomes = {item["arm"]: item["outcome"] for item in observation["arms"]}
    for arm in EXPECTED_ARMS:
        if old_outcomes.get(arm) != new_outcomes.get(arm):
            state.setdefault("events", []).append(
                {
                    "time_utc": observation["observed_utc"],
                    "event": "arm_outcome_changed",
                    "arm": arm,
                    "from": old_outcomes.get(arm),
                    "to": new_outcomes.get(arm),
                }
            )
    state.update(
        {
            "updated_utc": observation["observed_utc"],
            "poll_count": int(state.get("poll_count", 0)) + 1,
            "status": observation["status"],
            "complete_arm_count": observation["complete_arm_count"],
            "required_arm_count": observation["required_arm_count"],
            "config_sha256": config_sha256,
            "last_outcomes": new_outcomes,
            "arms": observation["arms"],
            "scientific_gate_decision": None,
        }
    )
    return state


def _terminal_markdown(notification: dict[str, Any]) -> str:
    lines = [
        "# M2 Pilot Completion Watchdog",
        "",
        f"- Result: `{notification['result']}`",
        f"- Time (UTC): `{notification['terminal_time_utc']}`",
        f"- Completed arms: `{notification['complete_arm_count']}/{notification['required_arm_count']}`",
        "- Scientific gate decision: `none`",
        "",
        "| Arm | Node | Outcome | Parent status | Exit code | Manifest |",
        "|---|---|---|---|---:|---|",
    ]
    for item in notification["arms"]:
        lines.append(
            "| {arm} | {node} | {outcome} | {status} | {exit_code} | `{manifest}` |".format(
                arm=item["arm"],
                node=item["expected_node"],
                outcome=item["outcome"],
                status=item.get("observed_status"),
                exit_code=item.get("exit_code"),
                manifest=item["manifest"],
            )
        )
    lines.extend(
        [
            "",
            "This is a mechanical completion/failure notification. It does not interpret metrics or pass a PI gate.",
            "",
        ]
    )
    return "\n".join(lines)


def write_terminal_notification(
    config: dict[str, Any], state: dict[str, Any], root: Path = ROOT
) -> None:
    json_path = _resolve_within_root(root, str(config["terminal_json"]))
    markdown_path = _resolve_within_root(root, str(config["terminal_markdown"]))
    result = "complete" if state["status"] == "complete" else "failed"
    notification = {
        "schema_version": "blind-gains.m2-completion-watchdog-terminal.v1",
        "result": result,
        "terminal_time_utc": _now_utc(),
        "complete_arm_count": state["complete_arm_count"],
        "required_arm_count": state["required_arm_count"],
        "config_sha256": state["config_sha256"],
        "arms": state["arms"],
        "scientific_gate_decision": None,
    }
    if json_path.exists():
        existing = _load_json(json_path)
        identity = ("result", "config_sha256", "required_arm_count")
        if any(existing.get(key) != notification.get(key) for key in identity):
            raise FileExistsError("terminal notification exists with different identity")
        notification = existing
    else:
        if markdown_path.exists():
            raise FileExistsError("terminal Markdown exists without its machine JSON")
        _atomic_json(json_path, notification)
    if markdown_path.exists():
        if markdown_path.read_text(encoding="utf-8") != _terminal_markdown(notification):
            raise FileExistsError("terminal Markdown exists with different content")
        return
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    with markdown_path.open("x", encoding="utf-8") as handle:
        handle.write(_terminal_markdown(notification))


def run_watchdog(config_path: Path, root: Path = ROOT, once: bool = False) -> int:
    config = _load_json(config_path)
    validate_config(config, root)
    config_sha256 = _sha256(config_path)
    state_path = _resolve_within_root(root, str(config["state_path"]))
    previous = _load_json(state_path) if state_path.is_file() else None
    while True:
        observation = observe(config, root)
        state = _update_state(previous, observation, config_sha256)
        _atomic_json(state_path, state)
        print(
            json.dumps(
                {
                    "time_utc": state["updated_utc"],
                    "status": state["status"],
                    "complete": f"{state['complete_arm_count']}/{state['required_arm_count']}",
                    "outcomes": state["last_outcomes"],
                },
                sort_keys=True,
            ),
            flush=True,
        )
        if state["status"] in {"complete", "failed"}:
            write_terminal_notification(config, state, root)
            return 0 if state["status"] == "complete" else 1
        if once:
            return 3
        previous = state
        time.sleep(int(config["poll_interval_seconds"]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    raise SystemExit(run_watchdog(args.config, once=args.once))


if __name__ == "__main__":
    main()
