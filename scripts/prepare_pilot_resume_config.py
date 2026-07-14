#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import yaml


ALLOWED_CHANGES = {
    "trainer.experiment_name",
    "trainer.save_checkpoint_path",
    "trainer.load_checkpoint_path",
    "trainer.find_last_checkpoint",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _differences(left: Any, right: Any, prefix: str = "") -> list[str]:
    if isinstance(left, dict) and isinstance(right, dict):
        keys = sorted(set(left) | set(right))
        changed: list[str] = []
        for key in keys:
            path = f"{prefix}.{key}" if prefix else str(key)
            if key not in left or key not in right:
                changed.append(path)
            else:
                changed.extend(_differences(left[key], right[key], path))
        return changed
    return [] if left == right else [prefix]


def prepare_resume_config(
    source: Path,
    output: Path,
    *,
    experiment_name: str,
    save_checkpoint_path: Path,
    load_checkpoint_path: Path,
    expected_step: int,
    expected_image_condition: str = "caption",
) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite resume config: {output}")
    payload = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("trainer"), dict):
        raise ValueError("pilot config has no trainer mapping")
    trainer = payload["trainer"]
    if trainer.get("max_steps") != 100 or trainer.get("save_freq") != 20:
        raise ValueError("resume source does not have the registered 100-step/20-save budget")
    observed_condition = payload.get("data", {}).get("image_condition")
    if observed_condition != expected_image_condition:
        raise ValueError(
            "resume source image condition mismatch: "
            f"expected {expected_image_condition!r}, found {observed_condition!r}"
        )
    if load_checkpoint_path.name != f"global_step_{expected_step}":
        raise ValueError("load checkpoint basename does not match expected resume step")
    if save_checkpoint_path.resolve() == Path(str(trainer.get("save_checkpoint_path"))).resolve():
        raise ValueError("resume output must use a new immutable checkpoint namespace")

    original = yaml.safe_load(source.read_text(encoding="utf-8"))
    trainer["experiment_name"] = experiment_name
    trainer["save_checkpoint_path"] = str(save_checkpoint_path.resolve())
    trainer["load_checkpoint_path"] = str(load_checkpoint_path.resolve())
    trainer["find_last_checkpoint"] = False
    changed = _differences(original, payload)
    required_changes = {
        "trainer.experiment_name",
        "trainer.save_checkpoint_path",
        "trainer.load_checkpoint_path",
    }
    if not required_changes.issubset(changed) or not set(changed).issubset(ALLOWED_CHANGES):
        raise RuntimeError(f"unexpected scientific config changes: {changed}")

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False)
    return {
        "schema_version": "blind-gains.pilot-resume-config-audit.v1",
        "status": "pass",
        "source_config": str(source.resolve()),
        "source_config_sha256": _sha256(source),
        "resume_config": str(output.resolve()),
        "resume_config_sha256": _sha256(output),
        "changed_fields": changed,
        "allowed_changes": sorted(ALLOWED_CHANGES),
        "resume_global_step": expected_step,
        "image_condition": observed_condition,
        "save_checkpoint_path": str(save_checkpoint_path.resolve()),
        "load_checkpoint_path": str(load_checkpoint_path.resolve()),
        "scientific_config_changed": False,
    }


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite resume audit: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--experiment-name", required=True)
    parser.add_argument("--save-checkpoint-path", type=Path, required=True)
    parser.add_argument("--load-checkpoint-path", type=Path, required=True)
    parser.add_argument("--expected-step", type=int, default=20)
    parser.add_argument("--expected-image-condition", default="caption")
    args = parser.parse_args()
    audit = prepare_resume_config(
        args.source,
        args.output,
        experiment_name=args.experiment_name,
        save_checkpoint_path=args.save_checkpoint_path,
        load_checkpoint_path=args.load_checkpoint_path,
        expected_step=args.expected_step,
        expected_image_condition=args.expected_image_condition,
    )
    _atomic_json(args.audit, audit)
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
