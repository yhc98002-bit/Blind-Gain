#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
ARMS = {
    "a1_real": "mech_a1_real",
    "a2_gray": "mech_a2_gray",
    "a2b_noimage": "mech_a2b_noimage",
    "a3_caption": "mech_a3_caption",
}
ALLOWED_DIFFS = {
    "data.seed",
    "trainer.experiment_name",
    "trainer.save_checkpoint_path",
}


def _flatten(value: object, prefix: str = "") -> dict[str, object]:
    if not isinstance(value, dict):
        return {prefix: value}
    result: dict[str, object] = {}
    for key, item in value.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        result.update(_flatten(item, path))
    return result


def config_diff(left: dict, right: dict) -> set[str]:
    left_flat = _flatten(left)
    right_flat = _flatten(right)
    return {
        key
        for key in left_flat.keys() | right_flat.keys()
        if left_flat.get(key) != right_flat.get(key)
    }


def build(seed: int, output_dir: Path) -> list[Path]:
    if seed not in {2, 3}:
        raise ValueError("follow-up pilot seed must be 2 or 3")
    outputs: list[Path] = []
    for arm, base_name in ARMS.items():
        source = ROOT / "configs/train" / f"{base_name}_3b_geo3k.yaml"
        destination = output_dir / f"{base_name}_seed{seed}_3b_geo3k.yaml"
        if destination.exists():
            raise FileExistsError(f"refusing to overwrite follow-up config: {destination}")
        base = yaml.safe_load(source.read_text(encoding="utf-8"))
        derived = copy.deepcopy(base)
        derived["data"]["seed"] = seed
        derived["trainer"]["experiment_name"] = f"{base_name}_seed{seed}"
        derived["trainer"]["save_checkpoint_path"] = str(
            ROOT / "checkpoints/pilot" / f"{base_name}_seed{seed}"
        )
        differences = config_diff(base, derived)
        if differences != ALLOWED_DIFFS:
            raise RuntimeError(f"unexpected config differences for {arm}: {sorted(differences)}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(yaml.safe_dump(derived, sort_keys=False), encoding="utf-8")
        outputs.append(destination)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, choices=(2, 3), required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "configs/train")
    args = parser.parse_args()
    for path in build(args.seed, args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
