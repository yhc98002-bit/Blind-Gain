#!/usr/bin/env python3
"""Preflight part 3: locked-R19 vs source-R19 item identity. Non-evaluative."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
LOCKED = ROOT / "experiments/runs/caption_qa_pair_build_fliptrack_v02r19_qwen25vl3b_384_20260710T140200Z/shards/captions_shard_0.jsonl"
SRC = ROOT / "data/fliptrack_v02r19_artifact_expanded_source_manifest.jsonl"


def rows(p: Path):
    with p.open(encoding="utf-8") as fh:
        return [json.loads(x) for x in fh if x.strip()]


lk = rows(LOCKED)
sc = rows(SRC)

lk_pid = {str(r["pair_id"]) for r in lk}
lk_spid = {str(r.get("source_pair_id")) for r in lk}
sc_pid = {str(r["pair_id"]) for r in sc}

lk_img = {(r["image_a_sha256"], r["image_b_sha256"]) for r in lk}
sc_img = {(r["image_a_sha256"], r["image_b_sha256"]) for r in sc}

print(
    json.dumps(
        {
            "locked_pair_id_sample": sorted(lk_pid)[:3],
            "locked_source_pair_id_sample": sorted(lk_spid)[:3],
            "source_pair_id_sample": sorted(sc_pid)[:3],
            "locked_source_pair_id_set_equals_source_pair_id_set": lk_spid == sc_pid,
            "locked_pair_ids_unique": len(lk_pid) == len(lk),
            "image_sha_pairs_identical": lk_img == sc_img,
            "n_locked_img_pairs": len(lk_img),
            "n_source_img_pairs": len(sc_img),
            "locked_template_ids": sorted({r["template_id"] for r in lk}),
            "source_template_ids": sorted({r["template_id"] for r in sc}),
        },
        indent=2,
        sort_keys=True,
    )
)
