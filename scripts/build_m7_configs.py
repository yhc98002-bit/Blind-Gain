#!/usr/bin/env python3
"""Generate the eight matched M7 ViRL39K 3B arm configurations.

Each config is the corresponding registered Geometry3K seed-3 pilot config with
ONLY the corpus, the image source, the caption store, the seed, and the
checkpoint/experiment identity changed. Every optimization hyperparameter,
batch size, rollout setting, KL setting, and step budget is inherited
unchanged, so the four arms remain matched to each other and the M7 recipe
remains matched to the pilot.

Amended by docs/registered_m7_seed_scope_v1.md: seed 1 only is in execution
scope for all four arms (seed 2 configs stay generated but deferred), and arms
2-4 write model-only checkpoints at the unchanged save_freq of 20. Both
deviations are recorded in SANCTIONED_DEVIATIONS below and emitted into
reports/m7_arm_configs_v1.json.
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
# docs/registered_m7_seed_scope_v1.md 1(a): seed 1 only is in EXECUTION scope
# for all four arms, and every estimand is reported per-seed rather than as the
# registered two-seed mean. Seed 2 is deferred, not abandoned, so its configs
# are still generated and still registered in the manifest -- that is what
# keeps the launcher's `SEED in {1,2}` guard and its manifest-hash gate usable
# later without a further amendment. Generating a config does not run it.
EXECUTION_SEEDS = (1,)
# docs/registered_m7_seed_scope_v1.md 1(b): arms 2-4 write model-only
# checkpoints (7.6 GB of HF weights) instead of full FSDP checkpoints (38.5 GB
# including optimizer shards). `save_freq` stays 20 for every arm, so the
# registered matched checkpoint CADENCE is unchanged and only the on-disk
# FORMAT differs. Arm 1 is already running and is deliberately left at false;
# it is not restarted or altered.
SAVE_MODEL_ONLY_ARMS = ("a2_gray", "a2b_noimage", "a3_caption")
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
            # Arm-scoped, not seed-scoped: the registered deviation is a
            # property of arms 2-4. Assigning to a key the template already
            # carries leaves dict insertion order untouched, so arm 1's
            # emitted bytes are unchanged.
            trainer["save_model_only"] = arm in SAVE_MODEL_ONLY_ARMS
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
                    "save_freq": trainer["save_freq"],
                    "save_model_only": trainer["save_model_only"],
                    "in_execution_scope": seed in EXECUTION_SEEDS,
                }
            )

    hyper_keys = ("algorithm", "worker")
    SANCTIONED_DEVIATIONS = (
        # ViRL39K carries up to 8 images per prompt; geo3k is single-image and
        # uses 0. All eight configs receive the identical value, so arm-to-arm
        # parity is preserved. Inside hyper_keys, so it is stripped before the
        # matched-recipe comparison and re-checked explicitly below.
        ("worker", "rollout", "limit_images"),
        # docs/registered_m7_seed_scope_v1.md 1(b): arms 2-4 write model-only
        # checkpoints; arm 1 does not. This path is in the `trainer` block,
        # which is deliberately outside hyper_keys and already varies by arm,
        # so _strip_sanctioned never reaches it -- the entry is a machine-
        # readable RECORD of the sanctioned deviation, emitted into the
        # manifest, not a strip directive. Cadence parity (`save_freq`) is
        # asserted separately below, because cadence is what Extension 3
        # registers as matched.
        ("trainer", "save_model_only"),
    )

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
        # Extension 3 registers matched checkpoint CADENCE, and the seed-scope
        # amendment leaves it unchanged: save_freq must equal the pilot
        # template's value in every arm, seed 1 and seed 2 alike.
        if config["trainer"]["save_freq"] != baseline["trainer"]["save_freq"]:
            raise AssertionError(
                f"arm {record['arm']} seed {record['seed']} has save_freq "
                f"{config['trainer']['save_freq']}, expected {baseline['trainer']['save_freq']}"
            )
        # Only the on-disk FORMAT is allowed to differ, and only for arms 2-4.
        expected_model_only = record["arm"] in SAVE_MODEL_ONLY_ARMS
        if config["trainer"]["save_model_only"] != expected_model_only:
            raise AssertionError(
                f"arm {record['arm']} seed {record['seed']} has save_model_only "
                f"{config['trainer']['save_model_only']}, expected {expected_model_only}"
            )
    # docs/registered_m7_seed_scope_v1.md 3: the diff against arm 1 must be
    # confined to these trainer fields. Compared arm-1-vs-arm-N at equal seed,
    # which is the contrast the registration names.
    ALLOWED_TRAINER_DIFFS = {
        "project_name",
        "experiment_name",
        "save_checkpoint_path",
        "load_checkpoint_path",
        "save_model_only",
    }
    for record in written:
        if record["arm"] == "a1_real":
            continue
        arm1 = yaml.safe_load(
            (ROOT / f"configs/train/m7_virl_a1_real_seed{record['seed']}_3b.yaml").read_text(encoding="utf-8")
        )["trainer"]
        other = yaml.safe_load((ROOT / record["config"]).read_text(encoding="utf-8"))["trainer"]
        drifted = {
            k for k in set(arm1) | set(other) if arm1.get(k) != other.get(k)
        } - ALLOWED_TRAINER_DIFFS
        if drifted:
            raise AssertionError(
                f"arm {record['arm']} seed {record['seed']} differs from arm 1 in "
                f"unsanctioned trainer fields: {sorted(drifted)}"
            )

    manifest = {
        "schema_version": "blind-gains.m7-arm-configs.v1",
        "registration": (
            "docs/registered_m7_amendment_v1.md + docs/registered_m7_heldout_split_v2.md"
            " + docs/registered_m7_seed_scope_v1.md"
        ),
        "train_file": TRAIN_FILE,
        "val_file": VAL_FILE,
        "caption_store": str(Path(CAPTION_STORE).relative_to(ROOT)),
        "configs": written,
        "matched_recipe_check": "algorithm and worker blocks byte-identical across all eight configs",
        "sanctioned_deviations": [".".join(path) for path in SANCTIONED_DEVIATIONS],
        "execution_scope": {
            "seeds": list(EXECUTION_SEEDS),
            "note": (
                "docs/registered_m7_seed_scope_v1.md 1(a): seed 1 only is executed, for all "
                "four arms; every estimand is reported per-seed, not as the registered "
                "two-seed mean, and every M7 readout carries the scope tag 'one seed'. "
                "Seed 2 configs are generated and registered but deferred, not abandoned."
            ),
        },
        "checkpoint_policy": {
            "save_freq": baseline["trainer"]["save_freq"],
            "cadence_matched_across_arms": True,
            "save_model_only_arms": list(SAVE_MODEL_ONLY_ARMS),
            "note": (
                "docs/registered_m7_seed_scope_v1.md 1(b): arms 2-4 write model-only "
                "checkpoints. save_freq is unchanged, so the registered matched checkpoint "
                "cadence holds; only the on-disk format differs. Arms 2-4 therefore cannot "
                "be resumed mid-run. Arm 1 is unchanged at save_model_only: false."
            ),
        },
        "trainer_fields_allowed_to_differ_from_arm1": sorted(ALLOWED_TRAINER_DIFFS),
    }
    out = ROOT / "reports/m7_arm_configs_v1.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"configs": len(written), "manifest": str(out.relative_to(ROOT))}))
    for record in written:
        print(
            f"{record['config']}  {record['config_sha256'][:16]}  "
            f"steps={record['max_steps']}  gpus={record['n_gpus_per_node']}  "
            f"save_freq={record['save_freq']}  save_model_only={record['save_model_only']}  "
            f"exec_scope={record['in_execution_scope']}"
        )


if __name__ == "__main__":
    main()
