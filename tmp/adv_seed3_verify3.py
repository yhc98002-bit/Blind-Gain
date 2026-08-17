#!/usr/bin/env python3
"""Pass 3: compare base vs arm prompt text (answer-tag contract) on geometry pairs."""
import glob, json, hashlib
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
TEMPLATE = "coordinate_register_twenty_point_x_v02"
RUNS = {
    "base": "fliptrack_v02r19_packaged_qwen25vl3b_real_an29_20260710T142716Z",
    "seed3": "pilot_fliptrack_a2_gray_seed3_step100_real_an29_20260725T092515Z",
    "seed1": "pilot_fliptrack_a2_gray_seed1_step100_real_an12_20260716T152519Z",
}

def load(run):
    rows = {}
    for p in sorted(glob.glob(str(ROOT / "experiments/runs" / run / "shards" / "*.jsonl"))):
        for line in Path(p).read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("template_id") != TEMPLATE:
                continue
            rows[str(r["pair_id"])] = r
    return rows

d = {k: load(v) for k, v in RUNS.items()}
ids = sorted(d["base"])
out = {}
q_same_b3 = sum(1 for p in ids if d["base"][p]["question"] == d["seed3"][p]["question"])
q_same_b1 = sum(1 for p in ids if d["base"][p]["question"] == d["seed1"][p]["question"])
out["question_identical_base_vs_seed3"] = f"{q_same_b3}/{len(ids)}"
out["question_identical_base_vs_seed1"] = f"{q_same_b1}/{len(ids)}"
out["base_question_contains_answer_tag_instruction"] = sum(
    1 for p in ids if "<answer>" in d["base"][p]["question"]
)
out["seed3_question_contains_answer_tag_instruction"] = sum(
    1 for p in ids if "<answer>" in d["seed3"][p]["question"]
)
out["base_question_sample"] = d["base"][ids[0]]["question"][-260:]
out["base_schema_version"] = d["base"][ids[0]].get("schema_version")
out["arm_schema_version"] = d["seed3"][ids[0]].get("schema_version")

# contract-validity of base member slots (recomputed) among base pair-correct
import sys
sys.path.insert(0, str(ROOT))
from src.eval.fliptrack_metrics import pair_score
n_lenient = n_strict = 0
lenient_not_strict = 0
for p in ids:
    s = pair_score(d["base"][p])
    n_lenient += bool(s["pair_correct"])
    n_strict += bool(s["strict_pair_correct"])
    if s["pair_correct"] and not s["strict_pair_correct"]:
        lenient_not_strict += 1
out["base_lenient_correct"] = n_lenient
out["base_strict_correct"] = n_strict
out["base_lenient_correct_but_contract_invalid"] = lenient_not_strict

# arm-side same figure
for s in ("seed1", "seed3"):
    a = b = 0
    for p in ids:
        sc = pair_score(d[s][p])
        a += bool(sc["pair_correct"])
        b += bool(sc["strict_pair_correct"])
    out[f"{s}_lenient_correct"] = a
    out[f"{s}_strict_correct"] = b

print(json.dumps(out, indent=1, sort_keys=True))
