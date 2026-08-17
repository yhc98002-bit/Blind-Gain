import json, os, re, collections
R="/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"
def load(p): return [json.loads(l) for l in open(p) if l.strip()]
D=load(os.path.join(R,"experiments/runs/m11_blind_gemma3_virl4096_none_gemma3_none_s0of1_an29_20260716T200132Z/per_item.jsonl"))
mc=[r for r in D if r['source_metadata']['answer_type']=='multiple_choice']
def norm(p):
    return p.replace('\\n','\n').replace('/n','\n')
PATS=[re.compile(r'(?:(?<=^)|(?<=[\s\n(]))\(([A-Z])\)\s*'),
      re.compile(r'^[ \t]*([A-Z])[\.．\)）、:：]\s*', re.M),
      re.compile(r'(?<![A-Za-z0-9])([A-Z])[\.．][ \t]+', re.M)]
def parse_opts(prob):
    prob=norm(prob); best=[]
    for p in PATS:
        labs=[]
        for m in p.finditer(prob):
            L=m.group(1)
            if L not in labs: labs.append(L)
        exp=[chr(65+i) for i in range(len(labs))]
        if labs==exp and len(labs)>=2 and len(labs)>len(best): best=labs
    return best
kc=collections.Counter(); fails=[]
for r in mc:
    o=parse_opts(r['problem'])
    if o: kc[len(o)]+=1
    else: fails.append(r)
print("k dist:",dict(sorted(kc.items())),"determinable",sum(kc.values()),"/",len(mc))
print("fail sources:",collections.Counter(r['source_metadata']['source'] for r in fails).most_common())
bad=[r for r in mc if parse_opts(r['problem']) and r['ground_truth'] not in parse_opts(r['problem'])]
print("gold outside options:",len(bad),[(r['ground_truth'],parse_opts(r['problem'])) for r in bad[:8]])
# check non-MC types don't accidentally parse options
for at in ('numeric','text_or_expression'):
    sub=[r for r in D if r['source_metadata']['answer_type']==at]
    n=sum(1 for r in sub if parse_opts(r['problem']))
    print(at,"n=",len(sub),"would-parse-options:",n)
for r in fails[:5]:
    print("=== GT",r['ground_truth'],r['source_metadata']['source']); print(repr(norm(r['problem'])[:300]))
