#!/usr/bin/env python3
"""Generate E1b configs: trained arms on the external suite, with and without images.

E1b evaluates all four arms x 3 seeds on the pinned external benchmarks in BOTH
conditions, so the F1 access-matrix result can be checked beyond geo3k. Base rows
already exist (E1a).

Two harnesses are required and that is deliberate:
  with-image : vlmevalkit  (configs/eval/vlmevalkit_p1_2_<bench>_local_3b.json)
  blind      : eval_layer1_blind.py (configs/eval/layer1_blind_<bench>_3b.json),
               which RAISES if a vision token reaches the prompt -- the integrity
               guard that makes the blind column trustworthy.
Both are used exactly as the base rows used them, with only model_path swapped,
so trained arms and base are directly comparable.

RESOURCE ISOLATION (recorded in every generated config): E1b runs on an12 GPUs
4-7 only. M7 holds GPUs 0-3 at its registered 4-GPU width and is never touched.
"""
import json
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
OUT = ROOT / "configs/eval/e1b"
STEP = "global_step_100/actor/huggingface"

ARMS = {
    "a1_real": ["mech_a1_real_resume60", "mech_a1_real_seed2", "mech_a1_real_seed3"],
    "a2_gray": ["mech_a2_gray_resume60_retry2", "mech_a2_gray_seed2_resume20",
                "mech_a2_gray_seed3"],
    "a2b_noimage": ["mech_a2b_noimage_retry4", "mech_a2b_noimage_seed2_resume20",
                    "mech_a2b_noimage_seed3"],
    "a3_caption": ["mech_a3_caption_resume20", "mech_a3_caption_seed2",
                   "mech_a3_caption_seed3"],
}
BENCH = {
    "mmstar": {"image": "configs/eval/vlmevalkit_p1_2_mmstar_local_3b.json",
               "blind": "configs/eval/layer1_blind_mmstar_3b.json"},
    "mathvista": {"image": "configs/eval/vlmevalkit_p1_2_mathvista_local_3b.json",
                  "blind": "configs/eval/layer1_blind_mathvista_3b.json"},
}
ISOLATION = {
    "allowed_gpus": [4, 5, 6, 7],
    "forbidden_gpus": [0, 1, 2, 3],
    "reason": ("an12 GPUs 0-3 are held by M7 at its registered 4-GPU width "
               "(one synchronous RL trainer per node). E1b is inference-only and "
               "must never widen onto them."),
}

OUT.mkdir(parents=True, exist_ok=True)
written, missing = [], []

for arm, runs in ARMS.items():
    for seed_idx, run in enumerate(runs, start=1):
        ckpt = ROOT / "checkpoints/pilot" / run / STEP
        if not ckpt.is_dir():
            missing.append(f"{arm}_seed{seed_idx}: {ckpt}")
            continue
        for bench, tmpl in BENCH.items():
            # ---- with-image (vlmevalkit) ----
            base = json.loads((ROOT / tmpl["image"]).read_text())
            model_key = next(iter(base["model"]))
            new_key = f"E1b-{arm}-seed{seed_idx}"
            base["model"] = {new_key: dict(base["model"][model_key],
                                           model_path=str(ckpt))}
            base["_e1b"] = {"arm": arm, "seed": seed_idx, "benchmark": bench,
                            "condition": "image", "checkpoint": str(ckpt),
                            "template": tmpl["image"], "resource_isolation": ISOLATION}
            p = OUT / f"e1b_{arm}_seed{seed_idx}_{bench}_image.json"
            p.write_text(json.dumps(base, indent=2) + "\n")
            written.append(str(p.relative_to(ROOT)))

            # ---- blind (layer1) ----
            b = json.loads((ROOT / tmpl["blind"]).read_text())
            b["model_path"] = str(ckpt)
            b["_e1b"] = {"arm": arm, "seed": seed_idx, "benchmark": bench,
                         "condition": "blind", "checkpoint": str(ckpt),
                         "template": tmpl["blind"], "resource_isolation": ISOLATION}
            p = OUT / f"e1b_{arm}_seed{seed_idx}_{bench}_blind.json"
            p.write_text(json.dumps(b, indent=2) + "\n")
            written.append(str(p.relative_to(ROOT)))

summary = {"schema_version": 1, "n_configs": len(written),
           "expected": len(ARMS) * 3 * len(BENCH) * 2,
           "resource_isolation": ISOLATION,
           "missing_checkpoints": missing, "configs": sorted(written)}
(ROOT / "reports/e1b_config_inventory_v1.json").write_text(
    json.dumps(summary, indent=2, sort_keys=True) + "\n")

print(f"wrote {len(written)} configs (expected {summary['expected']})")
if missing:
    print("MISSING CHECKPOINTS:")
    for m in missing:
        print("  " + m)
else:
    print("all 12 checkpoints present")
print("inventory: reports/e1b_config_inventory_v1.json")
