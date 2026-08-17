#!/usr/bin/env python3
"""Point the M7 configs at the store that actually holds their images.

M7 arm 1 crashed with FileNotFoundError on
  data/virl39k_main_filtered_images/data/virl39k/images/Processed-....jpg
i.e. image_dir joined to a manifest path that is already repo-root relative.

Measured coverage of the M7 manifests:
  from repo root (image_dir: null) : 25712/25712 train, 4524/4524 heldout
  under the flat store (current)   : 0/25712, 0/4524 (also 0 by basename)

The flat `virl39k_main_filtered_images` store is content-addressed and holds a
different 28,768-file subset; it never resolved these manifests. Every other
config in the repo uses `image_dir: null`. This aligns M7 with that convention.

Scientific scope: none. No item, split, seed, reward or estimand changes; the
images resolved are the same ones the manifests always named. This only makes
the registered design runnable.
"""
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
p = ROOT / "scripts/build_m7_configs.py"
t = p.read_text()

old_const = 'IMAGE_DIR = str(ROOT / "data/virl39k_main_filtered_images")'
new_const = ('# The M7 manifests carry repo-root-relative image paths\n'
             '# ("data/virl39k/images/..."), so image_dir must be null exactly as it is\n'
             '# for every other config in this repo. The flat\n'
             '# virl39k_main_filtered_images store is content-addressed and resolves\n'
             '# none of them (measured 0/25712 train, 0/4524 heldout).\n'
             'IMAGE_DIR = None')

if 'IMAGE_DIR = None' in t:
    print("already patched")
else:
    assert t.count(old_const) == 1, f"const anchor {t.count(old_const)}"
    t = t.replace(old_const, new_const, 1)
    p.write_text(t)
    print("patched scripts/build_m7_configs.py: IMAGE_DIR = None")
