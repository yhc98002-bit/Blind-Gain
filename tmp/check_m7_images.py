#!/usr/bin/env python3
"""Which image store actually covers the M7 manifests?

M7 crashed on a missing image. The config points image_dir at a flat,
content-addressed store (28,768 files) while the manifests carry original
relative paths; every other config in the repo uses image_dir: null, i.e.
resolve from the repo root. This checks coverage both ways before changing
anything.
"""
import json
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
FLAT = ROOT / "data/virl39k_main_filtered_images"

for split in ("train", "heldout"):
    man = ROOT / f"data/virl39k_m7_{split}_v2.jsonl"
    rows = [json.loads(l) for l in man.read_text().splitlines() if l.strip()]
    imgs = []
    for r in rows:
        imgs.extend(r.get("images") or [])
    uniq = sorted(set(imgs))

    from_root = sum(1 for i in uniq if (ROOT / i).is_file())
    from_flat = sum(1 for i in uniq if (FLAT / i).is_file())
    # also test the flat store by basename, in case names are content-addressed
    flat_names = {p.name for p in FLAT.iterdir()} if FLAT.is_dir() else set()
    by_basename = sum(1 for i in uniq if Path(i).name in flat_names)

    print(f"{split}: {len(rows)} rows, {len(uniq)} unique images")
    print(f"   resolve from repo ROOT (image_dir: null) : {from_root}/{len(uniq)}"
          f"  {'ALL PRESENT' if from_root == len(uniq) else 'INCOMPLETE'}")
    print(f"   resolve under the flat store (current)   : {from_flat}/{len(uniq)}")
    print(f"   flat store match by basename             : {by_basename}/{len(uniq)}")
    print()
