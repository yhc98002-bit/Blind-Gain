#!/usr/bin/env python3
"""Generate the two matched C5 7B access-pair configurations (ladder rung R4).

C5 is a PURE SCALE manipulation of the registered Geometry3K access-matrix
pilot: each generated config is the corresponding seed-1 3B pilot config with
ONLY the model path (3B -> 7B), the vLLM memory fraction (a registered
mechanics deviation), the checkpoint format (model-only, a registered
mechanics deviation) and the run identity (project/experiment/checkpoint
namespace) changed.  Corpus, seed, image-condition machinery, reward, prompt
contract, optimizer, batch geometry, KL, rollout sampling, step budget,
validation cadence and checkpoint cadence are inherited byte-identically, so
the 7B pair stays matched to the 3B pilot recipe and the two 7B arms stay
matched to each other.

Registered by docs/registered_c5_7b_access_pair_v1.md, which amends
Extension 4 of docs/registered_extensions_v1.md down to two arms x one seed
on the Geometry3K pilot recipe (A2-gray retained by the fired precommitted M8
fork rule; the four-arm x three-seed ViRL39K flagship is DEFERRED, not
discharged).

The 7B model directory carries NO upstream revision marker, so this script
pins model identity by computed on-disk hashes: the SHA256 of
model.safetensors.index.json, config.json and every auxiliary file, plus
per-shard byte sizes and full per-shard SHA256s.  Equality with the upstream
revision named in Extension 4's M8 audit row is NOT asserted anywhere.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")

# Parity baseline: the registered seed-1 Geometry3K pilot configs, NOT the
# m7_virl configs.  docs/EXPERIMENT_TODO.md row C5: "the headline matrix
# replicates" -- the headline matrix is the geo3k access matrix.
ARMS = {
    "a1_real": ("mech_a1_real_3b_geo3k.yaml", "real"),
    "a2_gray": ("mech_a2_gray_3b_geo3k.yaml", "gray"),
}
SEED = 1  # one seed only, per the PI decision recorded in the registration
PROJECT_NAME = "blind_gains_c5_7b"
MODEL_DIR = ROOT / "artifacts/models/Qwen/Qwen2.5-VL-7B-Instruct"
MODEL_PATH_7B = str(MODEL_DIR)

# Registered mechanics deviation 1: worker.rollout.gpu_memory_utilization
# 0.6 -> 0.45.  Measured 3B peak is 63.58 GB of 79.33 (transient FSDP
# all-gather while vLLM holds its reservation; live arms show ~68 GB).  7B at
# the inherited 0.6 projects to 75-78 GB, which is not safe; 0.45 projects to
# ~65 GB.  Serving memory reservation only -- no estimand is touched.
GPU_MEMORY_UTILIZATION = 0.45

# Registered mechanics deviation 2: trainer.save_model_only true for BOTH
# arms.  No registered C5 estimand reads intermediate optimizer state;
# save_freq stays 20 so the registered checkpoint CADENCE is unchanged and
# only the on-disk format differs (~85 GB/arm of HF weights instead of ~600 GB
# of full FSDP state).  Cost: neither arm can be resumed mid-run.  Symmetric
# across arms, so arm-to-arm matching is preserved.
SAVE_MODEL_ONLY = True

TRAIN_FILE = "data/geo3k_pilot_filtered.jsonl"
FILTERED_IDS = "data/geo3k_pilot_filtered_ids.json"
REWARD_FILE = "src/rewards/pilot_reward.py"
FORMAT_PROMPT = "artifacts/repos/EasyR1/examples/format_prompt/r1v.jinja"

MODEL_AUX_FILES = (
    "config.json",
    "generation_config.json",
    "model.safetensors.index.json",
    "preprocessor_config.json",
    "tokenizer_config.json",
    "tokenizer.json",
    "vocab.json",
    "merges.txt",
    "chat_template.json",
)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 22), b""):
            digest.update(chunk)
    return digest.hexdigest()


def model_identity(model_dir: Path) -> dict:
    index_path = model_dir / "model.safetensors.index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    shard_names = sorted(set(index["weight_map"].values()))
    if not shard_names:
        raise ValueError("model index names no shards")
    shards = []
    for name in shard_names:
        shard_path = model_dir / name
        shards.append(
            {
                "file": name,
                "bytes": shard_path.stat().st_size,
                "sha256": _sha256_file(shard_path),
            }
        )
    aux = {}
    for name in MODEL_AUX_FILES:
        aux_path = model_dir / name
        if not aux_path.is_file():
            raise FileNotFoundError(f"expected model file missing: {aux_path}")
        aux[name] = _sha256_file(aux_path)
    return {
        "path": str(model_dir.relative_to(ROOT)),
        "on_disk_revision_marker": None,
        "index_total_size": int(index["metadata"]["total_size"]),
        "index_sha256": aux["model.safetensors.index.json"],
        "config_sha256": aux["config.json"],
        "shards": shards,
        "aux_file_sha256": aux,
        "note": (
            "The model directory carries no upstream revision marker, so identity "
            "is pinned by these computed on-disk hashes. Equality with "
            "Qwen/Qwen2.5-VL-7B-Instruct@cc594898137f460bfe9f0759e9844b3ce807cfb5 "
            "(the M8 audit revision named in Extension 4) is NOT asserted."
        ),
    }


def main() -> None:
    model = model_identity(MODEL_DIR)

    templates = {}
    for arm, (template_name, condition) in ARMS.items():
        template_path = ROOT / "configs/train" / template_name
        template_text = template_path.read_text(encoding="utf-8")
        template = yaml.safe_load(template_text)
        if template["data"].get("image_condition") != condition:
            raise ValueError(
                f"template condition mismatch for {arm}: "
                f"{template['data'].get('image_condition')}"
            )
        if template["data"].get("seed") != SEED:
            raise ValueError(f"template {template_name} carries data.seed != {SEED}")
        templates[arm] = {
            "name": template_name,
            "sha256": _sha256_text(template_text),
            "config": template,
        }

    written = []
    for arm, (template_name, condition) in ARMS.items():
        config = yaml.safe_load(
            (ROOT / "configs/train" / template_name).read_text(encoding="utf-8")
        )
        label = f"c5_{arm}_seed{SEED}_7b"
        config["worker"]["actor"]["model"]["model_path"] = MODEL_PATH_7B
        config["worker"]["rollout"]["gpu_memory_utilization"] = GPU_MEMORY_UTILIZATION
        trainer = config["trainer"]
        trainer["project_name"] = PROJECT_NAME
        trainer["experiment_name"] = label
        trainer["save_checkpoint_path"] = str(ROOT / "checkpoints/c5" / label)
        trainer["load_checkpoint_path"] = None
        # Assigning to keys the template already carries leaves dict insertion
        # order untouched, so the emitted bytes diff against the pilot config
        # is exactly the declared deviation set.
        trainer["save_model_only"] = SAVE_MODEL_ONLY
        out_path = ROOT / "configs/train" / f"{label}.yaml"
        if out_path.exists():
            raise FileExistsError(f"refusing to overwrite {out_path}")
        text = yaml.safe_dump(config, sort_keys=False)
        out_path.write_text(text, encoding="utf-8")
        written.append(
            {
                "arm": arm,
                "seed": SEED,
                "condition": condition,
                "config": str(out_path.relative_to(ROOT)),
                "config_sha256": _sha256_text(text),
                "template": template_name,
                "template_sha256": templates[arm]["sha256"],
                "model_path": MODEL_PATH_7B,
                "gpu_memory_utilization": GPU_MEMORY_UTILIZATION,
                "max_steps": trainer["max_steps"],
                "n_gpus_per_node": trainer["n_gpus_per_node"],
                "save_freq": trainer["save_freq"],
                "save_model_only": trainer["save_model_only"],
                "tensor_parallel_size": config["worker"]["rollout"]["tensor_parallel_size"],
            }
        )

    # ------------------------------------------------------------------
    # Parity assertions, the way scripts/build_m7_configs.py does them.
    # ------------------------------------------------------------------
    hyper_keys = ("algorithm", "worker")
    SANCTIONED_DEVIATIONS = (
        # The registered scale manipulation itself: 3B -> 7B.  Stripped before
        # the matched-recipe comparison and re-checked explicitly below.
        ("worker", "actor", "model", "model_path"),
        # Mechanics deviation 1: vLLM memory fraction 0.6 -> 0.45 (OOM
        # headroom at 7B).  Identical in both arms, so arm-to-arm parity is
        # preserved.  Stripped before comparison, re-checked below.
        ("worker", "rollout", "gpu_memory_utilization"),
        # Mechanics deviation 2: model-only checkpoints, BOTH arms.  In the
        # `trainer` block, which is outside hyper_keys and already varies by
        # arm; this entry is the machine-readable RECORD emitted into the
        # inventory, not a strip directive.  Cadence parity (`save_freq`) is
        # asserted separately below.
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

    baseline = templates["a1_real"]["config"]

    # The two 3B pilot templates must themselves agree in algorithm/worker, or
    # "the pilot recipe" would be ambiguous as a parity baseline.
    for key in hyper_keys:
        a1 = json.dumps(templates["a1_real"]["config"][key], sort_keys=True)
        a2 = json.dumps(templates["a2_gray"]["config"][key], sort_keys=True)
        if a1 != a2:
            raise AssertionError(f"3B pilot templates disagree in {key}; no unambiguous recipe")

    generated = {
        record["arm"]: yaml.safe_load((ROOT / record["config"]).read_text(encoding="utf-8"))
        for record in written
    }

    for record in written:
        arm = record["arm"]
        config = generated[arm]
        # 1. Matched recipe: algorithm/worker byte-identical to the 3B pilot
        #    except the sanctioned deviations.
        for key in hyper_keys:
            got = json.dumps(_strip_sanctioned(config[key], key), sort_keys=True)
            want = json.dumps(_strip_sanctioned(baseline[key], key), sort_keys=True)
            if got != want:
                raise AssertionError(f"arm {arm} deviates from the pilot recipe in {key}")
        # 2. Data block: inherited byte-identically from the arm's own
        #    template -- corpus, seed, image condition, condition seed,
        #    caption store paths, prompt lengths, everything.
        got = json.dumps(config["data"], sort_keys=True)
        want = json.dumps(templates[arm]["config"]["data"], sort_keys=True)
        if got != want:
            raise AssertionError(f"arm {arm} data block deviates from its pilot template")
        # 3. The sanctioned values themselves.
        if config["worker"]["actor"]["model"]["model_path"] != MODEL_PATH_7B:
            raise AssertionError(f"arm {arm} model_path is not the pinned 7B path")
        if config["worker"]["rollout"]["gpu_memory_utilization"] != GPU_MEMORY_UTILIZATION:
            raise AssertionError(
                f"arm {arm} gpu_memory_utilization "
                f"{config['worker']['rollout']['gpu_memory_utilization']}, "
                f"expected {GPU_MEMORY_UTILIZATION}"
            )
        if config["trainer"]["save_model_only"] is not True:
            raise AssertionError(f"arm {arm} must run save_model_only: true")
        # 4. Registered invariants inherited unchanged.
        if config["trainer"]["save_freq"] != baseline["trainer"]["save_freq"]:
            raise AssertionError(f"arm {arm} save_freq deviates from the pilot cadence")
        if config["trainer"]["max_steps"] != baseline["trainer"]["max_steps"]:
            raise AssertionError(f"arm {arm} max_steps deviates from the pilot budget")
        if config["trainer"]["n_gpus_per_node"] != baseline["trainer"]["n_gpus_per_node"]:
            raise AssertionError(f"arm {arm} n_gpus_per_node deviates from the pilot width")
        if config["worker"]["rollout"]["tensor_parallel_size"] != 1:
            raise AssertionError(
                f"arm {arm} violates TP1 (pi-2026-07-11; "
                "docs/registered_extensions_v1.md Global Contract)"
            )
        # 5. Trainer diffs against the arm's own template are confined to the
        #    identity fields plus the sanctioned checkpoint format.
        ALLOWED_TRAINER_DIFFS = {
            "project_name",
            "experiment_name",
            "save_checkpoint_path",
            "save_model_only",
        }
        t_template = templates[arm]["config"]["trainer"]
        t_config = config["trainer"]
        drifted = {
            k for k in set(t_template) | set(t_config) if t_template.get(k) != t_config.get(k)
        } - ALLOWED_TRAINER_DIFFS
        if drifted:
            raise AssertionError(
                f"arm {arm} differs from its template in unsanctioned trainer "
                f"fields: {sorted(drifted)}"
            )

    # 6. Arm-to-arm parity: the two generated configs may differ ONLY in the
    #    image condition and the run identity.
    a1_cfg, a2_cfg = generated["a1_real"], generated["a2_gray"]
    for key in hyper_keys:
        if json.dumps(a1_cfg[key], sort_keys=True) != json.dumps(a2_cfg[key], sort_keys=True):
            raise AssertionError(f"C5 arms differ in {key}; the pair is not matched")
    data_diff = {
        k
        for k in set(a1_cfg["data"]) | set(a2_cfg["data"])
        if a1_cfg["data"].get(k) != a2_cfg["data"].get(k)
    }
    if data_diff != {"image_condition"}:
        raise AssertionError(f"C5 arms differ in data fields {sorted(data_diff)}; expected only image_condition")
    trainer_diff = {
        k
        for k in set(a1_cfg["trainer"]) | set(a2_cfg["trainer"])
        if a1_cfg["trainer"].get(k) != a2_cfg["trainer"].get(k)
    }
    if trainer_diff != {"experiment_name", "save_checkpoint_path"}:
        raise AssertionError(
            f"C5 arms differ in trainer fields {sorted(trainer_diff)}; "
            "expected only experiment_name and save_checkpoint_path"
        )

    manifest = {
        "schema_version": "blind-gains.c5-arm-configs.v1",
        "registration": (
            "docs/registered_c5_7b_access_pair_v1.md "
            "(amends docs/registered_extensions_v1.md Extension 4)"
        ),
        "recipe_provenance": {
            arm: {"template": templates[arm]["name"], "template_sha256": templates[arm]["sha256"]}
            for arm in ARMS
        },
        "train_file": TRAIN_FILE,
        "train_sha256": _sha256_file(ROOT / TRAIN_FILE),
        "filtered_ids": FILTERED_IDS,
        "filtered_ids_sha256": _sha256_file(ROOT / FILTERED_IDS),
        "reward_function": REWARD_FILE,
        "reward_sha256": _sha256_file(ROOT / REWARD_FILE),
        "format_prompt": FORMAT_PROMPT,
        "format_prompt_sha256": _sha256_file(ROOT / FORMAT_PROMPT),
        "model": model,
        "configs": written,
        "matched_recipe_check": (
            "algorithm and worker blocks byte-identical to the seed-1 3B geo3k "
            "pilot configs except worker.actor.model.model_path (the registered "
            "scale manipulation) and worker.rollout.gpu_memory_utilization (a "
            "registered mechanics deviation); data blocks inherited unchanged; "
            "the two C5 arms differ only in data.image_condition and run identity"
        ),
        "sanctioned_deviations": [".".join(path) for path in SANCTIONED_DEVIATIONS],
        "tensor_parallel_policy": (
            "TP1 per the PI GPU Placement Addendum pi-2026-07-11 "
            "(docs/PRELAUNCH_BRIEF.md) and the Global Contract of "
            "docs/registered_extensions_v1.md ('Models at or below 7B use TP1; "
            "throughput comes from independent replicas'). The upstream EasyR1 "
            "default is TP2, so the explicit tensor_parallel_size: 1 override "
            "is retained in both configs."
        ),
        "execution_scope": {
            "arms": sorted(ARMS),
            "seed": SEED,
            "note": (
                "Two arms x one seed per the PI decision registered in "
                "docs/registered_c5_7b_access_pair_v1.md. A2-gray is retained by "
                "the FIRED precommitted M8 fork rule quoted there from Extension 4 "
                "(gray 0.2456 vs no-image 0.1824, non-overlapping 95% intervals); "
                "A2b and A3 are NOT run at 7B, and Extension 4's four-arm x "
                "three-seed ViRL39K flagship is deferred, not discharged."
            ),
        },
        "checkpoint_policy": {
            "save_freq": baseline["trainer"]["save_freq"],
            "cadence_matched_across_arms": True,
            "save_model_only_arms": sorted(ARMS),
            "note": (
                "Both arms write model-only checkpoints (~17 GB of HF weights per "
                "save, ~85 GB/arm) instead of full FSDP state (~600 GB/arm). "
                "save_freq is unchanged, so the registered matched checkpoint "
                "cadence holds; only the on-disk format differs. Neither arm can "
                "be resumed mid-run. Symmetric across both arms, so no arm-to-arm "
                "asymmetry is introduced."
            ),
        },
    }
    out = ROOT / "reports/c5_arm_configs_v1.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"configs": len(written), "manifest": str(out.relative_to(ROOT))}))
    for record in written:
        print(
            f"{record['config']}  {record['config_sha256'][:16]}  "
            f"steps={record['max_steps']}  gpus={record['n_gpus_per_node']}  "
            f"gpu_mem_util={record['gpu_memory_utilization']}  "
            f"save_freq={record['save_freq']}  save_model_only={record['save_model_only']}  "
            f"tp={record['tensor_parallel_size']}"
        )


if __name__ == "__main__":
    main()
