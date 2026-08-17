#!/usr/bin/env python3
"""Preflight part 2: pair_id disjointness + template role mapping. Non-evaluative."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")

R19 = ROOT / "experiments/runs/caption_qa_pair_build_fliptrack_v02r19_qwen25vl3b_384_20260710T140200Z/shards/captions_shard_0.jsonl"
R19SRC = ROOT / "data/fliptrack_v02r19_artifact_expanded_source_manifest.jsonl"
R20 = ROOT / "data/fliptrack_r20_source_manifest.jsonl"
CHART = ROOT / "data/fliptrack_chart_v08_calibration_v1_manifest.jsonl"


def ids(p: Path) -> set:
    out = set()
    with p.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                out.add(str(json.loads(line)["pair_id"]))
    return out


a, asrc, b, c = ids(R19), ids(R19SRC), ids(R20), ids(CHART)
print(
    json.dumps(
        {
            "r19_locked_n": len(a),
            "r19_source_n": len(asrc),
            "r19_locked_equals_r19_source_pair_ids": a == asrc,
            "r20_n": len(b),
            "chart_n": len(c),
            "r19_r20_shared_pair_ids": len(a & b),
            "r19_chart_shared_pair_ids": len(a & c),
            "r20_chart_shared_pair_ids": len(b & c),
            "union_all_three": len(a | b | c),
        },
        indent=2,
        sort_keys=True,
    )
)

# decontamination record cross-check
dec = ROOT / "data/mini_a5_train_v1/decontamination.json"
if dec.is_file():
    d = json.loads(dec.read_text(encoding="utf-8"))
    print(json.dumps({"decontamination_evaluation_manifests": d.get("evaluation_manifests")}, indent=2, sort_keys=True))
else:
    print(json.dumps({"decontamination_json": "ABSENT"}))
