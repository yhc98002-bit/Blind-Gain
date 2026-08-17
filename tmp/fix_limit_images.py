#!/usr/bin/env python3
"""Set limit_images for the multi-image ViRL39K corpus.

M7 crashed at the first rollout with:
  ValueError: You set image=1 (or defaulted to 1) in `--limit-mm-per-prompt`,
  but passed 4 image items in the same prompt.

EasyR1 only forwards the limit when it is truthy:
  verl/workers/rollout/vllm_rollout_spmd.py:122
      if config.limit_images:
          engine_kwargs["limit_mm_per_prompt"] = {"image": config.limit_images}
so limit_images: 0 leaves vLLM at its default of one image per prompt.

Geometry3K is single-image, so the pilot recipe M7 inherited never needed this.
ViRL39K is not: measured over the registered M7 splits,

  train   1 img 23542 | 2 img 984 | 3 img 307 | 4 img 279 | 5 img 133
          6 img 6 | 7 img 2 | 8 img 2      -> max 8
  heldout 1 img 4239 | 2 img 152 | 3 img 40 | 4 img 44 | 5 img 25 | 7 img 1
          -> max 7

Set to 8 so every registered row is servable. Capping lower would silently
require dropping rows from a registered split, which is not a config change.

Note for future audits: a config-diff against the geo3k launchers cannot find
this class of defect -- limit_images is 0 in both. It is a property of the
corpus, not a divergence from the reference.
"""
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
p = ROOT / "scripts/build_m7_configs.py"
t = p.read_text()

if 'LIMIT_IMAGES' in t:
    print("already patched")
    raise SystemExit(0)

# the builder copies a geo3k template; force the rollout limit after that copy
anchor = '            data["image_dir"] = IMAGE_DIR'
assert t.count(anchor) == 1, f"anchor count {t.count(anchor)}"
new = (anchor + "\n"
       "            # ViRL39K carries up to 8 images per prompt (geo3k is\n"
       "            # single-image). EasyR1 only forwards limit_mm_per_prompt when\n"
       "            # limit_images is truthy, so 0 leaves vLLM at its default of 1\n"
       "            # and any multi-image row aborts the rollout.\n"
       "            config[\"worker\"][\"rollout\"][\"limit_images\"] = LIMIT_IMAGES")
t = t.replace(anchor, new, 1)

# define the constant next to IMAGE_DIR
c_anchor = "IMAGE_DIR = None"
assert t.count(c_anchor) == 1, "IMAGE_DIR anchor"
t = t.replace(c_anchor, c_anchor + "\n\n# max images per prompt across the registered M7 splits (train 8, heldout 7)\nLIMIT_IMAGES = 8", 1)

p.write_text(t)
print("patched scripts/build_m7_configs.py: LIMIT_IMAGES = 8")
