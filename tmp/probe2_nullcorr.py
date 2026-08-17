import json, os, csv, sys, collections
R="/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"
def load(p):
    out=[]
    for line in open(p):
        line=line.strip()
        if line: out.append(json.loads(line))
    return out
B=load(os.path.join(R,"experiments/runs/layer1_blind_mmstar3b_an29_20260710T023019Z/predictions.jsonl"))
byk=collections.defaultdict(list)
for r in B: byk[len(r.get("option_labels") or [])].append(r)
for k in sorted(byk):
    print("k=%d n=%d example indices %s"%(k,len(byk[k]),[r["index"] for r in byk[k][:5]]))
# load source tsv
csv.field_size_limit(10**9)
tsv=os.path.join(R,"data/vlmevalkit/MMStar_VLMEVAL.tsv")
rows={}
with open(tsv, newline='') as f:
    rd=csv.DictReader(f, delimiter='\t')
    cols=rd.fieldnames
    for r in rd:
        rows[r.get('index')]=r
print("TSV cols:", cols, "nrows", len(rows))
for k in (2,3):
    for r in byk[k][:2]:
        idx=r["index"]; src=rows.get(idx)
        print("=== k=%d index=%s gold=%s labels=%s"%(k,idx,r["gold"],r["option_labels"]))
        if src:
            q=src.get('question','')
            print("QUESTION:", repr(q[:700]))
            for c in ['A','B','C','D','E','answer']:
                if c in src: print("  col",c,"=",repr(src[c])[:120])
# gold label distribution overall
print("gold dist:", collections.Counter(r["gold"] for r in B))
