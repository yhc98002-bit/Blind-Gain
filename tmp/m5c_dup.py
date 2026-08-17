#!/usr/bin/env python3
"""Duplicate-content census on the 601 geo3k test items, and its effect on
the 100->400 transition table. Items are keyed on (split,row_index); several
rows share the same problem text and/or the same image."""
from __future__ import annotations

import collections
import hashlib
import json
import os

ROOT = "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"
os.chdir(ROOT)

RUN100 = "experiments/runs/blind_solvability_v2_guarded_rescore_anchor_step100_geo3k_real_login_20260712T082107Z"


def load_jsonl(p):
    with open(p, encoding="utf-8") as fh:
        return [json.loads(x) for x in fh if x.strip()]


rows = {(str(r["split"]), int(r["row_index"])): r
        for r in load_jsonl(os.path.join(RUN100, "per_item.jsonl")) if r.get("split") == "test"}
sub = {(r["split"], int(r["row_index"])): r
       for r in load_jsonl("reports/m5c_item_substrate_v1.jsonl")}
assert set(rows) == set(sub), "key sets differ"

def census(fn, name):
    groups = collections.defaultdict(list)
    for k, r in rows.items():
        groups[fn(r)].append(k)
    sizes = collections.Counter(len(v) for v in groups.values())
    n_in_dup = sum(len(v) for v in groups.values() if len(v) > 1)
    return {
        "field": name,
        "n_items": len(rows),
        "n_distinct_groups": len(groups),
        "group_size_histogram": dict(sorted(sizes.items())),
        "n_items_in_a_multi_item_group": n_in_dup,
        "fraction_items_in_multi_item_group": n_in_dup / len(rows),
    }, groups


prob_c, prob_g = census(lambda r: hashlib.sha256(str(r["problem"]).encode()).hexdigest(), "problem_sha256")
img_c, img_g = census(lambda r: json.dumps(r["image_sha256"], sort_keys=True), "image_sha256")
pair_c, pair_g = census(
    lambda r: hashlib.sha256((str(r["problem"]) + "|" + json.dumps(r["image_sha256"], sort_keys=True)).encode()).hexdigest(),
    "problem+image",
)

# Do duplicate-content groups move together? For exact (problem+image) duplicates
# the greedy response should be identical, hence identical transition label.
disagree = 0
groups_gt1 = 0
for g, keys in pair_g.items():
    if len(keys) < 2:
        continue
    groups_gt1 += 1
    labs = {sub[k]["transition_100_400_lenient"] for k in keys}
    if len(labs) > 1:
        disagree += 1

# transition table on de-duplicated (problem+image) groups, one item per group
first = {g: sorted(keys)[0] for g, keys in pair_g.items()}
c = collections.Counter(sub[k]["transition_100_400_lenient"] for k in first.values())
n_dedup = len(first)
b01, b10 = c["gained"], c["lost"]
dedup = {
    "n_groups": n_dedup,
    "counts": dict(c),
    "acc_from": (c["stable_correct"] + c["lost"]) / n_dedup,
    "acc_to": (c["stable_correct"] + c["gained"]) / n_dedup,
    "net_delta": (b01 - b10) / n_dedup,
    "turnover_fraction": (b01 + b10) / n_dedup,
    "b01_gained": b01,
    "b10_lost": b10,
}

out = {
    "note": "Descriptive only. The reported substrate and all headline transition "
            "tables use ALL 601 items keyed on (split,row_index); this census records "
            "content duplication so downstream analyses can decide how to treat it.",
    "problem_text": prob_c,
    "image": img_c,
    "problem_plus_image": pair_c,
    "exact_duplicate_groups_with_disagreeing_100_400_label": disagree,
    "exact_duplicate_groups_size_gt1": groups_gt1,
    "dedup_by_problem_plus_image_100_to_400_lenient": dedup,
}

tj = "reports/m5c_turnover_v1.json"
art = json.load(open(tj, encoding="utf-8"))
art["duplicate_content_census"] = out
json.dump(art, open(tj, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
open(tj, "a", encoding="utf-8").write("\n")
print(json.dumps(out, indent=2))
