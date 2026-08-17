import csv, sys, json
csv.field_size_limit(sys.maxsize)
R="/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/"
with open(R+"data/vlmevalkit/MMStar_VLMEVAL.tsv", newline='', encoding='utf-8') as f:
    rows={str(r['index']):r for r in csv.DictReader(f, delimiter='\t')}
bl={json.loads(l)['index']: json.loads(l) for l in open(R+"experiments/runs/layer1_blind_mmstar3b_an29_20260710T023019Z/predictions.jsonl") if l.strip()}
hits=[]
for i,r in rows.items():
    for c in "ABCD":
        v=str(r.get(c) or "").strip()
        if v.lower() in ("none","na","<na>") and v not in ("","nan"):
            hits.append((i,c,v,r['answer'],bl[i]['option_labels']))
print("items where an option's TEXT is literally None/NA (dropped by the report's census rule but real options):")
for h in hits: print("  idx=%s col=%s text=%r gold=%s artifact_option_labels=%s"%h)
