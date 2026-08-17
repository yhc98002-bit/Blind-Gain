#!/usr/bin/env python3
"""Build a PI review package of representative benchmark examples.

Selection is deterministic and outcome-blind: first N pair_ids per template in
frozen source-manifest order (falling back to lexicographic pair_id order).
No interpretive labels are added; every field shown comes from the existing
benchmark manifests / eval records.
"""
import json, os, shutil, sys, collections, html

ROOT = "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"
OUT = os.path.join(ROOT, "reports/review_packages/pi_review_20260811")

# (run directory, join key).  The R20 base run keys on the release pair_id and
# carries the trained arms' key in source_pair_id; verified 1200/1200 join with
# zero image_a_sha256 / question / gold mismatches.
RUNS = {
    "R19": {
        "base":          ("fliptrack_v02r19_packaged_qwen25vl3b_real_an29_20260710T142716Z", "pair_id"),
        "standard_grpo": ("mini_a5_gate1_r19_std_step120_real_an12_20260807T235840Z", "pair_id"),
        "cp":            ("mini_a5_f8_r19_cp_step120_real_an29_20260730T004031Z", "pair_id"),
    },
    "R20": {
        "base":          ("fliptrack_r20_qwen25vl3b_real_an12_20260711T131807Z", "source_pair_id"),
        "standard_grpo": ("mini_a5_gate1_r20_std_step120_real_an12_20260807T235840Z", "pair_id"),
        "cp":            ("mini_a5_f8_r20_cp_step120_real_an29_20260730T004031Z", "pair_id"),
    },
}
ARM_MODEL = {
    "base":          "artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct (frozen base)",
    "standard_grpo": "checkpoints/mini_a5/mini_a5_std_seed1/global_step_120 (registered Gate-1 arm 1, standard GRPO)",
    "cp":            "checkpoints/mini_a5/mini_a5_cp_seed1/global_step_120 (registered Gate-1 arm 4, CP-GRPO)",
}
# Task roles as registered in docs/EXPERIMENT_TODO.md P0.4 / PAPER1_RESEARCH_DOC.md §  (verbatim project terminology)
TEMPLATE_ROLE = {
    "coordinate_register_twenty_point_x_v02": "primary visual anchor (search + binding) - coordinate survey register",
    "starred_series_value_nine_v07":          "oracle-localized readout control - nine-series calibration trace",
    "header_cued_table_code_v02":             "saturated positive control + retention canary - header-cued table",
}

def load_run(run, key="pair_id"):
    d = os.path.join(ROOT, "experiments/runs", run, "shards")
    recs = {}
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".jsonl"):
            continue
        for line in open(os.path.join(d, fn)):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            k = r.get(key)
            if k:
                recs[k] = r
    return recs

def manifest_order(path, key="pair_id"):
    order = []
    if not os.path.exists(path):
        return order
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        pid = r.get(key) or r.get("source_pair_id")
        if pid and pid not in order:
            order.append(pid)
    return order

MANIFESTS = {
    "R19": os.path.join(ROOT, "data/fliptrack_v02r19_artifact_expanded_source_manifest.jsonl"),
    "R20": os.path.join(ROOT, "data/fliptrack_r20/manifest.jsonl"),
}

# ---- how many examples per group -------------------------------------------
PLAN = [
    # (group key, benchmark, template filter, n)
    ("r19_primary",  "R19", "coordinate_register_twenty_point_x_v02", 20),
    ("r19_oracle",   "R19", "starred_series_value_nine_v07",          15),
    ("r20_coord",    "R20", "coordinate_register_twenty_point_x_v02",  6),
    ("r20_starred",  "R20", "starred_series_value_nine_v07",           5),
    ("r20_header",   "R20", "header_cued_table_code_v02",              4),
]

os.makedirs(os.path.join(OUT, "images"), exist_ok=True)

JOIN_AUDIT = {}
arms_data = {}
for bench, runs in RUNS.items():
    arms_data[bench] = {arm: load_run(run, key) for arm, (run, key) in runs.items()}
    counts = {a: len(v) for a, v in arms_data[bench].items()}
    print(f"[{bench}] loaded records per arm: {counts}", file=sys.stderr)
    common = set.intersection(*[set(v) for v in arms_data[bench].values()])
    print(f"[{bench}] pair_ids common to all three arms: {len(common)}", file=sys.stderr)
    # integrity: the joined rows must describe the same item in every arm
    bad = collections.Counter()
    ref_arm = arms_data[bench]["cp"]
    for k in common:
        for arm, recs in arms_data[bench].items():
            if arm == "cp":
                continue
            r, q = recs[k], ref_arm[k]
            if r.get("image_a_sha256") != q.get("image_a_sha256"): bad["image_a_sha256"] += 1
            if r.get("image_b_sha256") != q.get("image_b_sha256"): bad["image_b_sha256"] += 1
            if r.get("question") != q.get("question"): bad["question"] += 1
            if str(r.get("answer_a")) != str(q.get("answer_a")): bad["gold_a"] += 1
            if str(r.get("answer_b")) != str(q.get("answer_b")): bad["gold_b"] += 1
    print(f"[{bench}] cross-arm join mismatches: {dict(bad) or 'none'}", file=sys.stderr)
    JOIN_AUDIT[bench] = {"n_common": len(common), "mismatches": dict(bad)}

def copy_image(src):
    if not src:
        return None
    p = src if os.path.isabs(src) else os.path.join(ROOT, src)
    if not os.path.exists(p):
        return None
    base = os.path.basename(p)
    dst = os.path.join(OUT, "images", base)
    if not os.path.exists(dst):
        shutil.copyfile(p, dst)
    return "images/" + base

examples = []
for gkey, bench, tmpl, n in PLAN:
    arms = arms_data[bench]
    common = set.intersection(*[set(v) for v in arms.values()])
    ref = arms["cp"]
    order = manifest_order(MANIFESTS[bench])
    cand = [p for p in order if p in common and ref[p].get("template_id") == tmpl]
    extra = sorted(p for p in common
                   if ref[p].get("template_id") == tmpl and p not in set(cand))
    cand = cand + extra
    picked = cand[:n]
    print(f"[{gkey}] {bench}/{tmpl}: {len(cand)} available, picked {len(picked)}", file=sys.stderr)
    for pid in picked:
        r = ref[pid]
        ex = {
            "group": gkey,
            "benchmark": bench,
            "pair_id": pid,
            "template_id": r.get("template_id"),
            "task_role": TEMPLATE_ROLE.get(r.get("template_id"), ""),
            "category": r.get("category"),
            "source_pair_id": r.get("source_pair_id"),
            "scene_program_id": r.get("scene_program_id"),
            "prompt_contract_id": r.get("prompt_contract_id"),
            "eval_image_mode": r.get("eval_image_mode"),
            "question": r.get("question"),
            "gold_a": r.get("answer_a"),
            "gold_b": r.get("answer_b"),
            "image_a": copy_image(r.get("eval_image_a_path") or r.get("image_a_path")),
            "image_b": copy_image(r.get("eval_image_b_path") or r.get("image_b_path")),
            "arms": {},
        }
        for arm in ("base", "standard_grpo", "cp"):
            a = arms[arm].get(pid)
            if not a:
                continue
            ex["arms"][arm] = {
                "prediction_a": a.get("prediction_a"),
                "prediction_b": a.get("prediction_b"),
                "extracted_answer_a": a.get("extracted_answer_a"),
                "extracted_answer_b": a.get("extracted_answer_b"),
                "correct_a": a.get("correct_a"),
                "correct_b": a.get("correct_b"),
                "pair_correct": a.get("pair_correct"),
                "strict_pair_correct": a.get("strict_pair_correct"),
                "contract_valid": a.get("contract_valid"),
                "collapsed": a.get("collapsed"),
                "extraction_level": a.get("extraction_level"),
            }
        examples.append(ex)

# ---- premise v2 -------------------------------------------------------------
PV2 = os.path.join(ROOT, "experiments/runs/track4_premise_v2_gates_an29_20260811T095522Z")
def load_pv2(sub):
    recs = {}
    p = os.path.join(PV2, sub, "predictions.jsonl")
    if not os.path.exists(p):
        return recs
    for line in open(p):
        line = line.strip()
        if line:
            r = json.loads(line)
            recs[r["pair_id"]] = r
    return recs

pv2_probe = load_pv2("premise_probe")
pv2_final = load_pv2("final")
pv2_common = sorted(set(pv2_probe) & set(pv2_final))
print(f"[premise_v2] probe={len(pv2_probe)} final={len(pv2_final)} common={len(pv2_common)}", file=sys.stderr)
for pid in pv2_common[:6]:
    pr, fi = pv2_probe[pid], pv2_final[pid]
    ex = {
        "group": "premise_v2",
        "benchmark": "premise-v2 (track4 dev)",
        "pair_id": pid,
        "template_id": fi.get("template_id"),
        "task_role": "",
        "category": fi.get("category"),
        "intervention_type": fi.get("intervention_type"),
        "split": fi.get("split"),
        "scene_program_id": fi.get("scene_program_id"),
        "prompt_contract_id": fi.get("prompt_contract_id"),
        "eval_image_mode": fi.get("eval_image_mode"),
        "question": fi.get("question"),
        "gold_a": fi.get("answer_a"),
        "gold_b": fi.get("answer_b"),
        "premise_question": pr.get("premise_question"),
        "premise_gold_a": pr.get("premise_answer_a"),
        "premise_gold_b": pr.get("premise_answer_b"),
        "image_a": copy_image(fi.get("eval_image_a_path") or fi.get("image_a_path")),
        "image_b": copy_image(fi.get("eval_image_b_path") or fi.get("image_b_path")),
        "arms": {},
        "probes": {},
    }
    for pname, rec in (("premise_probe", pr), ("final", fi)):
        ex["probes"][pname] = {
            "question": rec.get("premise_question") if pname == "premise_probe" else rec.get("question"),
            "gold_a": rec.get("premise_answer_a") if pname == "premise_probe" else rec.get("answer_a"),
            "gold_b": rec.get("premise_answer_b") if pname == "premise_probe" else rec.get("answer_b"),
            "prediction_a": rec.get("prediction_a"),
            "prediction_b": rec.get("prediction_b"),
            "extracted_answer_a": rec.get("extracted_answer_a"),
            "extracted_answer_b": rec.get("extracted_answer_b"),
            "correct_a": rec.get("correct_a"),
            "correct_b": rec.get("correct_b"),
            "pair_correct": rec.get("pair_correct"),
            "strict_pair_correct": rec.get("strict_pair_correct"),
            "contract_valid": rec.get("contract_valid"),
            "collapsed": rec.get("collapsed"),
        }
    examples.append(ex)

meta = {
    "generated_from": ROOT,
    "selection_rule": "first N pair_ids per template in frozen source-manifest order "
                      "(lexicographic pair_id fallback); outcome-blind, no filtering on correctness",
    "arms": ARM_MODEL,
    "runs": {b: {a: {"run": r, "join_key": k} for a, (r, k) in v.items()} for b, v in RUNS.items()},
    "join_audit": JOIN_AUDIT,
    "premise_v2_run": "experiments/runs/track4_premise_v2_gates_an29_20260811T095522Z "
                      "(Qwen2.5-VL-3B-Instruct; base only - no trained-arm predictions exist for premise-v2)",
    "n_examples": len(examples),
    "counts_by_group": dict(collections.Counter(e["group"] for e in examples)),
}
json.dump({"meta": meta, "examples": examples},
          open(os.path.join(OUT, "examples.json"), "w"), indent=1)
print(json.dumps(meta["counts_by_group"]), file=sys.stderr)
print("TOTAL", len(examples), file=sys.stderr)
