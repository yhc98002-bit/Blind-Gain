import json, re, collections, random
R="/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/"
rows=[json.loads(l) for l in open(R+"experiments/runs/m11_blind_gemma3_virl4096_none_gemma3_none_s0of1_an29_20260716T200132Z/per_item.jsonl") if l.strip()]
meta={r['qid']:r for r in rows}; qids=sorted(meta)
def normR(p): return p.replace('\\n','\n').replace('/n','\n')
PATS=[re.compile(r'(?:(?<=^)|(?<=[\s\n(]))\(([A-Z])\)\s*'),
      re.compile(r'^[ \t]*([A-Z])[\.．\)）、:：]\s*', re.M),
      re.compile(r'(?<![A-Za-z0-9])([A-Z])[\.．][ \t]+', re.M)]
def parseR(prob):
    prob=normR(prob); best=[]; bestspans=None
    for p in PATS:
        labs=[]; spans={}
        for m in p.finditer(prob):
            L=m.group(1)
            if L not in labs: labs.append(L); spans[L]=m.start()
        exp=[chr(65+i) for i in range(len(labs))]
        if labs==exp and len(labs)>=2 and len(labs)>len(best): best=labs; bestspans=spans
    return best,bestspans
mc=[q for q in qids if meta[q]['source_metadata']['answer_type']=='multiple_choice']
# 1. monotonic position check: option markers should appear in increasing order
nonmono=[]; tailfrac=[]
for q in mc:
    labs,sp=parseR(meta[q]['problem'])
    if not labs: continue
    pos=[sp[L] for L in labs]
    if pos!=sorted(pos): nonmono.append(q)
    tailfrac.append(pos[0]/max(1,len(normR(meta[q]['problem']))))
print("parsed MC:",len(tailfrac))
print("non-monotonic option marker order (suspect parse):", len(nonmono), nonmono[:10])
import statistics
print("first-marker relative position: median %.2f, frac<0.2 (marker very early = suspect): %.3f"%(statistics.median(tailfrac), sum(1 for t in tailfrac if t<0.2)/len(tailfrac)))
# 2. suspicious: geometry problems where letters are point names
susp=[q for q in mc if parseR(meta[q]['problem'])[0] and 'Choices' not in normR(meta[q]['problem']) and 'choice' not in normR(meta[q]['problem']).lower() and 'options' not in normR(meta[q]['problem']).lower()]
print("parsed MC with NO 'choices/options' marker word in prompt:", len(susp))
random.seed(1)
for q in random.sample(susp,min(6,len(susp))):
    labs,_=parseR(meta[q]['problem'])
    print("  --- qid=%s parsed_k=%d gt=%r"%(q,len(labs),meta[q]['ground_truth']))
    print("      ", repr(normR(meta[q]['problem']))[:420])
