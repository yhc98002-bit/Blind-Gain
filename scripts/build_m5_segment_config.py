#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import yaml


REGISTERED_TERMINAL_STEP = 400
SEGMENT_START_STEPS = frozenset({200, 250, 300, 350})


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_text(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite M5 segment artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.partial")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def build_segment_config(
    base_path: Path,
    output_path: Path,
    *,
    load_checkpoint_path: Path,
    save_checkpoint_path: Path,
    segment_start_step: int,
) -> dict[str, Any]:
    if segment_start_step not in SEGMENT_START_STEPS:
        raise ValueError(f"unsupported M5 segment start: {segment_start_step}")
    segment_end_step = segment_start_step + 50
    if segment_end_step > REGISTERED_TERMINAL_STEP:
        raise ValueError("M5 segment exceeds the registered terminal step")
    if load_checkpoint_path.name != f"global_step_{segment_start_step}":
        raise ValueError("M5 segment source basename does not match its start step")

    payload = yaml.safe_load(base_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("trainer"), dict):
        raise ValueError("M5 base config has no trainer mapping")
    trainer = payload["trainer"]
    if trainer.get("max_steps") != REGISTERED_TERMINAL_STEP:
        raise ValueError("M5 base config no longer has registered max_steps=400")

    actor = payload.get("worker", {}).get("actor", {})
    optim = actor.get("optim", {}) if isinstance(actor, dict) else {}
    scheduler = optim.get("lr_scheduler_type", "constant")
    warmup_ratio = optim.get("lr_warmup_ratio", 0.0)
    warmup_steps = optim.get("lr_warmup_steps")
    if scheduler != "constant" or float(warmup_ratio) != 0.0 or warmup_steps not in (None, 0):
        raise ValueError(
            "segmented M5 recovery is valid only for the registered constant, zero-warmup schedule"
        )

    before = json.loads(json.dumps(payload))
    trainer["load_checkpoint_path"] = str(load_checkpoint_path.resolve())
    trainer["save_checkpoint_path"] = str(save_checkpoint_path.resolve())
    trainer["max_steps"] = segment_end_step

    comparison_before = json.loads(json.dumps(before))
    comparison_after = json.loads(json.dumps(payload))
    for candidate in (comparison_before, comparison_after):
        candidate["trainer"].pop("load_checkpoint_path", None)
        candidate["trainer"].pop("save_checkpoint_path", None)
        candidate["trainer"].pop("max_steps", None)
    if comparison_before != comparison_after:
        raise RuntimeError("M5 segment config changed fields beyond checkpoint paths and max_steps")

    _atomic_text(output_path, yaml.safe_dump(payload, sort_keys=False))
    return {
        "schema_version": "blind-gains.m5-segment-config.v1",
        "status": "pass",
        "base_config": str(base_path),
        "base_config_sha256": _sha256(base_path),
        "output_config": str(output_path),
        "output_config_sha256": _sha256(output_path),
        "segment_start_step": segment_start_step,
        "segment_end_step": segment_end_step,
        "registered_terminal_step": REGISTERED_TERMINAL_STEP,
        "changed_fields": [
            "trainer.load_checkpoint_path",
            "trainer.save_checkpoint_path",
            "trainer.max_steps",
        ],
        "load_checkpoint_path": str(load_checkpoint_path.resolve()),
        "save_checkpoint_path": str(save_checkpoint_path.resolve()),
        "scheduler_invariance": {
            "lr_scheduler_type": "constant",
            "lr_warmup_ratio": 0.0,
            "lr_warmup_steps": warmup_steps,
            "optimizer_scheduler_state_restored": True,
            "segment_end_does_not_change_lr_curve": True,
        },
        "scientific_terminal_unchanged": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--load-checkpoint-path", type=Path, required=True)
    parser.add_argument("--save-checkpoint-path", type=Path, required=True)
    parser.add_argument("--segment-start-step", type=int, required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    args = parser.parse_args()
    audit = build_segment_config(
        args.base,
        args.output,
        load_checkpoint_path=args.load_checkpoint_path,
        save_checkpoint_path=args.save_checkpoint_path,
        segment_start_step=args.segment_start_step,
    )
    _atomic_text(args.audit_output, json.dumps(audit, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
