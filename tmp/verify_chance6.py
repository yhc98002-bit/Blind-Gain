import json, collections, re, sys
R="/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/"
def load(p): return [json.loads(l) for l in open(R+p) if l.strip()]
p="experiments/runs/m11_blind_gemma3_virl4096_none_gemma3_none_s0of1_an29_20260716T200132Z/per_item.jsonl"
d=load(p)
print("n",len(d))
print("keys:", sorted(d[0].keys()))
print("source_metadata keys:", sorted(d[0]['source_metadata'].keys()))
print(json.dumps({k:(str(v)[:400]) for k,v in d[0].items()}, indent=1)[:2500])
print("answer_type census:", dict(collections.Counter(r['source_metadata']['answer_type'] for r in d)))
# is there a structured options field anywhere?
for r in d[:2000]:
    if r['source_metadata']['answer_type']=='multiple_choice':
        print("MC sample source_metadata:", json.dumps(r['source_metadata'])[:1200])
        print("MC sample problem:", repr(r['problem'])[:1200])
        break
