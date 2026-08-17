#!/usr/bin/env python3
"""Probe the R3 data contracts on the remote repo. Read-only."""
import glob
import hashlib
import json
import os
from collections import Counter

ROOT = "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"

out = {}

# 1. held-out jsonl: sha, rows, fields, stratum recount
path = os.path.join(ROOT, "data/virl39k_m7_heldout_v3.jsonl")
digest = hashlib.sha256()
with open(path, "rb") as handle:
    for chunk in iter(lambda: handle.read(1 << 20), b""):
        digest.update(chunk)
rows = []
with open(path, encoding="utf-8") as handle:
    for line in handle:
        if line.strip():
            rows.append(json.loads(line))
out["heldout_sha256"] = digest.hexdigest()
out["heldout_rows"] = len(rows)
first = rows[0]
out["heldout_top_keys"] = sorted(first.keys())
out["heldout_metadata_keys"] = sorted(first.get("metadata", {}).keys())
out["heldout_first_qid_type"] = type(first.get("qid")).__name__
out["heldout_first_row_index_type"] = type(first.get("row_index")).__name__
out["heldout_qid_unique"] = len({r.get("qid") for r in rows})
out["heldout_row_index_unique"] = len({r.get("row_index") for r in rows})
strata = Counter(
    (r["metadata"].get("source"), r["metadata"].get("category")) for r in rows
)
eligible = [s for s, n in strata.items() if n >= 30]
small = [s for s, n in strata.items() if n < 30]
out["n_strata_total"] = len(strata)
out["n_strata_eligible_ge30"] = len(eligible)
out["n_strata_small"] = len(small)
out["eligible_sizes"] = sorted(strata[s] for s in eligible)
out["boundary_sizes"] = sorted(n for n in strata.values() if 25 <= n <= 34)

# 2. existing blind_solvability_virl39k_v1 per_item schema
candidates = sorted(
    glob.glob(
        os.path.join(
            ROOT,
            "experiments/runs/blind_solvability_virl39k_v1_pilot_contract_guarded_*",
        )
    )
)
out["blind_solvability_runs"] = [os.path.basename(c) for c in candidates]
for c in candidates[:1]:
    per_item = os.path.join(c, "per_item.jsonl")
    if os.path.isfile(per_item):
        with open(per_item, encoding="utf-8") as handle:
            row = json.loads(handle.readline())
        out["per_item_keys"] = sorted(row.keys())
        out["per_item_example"] = {
            k: row.get(k)
            for k in (
                "qid",
                "row_index",
                "split",
                "condition",
                "q_i",
                "p_i_jeffreys",
                "sample_count",
                "sample_correct_count",
                "greedy_canonical_correct",
            )
        }

# 3. state of the live m7 step-0 runs
step0 = sorted(
    glob.glob(os.path.join(ROOT, "experiments/runs/m7_step0_heldout_base_*"))
)
out["step0_run_dirs"] = {}
for d in step0:
    name = os.path.basename(d)
    entry = {"contents": sorted(os.listdir(d))}
    pi = os.path.join(d, "per_item.jsonl")
    if os.path.isfile(pi):
        with open(pi, encoding="utf-8") as handle:
            n = sum(1 for line in handle if line.strip())
        entry["per_item_rows"] = n
        with open(pi, encoding="utf-8") as handle:
            row = json.loads(handle.readline())
        entry["per_item_keys"] = sorted(row.keys())
        entry["condition"] = row.get("condition")
        entry["sample_count"] = row.get("sample_count")
    man = os.path.join(d, "run_manifest.json")
    if os.path.isfile(man):
        with open(man, encoding="utf-8") as handle:
            m = json.load(handle)
        entry["manifest_status"] = m.get("status")
        entry["manifest_job_type"] = m.get("job_type")
        entry["manifest_keys"] = sorted(m.keys())
    out["step0_run_dirs"][name] = entry

# 4. does per_item row_index/qid match the heldout identity space?
if step0:
    pi = os.path.join(step0[0], "per_item.jsonl")
    if os.path.isfile(pi):
        seen = []
        with open(pi, encoding="utf-8") as handle:
            for i, line in enumerate(handle):
                if i >= 3:
                    break
                r = json.loads(line)
                seen.append({"qid": r.get("qid"), "row_index": r.get("row_index"), "split": r.get("split")})
        out["step0_first_rows_identity"] = seen
        heldout_ids = {(r["qid"], r["row_index"]) for r in rows}
        out["step0_first_in_heldout"] = [
            (s["qid"], s["row_index"]) in heldout_ids for s in seen
        ]

print(json.dumps(out, indent=1, default=str))
