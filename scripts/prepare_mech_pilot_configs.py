#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
from pathlib import Path

import yaml


ARMS = {
    "mech_a1_real_3b_geo3k.yaml": ("real", "mech_a1_real"),
    "mech_a2_gray_3b_geo3k.yaml": ("gray", "mech_a2_gray"),
    "mech_a2b_noimage_3b_geo3k.yaml": ("none", "mech_a2b_noimage"),
}


def build_configs(source: Path, output_dir: Path) -> list[Path]:
    base = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(base, dict):
        raise ValueError("anchor config must be a mapping")
    outputs = []
    for filename, (condition, run_name) in ARMS.items():
        output = output_dir / filename
        if output.exists():
            raise FileExistsError(f"refusing to overwrite pilot config: {output}")
        config = copy.deepcopy(base)
        config["data"]["image_condition"] = condition
        config["data"]["image_condition_seed"] = 20260710
        config["worker"]["actor"]["model"]["freeze_vision_tower"] = True
        config["trainer"]["project_name"] = "blind_gains_mech_pilot"
        config["trainer"]["experiment_name"] = run_name
        config["trainer"]["max_steps"] = 100
        config["trainer"]["save_checkpoint_path"] = str(
            source.resolve().parents[2] / "checkpoints" / "pilot" / run_name
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
        outputs.append(output)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("configs/train/anchor_a0_recipe_3b_geo3k.yaml"))
    parser.add_argument("--output-dir", type=Path, default=Path("configs/train"))
    args = parser.parse_args()
    for path in build_configs(args.source, args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
