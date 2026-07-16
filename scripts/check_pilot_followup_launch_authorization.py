#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import yaml

from scripts.prepare_pilot_followup_configs import ALLOWED_DIFFS, ARMS, config_diff


ROOT = Path(__file__).resolve().parents[1]
REGISTRATION = Path("docs/registered_pilot_seed23_v1.md")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ledger(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        task, status, _ = line.split(" | ", maxsplit=2)
        result[task] = status
    return result


def build_authorization(arm: str, seed: int, checkpoint: Path) -> dict[str, Any]:
    if arm not in ARMS or seed not in {2, 3}:
        raise ValueError("unsupported arm or seed")
    base_name = ARMS[arm]
    config = ROOT / "configs/train" / f"{base_name}_seed{seed}_3b_geo3k.yaml"
    source = ROOT / "configs/train" / f"{base_name}_3b_geo3k.yaml"
    registration = ROOT / REGISTRATION
    registration_text = registration.read_text(encoding="utf-8") if registration.is_file() else ""
    main = _ledger(ROOT / "reports/main_progress.md")
    expected_checkpoint = (ROOT / "checkpoints/pilot" / f"{base_name}_seed{seed}").resolve()
    try:
        source_payload = yaml.safe_load(source.read_text(encoding="utf-8"))
        config_payload = yaml.safe_load(config.read_text(encoding="utf-8"))
        differences = config_diff(source_payload, config_payload)
    except (OSError, ValueError, TypeError, yaml.YAMLError):
        source_payload, config_payload, differences = {}, {}, set()
    config_hash = _sha256(config) if config.is_file() else None
    checks = {
        "m2_seed1_complete": main.get("M2") == "pass",
        "m3_not_already_complete": main.get("M3") in {"blocked", "fail"},
        "registration_exists": registration.is_file() and registration.stat().st_size > 0,
        "registration_merged_marker": "Registration state: merged-at-HEAD; merge is sign-off." in registration_text,
        "seed_registered": f"Seed `{seed}`" in registration_text,
        "config_hash_registered": isinstance(config_hash, str) and config_hash in registration_text,
        "config_exact_allowed_diff": differences == ALLOWED_DIFFS,
        "seed_value_exact": config_payload.get("data", {}).get("seed") == seed,
        "image_condition_seed_fixed": config_payload.get("data", {}).get("image_condition_seed") == 20260710,
        "checkpoint_path_exact": checkpoint.resolve() == expected_checkpoint,
        "checkpoint_namespace_absent": checkpoint.resolve() == expected_checkpoint and not checkpoint.exists(),
    }
    return {
        "schema_version": "blind-gains.pilot-followup-launch-authorization.v1",
        "status": "authorized" if all(checks.values()) else "blocked",
        "arm": arm,
        "seed": seed,
        "config": str(config.relative_to(ROOT)),
        "config_sha256": config_hash,
        "registration": str(REGISTRATION),
        "registration_sha256": _sha256(registration) if registration.is_file() else None,
        "checkpoint_path": str(checkpoint.resolve()),
        "checks": checks,
        "errors": [name for name, value in checks.items() if not value],
        "scientific_gate_decision": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=tuple(ARMS), required=True)
    parser.add_argument("--seed", type=int, choices=(2, 3), required=True)
    parser.add_argument("--checkpoint-path", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    payload = build_authorization(args.arm, args.seed, args.checkpoint_path)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(f".{args.output.name}.partial.{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, args.output)
    print(json.dumps(payload, sort_keys=True))
    raise SystemExit(0 if payload["status"] == "authorized" else 1)


if __name__ == "__main__":
    main()
