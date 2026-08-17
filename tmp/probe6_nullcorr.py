import json, os, re, collections
R="/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"
def load(p): return [json.loads(l) for l in open(p) if l.strip()]
D=load(os.path.join(R,"experiments/runs/m11_blind_gemma3_virl4096_none_gemma3_none_s0of1_an29_20260716T200132Z/per_item.jsonl"))
mc=[r for r in D if r['source_metadata']['answer_type']=='multiple_choice']

PATS=[re.compile(r'(?:(?<=^)|(?<=[\s\n(]))\(([A-Z])\)\s*'),           # (A)
      re.compile(r'^[ \t]*([A-Z])[\.．\)）、:：]\s*', re.M),   # A. / A) / A． at line start
      re.compile(r'(?:^|[\s\n])([A-Z])[\.．][ \t]+', re.M)]       # inline A.
def parse_opts(prob):
    best=[]
    for p in PATS:
        labs=[]
        for m in p.finditer(prob):
            L=m.group(1)
            if L not in labs: labs.append(L)
        exp=[chr(65+i) for i in range(len(labs))]
        if labs==exp and len(labs)>=2 and len(labs)>len(best):
            best=labs
    return best
kc=collections.Counter(); fails=[]
for r in mc:
    o=parse_opts(r['problem'])
    if o: kc[len(o)]+=1
    else: fails.append(r)
print("parsed k dist:",dict(sorted(kc.items())),"determinable:",sum(kc.values()),"of",len(mc))
print("fails:",len(fails))
print("fail sources:", collections.Counter(r['source_metadata']['source'] for r in fails).most_common())
badgold=[r for r in mc if parse_opts(r['problem']) and r['ground_truth'] not in parse_opts(r['problem'])]
print("gold outside parsed options:", len(badgold), [ (r['ground_truth'], parse_opts(r['problem'])) for r in badgold[:5]])
for r in fails[:8]:
    print("======== GT:", r['ground_truth'], r['source_metadata']['source']); print(repr(r['problem'][:400]))
