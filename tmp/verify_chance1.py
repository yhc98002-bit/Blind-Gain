import json, csv, collections, sys
csv.field_size_limit(sys.maxsize)
R="/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/"
def load(p): return [json.loads(l) for l in open(R+p) if l.strip()]

tsv=R+"data/vlmevalkit/MMStar_VLMEVAL.tsv"
with open(tsv, newline='', encoding='utf-8') as f:
    rd=csv.DictReader(f, delimiter='\t')
    rows={str(r['index']): r for r in rd}
print("TSV n:", len(rows))
pat=collections.Counter(); tsvk={}
for i,r in rows.items():
    present=[c for c in "ABCD" if str(r.get(c) or "").strip() not in ("","nan","None")]
    pat["".join(present)]+=1
    tsvk[i]=present
print("TSV option-column presence patterns:", dict(pat))
kdist=collections.Counter(len(v) for v in tsvk.values())
print("TSV k dist:", dict(kdist))

bl=load("experiments/runs/layer1_blind_mmstar3b_an29_20260710T023019Z/predictions.jsonl")
art={r['index']: r for r in bl}
kart=collections.Counter(len(r.get('option_labels') or []) for r in bl)
print("artifact option_labels k dist:", dict(kart))
dis=[]
for i,r in art.items():
    labs=r.get('option_labels') or []
    if labs != tsvk.get(i):
        dis.append((i, labs, tsvk.get(i), r['gold']))
print("n disagreements artifact vs TSV:", len(dis))
for d in dis[:25]:
    print("  DISAGREE idx=%s artifact=%s tsv=%s gold=%s" % d)
