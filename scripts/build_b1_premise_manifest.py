#!/usr/bin/env python3
"""Build the B1 premise-probe manifest per docs/registered_b1_premise_probe_v1.md.

Derived manifest: same images, question := premise_question, and both member
golds := premise_answer (the premise is invariant across the flip by design).
"""
import hashlib
import json
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
SRC = ROOT / "data/b1_geometry_track_v1/manifest.jsonl"
OUT = ROOT / "data/b1_premise_probe_v1.jsonl"

rows = [json.loads(l) for l in SRC.read_text().splitlines() if l.strip()]
chained = [r for r in rows if r.get("intervention_type") == "chained_premise"]
if len(chained) != 20:
    raise SystemExit(f"FAIL: {len(chained)} chained_premise items, expected 20")

out = []
for r in chained:
    pq, pa = r.get("premise_question"), r.get("premise_answer")
    if not pq or not pa:
        raise SystemExit(f"FAIL: {r['pair_id']} missing premise fields")
    d = dict(r)
    d["question"] = pq
    d["answer_a"] = pa
    d["answer_b"] = pa
    d["answers_equal"] = True
    d["final_question_original"] = r["question"]
    d["final_answer_a_original"] = r["answer_a"]
    d["final_answer_b_original"] = r["answer_b"]
    d["probe"] = "premise"
    out.append(d)

blob = "".join(json.dumps(d, sort_keys=True) + "\n" for d in out)
OUT.write_text(blob)
print(f"wrote {OUT}  n={len(out)}  sha256={hashlib.sha256(blob.encode()).hexdigest()}")
