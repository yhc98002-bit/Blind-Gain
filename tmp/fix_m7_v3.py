#!/usr/bin/env python3
"""Point the M7 configs at the single-image v3 splits with limit_images: 1.

Per docs/registered_m7_single_image_v2.md. With every row single-image the
recipe returns to byte-parity with the Geometry3K pilot, which is the property
R3 depends on.
"""
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
p = ROOT / "scripts/build_m7_configs.py"
t = p.read_text()

# limit_images 8 -> 1 (single-image corpus; parity with the pilot recipe)
old_c = ("# max images per prompt across the registered M7 splits (train 8, heldout 7)\n"
         "LIMIT_IMAGES = 8")
new_c = ("# The M7 corpus is restricted to single-image rows per\n"
         "# docs/registered_m7_single_image_v2.md, so one image per prompt is both\n"
         "# sufficient and identical to the Geometry3K pilot recipe. Raising this to\n"
         "# cover multi-image rows made vLLM's worst-case multimodal profiling kill a\n"
         "# worker during init.\n"
         "LIMIT_IMAGES = 1")
assert t.count(old_c) == 1, f"limit const {t.count(old_c)}"
t = t.replace(old_c, new_c, 1)

old_g = 'if config["worker"]["rollout"]["limit_images"] != 8:'
new_g = 'if config["worker"]["rollout"]["limit_images"] != LIMIT_IMAGES:'
assert t.count(old_g) == 1, "guard literal"
t = t.replace(old_g, new_g, 1)
t = t.replace('f"{config[\'worker\'][\'rollout\'][\'limit_images\']}, expected 8")',
              'f"{config[\'worker\'][\'rollout\'][\'limit_images\']}, expected {LIMIT_IMAGES}")')

# v2 -> v3 split files
n = t.count("virl39k_m7_train_v2.jsonl") + t.count("virl39k_m7_heldout_v2.jsonl")
t = t.replace("virl39k_m7_train_v2.jsonl", "virl39k_m7_train_v3.jsonl")
t = t.replace("virl39k_m7_heldout_v2.jsonl", "virl39k_m7_heldout_v3.jsonl")
print(f"split references updated: {n}")

p.write_text(t)
print("patched build_m7_configs.py -> v3 splits, limit_images 1")
