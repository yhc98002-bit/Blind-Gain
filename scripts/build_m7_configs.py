#!/usr/bin/env python3
"""Generate the eight matched M7 ViRL39K 3B arm configurations.

Each config is the corresponding registered Geometry3K seed-3 pilot config with
ONLY the corpus, the image source, the caption store, the seed, and the
checkpoint/experiment identity changed. Every optimization hyperparameter,
batch size, rollout setting, KL setting, and step budget is inherited
unchanged, so the four arms remain matched to each other and the M7 recipe
remains matched to the pilot.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
ARMS = {
    "a1_real": ("mech_a1_real_seed3_3b_geo3k.yaml", "real"),
    "a2_gray": ("mech_a2_gray_seed3_3b_geo3k.yaml", "gray"),
    "a2b_noimage": ("mech_a2b_noimage_seed3_3b_geo3k.yaml", "none"),
    "a3_caption": ("mech_a3_caption_seed3_3b_geo3k.yaml", "caption"),
}
SEEDS = (1, 2)
TRAIN_FILE = "data/virl39k_m7_train_v3.jsonl"
VAL_FILE = "data/virl39k_m7_heldout_v3.jsonl"
# The M7 manifests carry repo-root-relative image paths
# ("data/virl39k/images/..."), so image_dir must be null exactly as it is
# for every other config in this repo. The flat
# virl39k_main_filtered_images store is content-addressed and resolves
# none of them (measured 0/25712 train, 0/4524 heldout).
IMAGE_DIR = None

# The M7 corpus is restricted to single-image rows per
# docs/registered_m7_single_image_v2.md, so one image per prompt is both
# sufficient and identical to the Geometry3K pilot recipe. Raising this to
# cover multi-image rows made vLLM's worst-case multimodal profiling kill a
# worker during init.
LIMIT_IMAGES = 1
CAPTION_STORE = str(ROOT / "data/virl39k_caption_store_3b_main_v2.jsonl")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> None:
    written = []
    for arm, (template_name, condition) in ARMS.items():
        template_path = ROOT / "configs/train" / template_name
        template = yaml.safe_load(template_path.read_text(encoding="utf-8"))
        if template["data"].get("image_condition") != condition:
            raise ValueError(f"template condition mismatch for {arm}: {template['data'].get('image_condition')}")
        for seed in SEEDS:
            config = yaml.safe_load(template_path.read_text(encoding="utf-8"))
            data = config["data"]
            data["train_files"] = TRAIN_FILE
            data["val_files"] = VAL_FILE
            data["image_dir"] = IMAGE_DIR
            # ViRL39K carries up to 8 images per prompt (geo3k is
            # single-image). EasyR1 only forwards limit_mm_per_prompt when
            # limit_images is truthy, so 0 leaves vLLM at its default of 1
            # and any multi-image row aborts the rollout.
            config["worker"]["rollout"]["limit_images"] = LIMIT_IMAGES
            data["seed"] = seed
            if condition == "caption":
                data["caption_store_paths"] = [CAPTION_STORE]
            else:
                data.pop("caption_store_paths", None)
            label = f"m7_virl_{arm}_seed{seed}"
            trainer = config["trainer"]
            trainer["project_name"] = "blind_gains_m7_virl"
            trainer["experiment_name"] = label
            trainer["save_checkpoint_path"] = str(ROOT / "checkpoints/m7" / label)
            trainer["load_checkpoint_path"] = None
            out_path = ROOT / "configs/train" / f"{label}_3b.yaml"
            if out_path.exists():
                raise FileExistsError(f"refusing to overwrite {out_path}")
            text = yaml.safe_dump(config, sort_keys=False)
            out_path.write_text(text, encoding="utf-8")
            written.append(
                {
                    "arm": arm,
                    "seed": seed,
                    "condition": condition,
                    "config": str(out_path.relative_to(ROOT)),
                    "config_sha256": _sha256_text(text),
                    "template": template_name,
                    "max_steps": trainer["max_steps"],
                    "n_gpus_per_node": trainer["n_gpus_per_node"],
                }
            )

    hyper_keys = ("algorithm", "worker")
    # ViRL39K carries up to 8 images per prompt; geo3k is single-image and uses 0.
    # This is the ONLY sanctioned deviation from the matched geo3k recipe, and all
    # eight arms receive the identical value, so arm-to-arm parity is preserved.
    SANCTIONED_DEVIATIONS = (("worker", "rollout", "limit_images"),)

    def _strip_sanctioned(blob, top):
        import copy as _copy
        out = _copy.deepcopy(blob)
        for path in SANCTIONED_DEVIATIONS:
            if path[0] != top:
                continue
            node = out
            for part in path[1:-1]:
                node = node.get(part) if isinstance(node, dict) else None
                if node is None:
                    break
            if isinstance(node, dict):
                node.pop(path[-1], None)
        return out

    baseline = yaml.safe_load((ROOT / "configs/train" / ARMS["a1_real"][0]).read_text(encoding="utf-8"))
    for record in written:
        config = yaml.safe_load((ROOT / record["config"]).read_text(encoding="utf-8"))
        for key in hyper_keys:
            got = json.dumps(_strip_sanctioned(config[key], key), sort_keys=True)
            want = json.dumps(_strip_sanctioned(baseline[key], key), sort_keys=True)
            if got != want:
                raise AssertionError(f"arm {record['arm']} deviates from the matched recipe in {key}")
        # arm-to-arm parity on the sanctioned key itself
        if config["worker"]["rollout"]["limit_images"] != LIMIT_IMAGES:
            raise AssertionError(f"arm {record['arm']} has limit_images "
                                 f"{config['worker']['rollout']['limit_images']}, expected {LIMIT_IMAGES}")
        if config["data"]["train_files"] != TRAIN_FILE or config["data"]["val_files"] != VAL_FILE:
            raise AssertionError("corpus pinning failed")

    manifest = {
        "schema_version": "blind-gains.m7-arm-configs.v1",
        "registration": "docs/registered_m7_amendment_v1.md + docs/registered_m7_heldout_split_v2.md",
        "train_file": TRAIN_FILE,
        "val_file": VAL_FILE,
        "caption_store": str(Path(CAPTION_STORE).relative_to(ROOT)),
        "configs": written,
        "matched_recipe_check": "algorithm and worker blocks byte-identical across all eight configs",
    }
    out = ROOT / "reports/m7_arm_configs_v1.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"configs": len(written), "manifest": str(out.relative_to(ROOT))}))
    for record in written:
        print(f"{record['config']}  {record['config_sha256'][:16]}  steps={record['max_steps']}")


if __name__ == "__main__":
    main()
