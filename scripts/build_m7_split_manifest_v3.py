#!/usr/bin/env python3
"""Build the v3 split manifest and re-verify image disjointness.

The launcher gate requires train/heldout sha256 plus
image_integrity.shared_images == 0. Disjointness is I6 -- train/eval separation
enforced at the image level -- and is re-measured here rather than inherited from
v2, because filtering rows could in principle change which images appear on each
side.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")


def load(p):
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


train_p = ROOT / "data/virl39k_m7_train_v3.jsonl"
held_p = ROOT / "data/virl39k_m7_heldout_v3.jsonl"
train, held = load(train_p), load(held_p)

t_imgs = {i for r in train for i in (r.get("images") or [])}
h_imgs = {i for r in held for i in (r.get("images") or [])}
shared = sorted(t_imgs & h_imgs)

t_prog = {(r.get("metadata") or {}).get("scene_program_id") or r.get("qid") for r in train}
h_prog = {(r.get("metadata") or {}).get("scene_program_id") or r.get("qid") for r in held}
shared_qid = sorted(x for x in (t_prog & h_prog) if x is not None)

v2 = json.loads((ROOT / "data/virl39k_m7_split_manifest_v2.json").read_text())

man = {
    "schema_version": v2.get("schema_version", 1),
    "supersedes": "data/virl39k_m7_split_manifest_v2.json",
    "registration": "docs/registered_m7_single_image_v2.md",
    "restriction": "single-image rows only (len(images) <= 1)",
    "train_file": train_p.name, "heldout_file": held_p.name,
    "train_rows": len(train), "heldout_rows": len(held),
    "train_sha256": sha(train_p), "heldout_sha256": sha(held_p),
    "image_integrity": {
        "train_unique_images": len(t_imgs),
        "heldout_unique_images": len(h_imgs),
        "shared_images": len(shared),
        "shared_image_examples": shared[:5],
    },
    "identifier_integrity": {"shared_qids": len(shared_qid)},
}

out = ROOT / "data/virl39k_m7_split_manifest_v3.json"
out.write_text(json.dumps(man, indent=2, sort_keys=True) + "\n")

print(f"train {len(train)} rows / {len(t_imgs)} images")
print(f"heldout {len(held)} rows / {len(h_imgs)} images")
print(f"shared images: {len(shared)}   shared qids: {len(shared_qid)}")
if shared:
    raise SystemExit("FAIL: train/heldout share images; I6 violated")
print("PASS: image-disjoint (I6 holds under the single-image restriction)")
print(f"wrote {out.name}")
