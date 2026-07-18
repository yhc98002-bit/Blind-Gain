#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import yaml


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_recovery_config(
    base_path: Path,
    output_path: Path,
    *,
    load_checkpoint_path: Path,
    save_checkpoint_path: Path,
) -> dict[str, Any]:
    payload = yaml.safe_load(base_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("trainer"), dict):
        raise ValueError("M5 base config has no trainer mapping")
    trainer = payload["trainer"]
    if trainer.get("max_steps") != 400:
        raise ValueError("M5 recovery must retain terminal max_steps=400")
    before = json.loads(json.dumps(payload))
    trainer["load_checkpoint_path"] = str(load_checkpoint_path.resolve())
    trainer["save_checkpoint_path"] = str(save_checkpoint_path.resolve())
    after_without_paths = json.loads(json.dumps(payload))
    before["trainer"].pop("load_checkpoint_path", None)
    before["trainer"].pop("save_checkpoint_path", None)
    after_without_paths["trainer"].pop("load_checkpoint_path", None)
    after_without_paths["trainer"].pop("save_checkpoint_path", None)
    if before != after_without_paths:
        raise RuntimeError("recovery config changed fields beyond checkpoint paths")
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite recovery config: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(f".{output_path.name}.partial.{os.getpid()}")
    temporary.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    os.replace(temporary, output_path)
    return {
        "schema_version": "blind-gains.m5-recovery-config.v1",
        "status": "pass",
        "base_config": str(base_path),
        "base_config_sha256": sha256_file(base_path),
        "output_config": str(output_path),
        "output_config_sha256": sha256_file(output_path),
        "only_checkpoint_paths_changed": True,
        "load_checkpoint_path": str(load_checkpoint_path.resolve()),
        "save_checkpoint_path": str(save_checkpoint_path.resolve()),
        "terminal_step": 400,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--load-checkpoint-path", type=Path, required=True)
    parser.add_argument("--save-checkpoint-path", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    args = parser.parse_args()
    if args.audit_output.exists():
        raise FileExistsError(f"refusing to overwrite config audit: {args.audit_output}")
    audit = build_recovery_config(
        args.base,
        args.output,
        load_checkpoint_path=args.load_checkpoint_path,
        save_checkpoint_path=args.save_checkpoint_path,
    )
    args.audit_output.write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
