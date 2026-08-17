#!/usr/bin/env python3
"""Fixup: carry qid/image_sha256 through with their SOURCE types (not str()),
and record which join-identity checks are vacuous."""
from __future__ import annotations

import hashlib
import json
import os

ROOT = "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"
os.chdir(ROOT)

RUNS = {
    "100": "experiments/runs/blind_solvability_v2_guarded_rescore_anchor_step100_geo3k_real_login_20260712T082107Z",
    "150": "experiments/runs/m5_geo3k_step150_an12_gpu4_20260718T051839Z",
    "200": "experiments/runs/m5_geo3k_step200_an29_gpu4_20260722T141052Z",
    "300": "experiments/runs/m5_geo3k_step300_an12_gpu0_20260726T083303Z",
    "400": "experiments/runs/m5_geo3k_step400_an12_gpu0_20260728T053115Z",
}
STEPS = ["100", "150", "200", "300", "400"]


def load_jsonl(p):
    with open(p, encoding="utf-8") as fh:
        return [json.loads(x) for x in fh if x.strip()]


raw = {}
for s in STEPS:
    raw[s] = {
        (str(r["split"]), int(r["row_index"])): r
        for r in load_jsonl(os.path.join(RUNS[s], "per_item.jsonl"))
        if r.get("split") == "test"
    }

# vacuity + type census of the join-identity fields
census = {}
for f in ("qid", "image_sha256", "ground_truth", "problem"):
    per_step = {}
    for s in STEPS:
        vals = [r.get(f) for r in raw[s].values()]
        per_step[s] = {
            "n_null": sum(1 for v in vals if v is None),
            "n_distinct": len({json.dumps(v, sort_keys=True) for v in vals}),
            "python_types": sorted({type(v).__name__ for v in vals}),
        }
    census[f] = per_step

sub_path = "reports/m5c_item_substrate_v1.jsonl"
rows = load_jsonl(sub_path)
with open(sub_path, "w", encoding="utf-8") as fh:
    for rec in rows:
        key = (rec["split"], int(rec["row_index"]))
        src = raw["100"][key]
        rec["qid"] = src.get("qid")                      # native type, null stays null
        rec["image_sha256"] = src.get("image_sha256")    # native type (list at source)
        rec["ground_truth"] = src.get("ground_truth")
        fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")

new_sha = hashlib.sha256(open(sub_path, "rb").read()).hexdigest()

tj = "reports/m5c_turnover_v1.json"
art = json.load(open(tj, encoding="utf-8"))
art["substrate_sha256"] = new_sha
art["join_identity_field_census"] = census
art["join_identity_check_scope"] = (
    "The (split,row_index) join was cross-checked on ground_truth, problem (sha256), "
    "image_sha256 and qid: 0 mismatches out of 601 items x 4 comparison steps. NOTE: "
    "`qid` is null in ALL FIVE source runs, so the qid arm of that check is VACUOUS and "
    "carries no evidence. The informative arms are ground_truth, problem-sha256 and "
    "image_sha256, each of which is populated and item-distinguishing."
)
json.dump(art, open(tj, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
open(tj, "a", encoding="utf-8").write("\n")

print(json.dumps({
    "substrate_sha256": new_sha,
    "turnover_sha256": hashlib.sha256(open(tj, "rb").read()).hexdigest(),
    "census": census,
}, indent=2))
