#!/usr/bin/env python3
"""Preflight 4: pinned R20 source manifest vs the caption-built R20 manifest used
by every prior base-model R20 FlipTrack eval. Non-evaluative (schema/ids only)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
PINNED = ROOT / "data/fliptrack_r20_source_manifest.jsonl"
PRIOR = ROOT / "experiments/runs/caption_qa_pair_build_fliptrack_r20_private_full_v1_20260711T124039Z/shards/captions_shard_0.jsonl"


def rows(p: Path):
    with p.open(encoding="utf-8") as fh:
        return [json.loads(x) for x in fh if x.strip()]


a = rows(PINNED)
b = rows(PRIOR)
print(
    json.dumps(
        {
            "pinned_n": len(a),
            "prior_n": len(b),
            "pinned_pair_ids_equal_prior_source_pair_ids": {str(r["pair_id"]) for r in a}
            == {str(r.get("source_pair_id")) for r in b},
            "pinned_pair_ids_equal_prior_pair_ids": {str(r["pair_id"]) for r in a}
            == {str(r["pair_id"]) for r in b},
            "image_sha_pairs_identical": {(r["image_a_sha256"], r["image_b_sha256"]) for r in a}
            == {(r["image_a_sha256"], r["image_b_sha256"]) for r in b},
            "pinned_templates": sorted({r["template_id"] for r in a}),
            "prior_templates": sorted({r["template_id"] for r in b}),
        },
        indent=2,
        sort_keys=True,
    )
)
