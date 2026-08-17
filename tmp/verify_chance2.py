import json, csv, collections, sys
csv.field_size_limit(sys.maxsize)
R="/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/"
def load(p): return [json.loads(l) for l in open(R+p) if l.strip()]
with open(R+"data/vlmevalkit/MMStar_VLMEVAL.tsv", newline='', encoding='utf-8') as f:
    rows={str(r['index']): r for r in csv.DictReader(f, delimiter='\t')}
tsvk={i:[c for c in "ABCD" if str(r.get(c) or "").strip() not in ("","nan","None")] for i,r in rows.items()}
# degenerate: gold not in presented
deg=[(i, rows[i]['answer'], "".join(tsvk[i])) for i in rows if str(rows[i]['answer']).strip() not in tsvk[i]]
print("degenerate (gold not in presented cols):", deg)
for i,_,_ in deg:
    r=rows[i]
    print("  idx",i,"answer=",repr(r['answer']),"A=",repr(r['A'])[:60],"B=",repr(r['B'])[:60],"C=",repr(r['C'])[:60],"D=",repr(r['D'])[:60])
    print("   question:", repr(r['question'])[:300])
