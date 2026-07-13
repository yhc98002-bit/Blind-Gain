#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def prepare_recovery_config(
    source: Path,
    output: Path,
    *,
    experiment_name: str,
    checkpoint_path: Path,
) -> None:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite recovery config: {output}")
    payload = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("trainer"), dict):
        raise ValueError("pilot config has no trainer mapping")
    trainer = payload["trainer"]
    if not trainer.get("experiment_name") or not trainer.get("save_checkpoint_path"):
        raise ValueError("pilot config lacks registered experiment/checkpoint fields")
    trainer["experiment_name"] = experiment_name
    trainer["save_checkpoint_path"] = str(checkpoint_path.resolve())
    trainer["load_checkpoint_path"] = None
    trainer["find_last_checkpoint"] = False
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--experiment-name", required=True)
    parser.add_argument("--checkpoint-path", type=Path, required=True)
    args = parser.parse_args()
    prepare_recovery_config(
        args.source,
        args.output,
        experiment_name=args.experiment_name,
        checkpoint_path=args.checkpoint_path,
    )


if __name__ == "__main__":
    main()
