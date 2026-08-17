import json, os, collections, sys
ROOT="/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"
os.chdir(ROOT)
TARGETS=[
 ("R19","data/fliptrack_v02r19_artifact_expanded_source_manifest.jsonl"),
 ("R20","data/fliptrack_r20/manifest.jsonl"),
 ("R20_source","data/fliptrack_r20_source_manifest.jsonl"),
 ("chart_v08","data/fliptrack_chart_v08_calibration_v1_manifest.jsonl"),
 ("chart_v08_diag","data/fliptrack_chart_v08_calibration_v1_diagnostics_v2.jsonl"),
 ("chart_v08_necessity","data/fliptrack_chart_v08_calibration_v1_necessity_eval_manifest_v1.jsonl"),
 ("doc_vnext","data/fliptrack_document_vnext_calibration_manifest.jsonl"),
 ("premise_probe_v2","data/track4_premise_v2_dev_v1/manifest_premise_probe.jsonl"),
 ("causal_v2","data/track4_premise_v2_dev_v1/manifest_causal_pairs.jsonl"),
 ("invariance_v2","data/track4_premise_v2_dev_v1/manifest_invariance_pairs.jsonl"),
 ("groups_v2","data/track4_premise_v2_dev_v1/groups_v2.jsonl"),
 ("b1_premise","data/b1_premise_probe_v1.jsonl"),
]
for r in ["exact","region","none","decoy","named_exact","named_region"]:
    TARGETS.append((f"cue_{r}", f"data/cue_ladder_v1/{r}_manifest.jsonl"))

FIELDS=["template_id","category","intervention_type","rung","cue","cue_mode","variant",
        "task","task_type","probe","split","render_variant_b","chart_kind","annotation",
        "family","construct","premise_transition","chained","kind","member_kind"]

for name,p in TARGETS:
    if not os.path.exists(p):
        print(f"### {name}: MISSING {p}"); continue
    rows=[]
    for line in open(p):
        line=line.strip()
        if line:
            try: rows.append(json.loads(line))
            except: pass
    print(f"### {name}  ({p})  n={len(rows)}")
    if not rows: continue
    keys=collections.Counter()
    for r in rows: keys.update(r.keys())
    present=[f for f in FIELDS if f in keys]
    for f in present:
        c=collections.Counter(str(r.get(f)) for r in rows)
        if len(c)<=12:
            print(f"    {f}: {dict(c)}")
        else:
            print(f"    {f}: {len(c)} distinct, top {dict(c.most_common(6))}")
    other=[k for k in keys if k not in FIELDS]
    print(f"    [all keys] {sorted(keys)}")
    print(f"    [sample question] {str(rows[0].get('question'))[:150]}")
    print()
