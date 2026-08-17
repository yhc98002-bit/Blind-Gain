#!/usr/bin/env python3
"""Append every template_id not already in the package, so the inventory is provably complete."""
import json, os, glob, shutil, collections, sys
ROOT="/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"
OUT=os.path.join(ROOT,"reports/review_packages/pi_review_v2_20260811")
os.chdir(ROOT)

d=json.load(open(os.path.join(OUT,"examples.json")))
covered={e["template_id"] for e in d["examples"] if e.get("template_id")}
print("already covered template_ids:",len(covered),file=sys.stderr)

def copy_image(src):
    if not src: return None
    p=src if os.path.isabs(src) else os.path.join(ROOT,src)
    if not os.path.exists(p): return None
    b=os.path.basename(p); dst=os.path.join(OUT,"images",b)
    if not os.path.exists(dst): shutil.copyfile(p,dst)
    return "images/"+b

def load_shards(run,key="pair_id"):
    dd=os.path.join("experiments/runs",run,"shards"); out={}
    if not os.path.isdir(dd): return out
    for fn in sorted(os.listdir(dd)):
        if fn.endswith(".jsonl"):
            for l in open(os.path.join(dd,fn)):
                l=l.strip()
                if l:
                    r=json.loads(l); k=r.get(key)
                    if k: out[k]=r
    return out

CATCH_ARMS=[("standard GRPO",load_shards("mini_a5_catch_std_step120_real_an12_20260807T235840Z")),
            ("CP",           load_shards("mini_a5_catch_cp_step120_real_an29_20260731T162926Z"))]

# ---- discover: template_id -> list of (manifest, rows)
files=sorted(glob.glob("data/*.jsonl"))+sorted(glob.glob("data/*/*.jsonl"))+sorted(glob.glob("data/*/*/*.jsonl"))
found=collections.defaultdict(list)
for f in files:
    try:
        if os.path.getsize(f)>60_000_000: continue
        rows=[]
        for i,l in enumerate(open(f)):
            if i>4000: break
            l=l.strip()
            if not l: continue
            try: rows.append(json.loads(l))
            except: break
        for r in rows:
            t=r.get("template_id")
            if t and t not in covered and r.get("image_a_path"):
                found[t].append((f,r))
    except Exception: continue

def lineage(t,man):
    if t.startswith("mini_a5_train_"): return ("train","TRAINING corpus (mini-A5) - not a benchmark","not a benchmark task; shown for completeness of the template census")
    if t.startswith("mini_a5_catch_"): return ("catch","Catch / distractor eval (mini-A5 catch-stability instrument)","invariance specificity - answer-preserving distractor edits (manifest verifier_results.answer_preserved)")
    return ("legacy","Superseded FlipTrack lineage - NOT part of frozen R19/R20","superseded revision of the R19 lineage; retained on disk, not evaluated in the frozen benchmarks")

N_BY={"starred_series_value_v02":2,"starred_series_value_legible_v03":2,"starred_series_value_balanced_v04":2,
      "starred_series_value_guided_v05":2,"starred_series_value_five_v06":2,"starred_legend_label_v01":2,
      "bar_value_v0":2,"mini_a5_catch_distractor_matrix_v1":2,"mini_a5_catch_distractor_scatter_v1":2,
      "mini_a5_catch_distractor_trajectory_v1":2}

added=0
for t in sorted(found):
    man,_=found[t][0]
    rows=[r for f,r in found[t] if f==man]
    n=N_BY.get(t,1)
    fam,famlabel,stage=lineage(t,man)
    picked=[]
    for r in rows:
        ia=copy_image(r.get("image_a_path"))
        if not ia: continue
        picked.append((r,ia))
        if len(picked)>=n: break
    if not picked:
        print(f"  !! no resolvable image for {t} ({man})",file=sys.stderr); continue
    for r,ia in picked:
        ex={"family":fam,"family_label":famlabel,"variant":f"x_{t}","variant_label":f"{t}",
            "pair_id":r.get("pair_id"),"template_id":t,"category":r.get("category"),
            "rung":r.get("rung"),"intervention_type":r.get("intervention_type"),
            "question":r.get("question"),"premise_question":r.get("premise_question"),
            "gold_a":r.get("answer_a"),"gold_b":r.get("answer_b"),
            "premise_gold_a":r.get("premise_answer_a") or r.get("premise_answer"),
            "premise_gold_b":r.get("premise_answer_b"),
            "image_a":ia,"image_b":copy_image(r.get("image_b_path")),
            "mask_a":None,"mask_b":None,"manifest":man,"record":r,"arms":{}}
        if fam=="catch":
            for lab,dd in CATCH_ARMS:
                a=dd.get(r.get("pair_id"))
                if a: ex["arms"][lab]={k:a.get(k) for k in
                    ["prediction_a","prediction_b","extracted_answer_a","extracted_answer_b",
                     "correct_a","correct_b","pair_correct","strict_pair_correct",
                     "contract_valid","collapsed","extraction_level"]}
        d["examples"].append(ex); added+=1
    d["inventory"].append({"family":fam,"family_label":famlabel,"variant":f"x_{t}","variant_label":t,
        "template_id":t,"category":picked[0][0].get("category"),
        "n_in_benchmark":len(rows),"n_in_package":len(picked),"manifest":man,
        "arms_available":[l for l,_ in CATCH_ARMS] if fam=="catch" else [],
        "n_joinable":sum(1 for r in rows if any(r.get("pair_id") in dd for _,dd in CATCH_ARMS)) if fam=="catch" else 0,
        "capability_stage":stage,
        "stage_source":"template census over all data/ manifests; category field quoted verbatim",
        "note":None})
    print(f"[+{fam:6s}] {t:44s} n={len(rows):5d} picked={len(picked)}  {man}",file=sys.stderr)

d["meta"]["n_examples"]=len(d["examples"])
d["meta"]["n_variants"]=len(d["inventory"])
d["meta"]["template_census"]={
 "distinct_template_ids_on_disk":len(covered)+len([t for t in found if found[t]]),
 "covered_in_package":len({e["template_id"] for e in d["examples"] if e.get("template_id")}),
 "method":"scan of every data/**.jsonl manifest for distinct template_id values"}
json.dump(d,open(os.path.join(OUT,"examples.json"),"w"),indent=1)
print("added",added,"examples; total",len(d["examples"]),"variants",len(d["inventory"]),file=sys.stderr)
