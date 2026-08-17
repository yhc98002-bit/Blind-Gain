import json, collections, re, sys
import numpy as np
R="/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/"
def load(p): return [json.loads(l) for l in open(R+p) if l.strip()]
XF={("gemma3","none"):"experiments/runs/m11_blind_gemma3_virl4096_none_gemma3_none_s0of1_an29_20260716T200132Z/per_item.jsonl",
    ("gemma3","real"):"experiments/runs/m11_blind_gemma3_virl4096_real_gemma3_real_s0of1_an29_20260716T191637Z/per_item.jsonl",
    ("gemma3","caption"):"experiments/runs/m11_blind_gemma3_virl4096_caption_gemma3_caption_s0of1_an29_20260716T231512Z/per_item.jsonl",
    ("internvl3","none"):"experiments/runs/m11_virl4096_retry1_internvl3_none_s0of1_an12_20260716T170739Z/per_item.jsonl",
    ("internvl3","real"):"experiments/runs/m11_virl4096_patchbudgetv2_internvl3_real_s0of1_an29_20260717T072527Z/per_item.jsonl",
    ("internvl3","caption"):"experiments/runs/m11_virl4096_retry1_internvl3_caption_s0of1_an12_20260716T170744Z/per_item.jsonl"}
XD={k:{r['qid']:r for r in load(p)} for k,p in XF.items()}
meta=XD[("gemma3","none")]; qids=sorted(meta)
print("n qids", len(qids), "all arms same ids:", all(set(v)==set(meta) for v in XD.values()))

# ---- INDEPENDENT option parser: line-anchored, requires contiguous A.. and >=2 ----
def norm(p): return p.replace('\\n','\n')
def parse2(prob):
    prob=norm(prob)
    found=[]
    for line in prob.split('\n'):
        s=line.strip()
        m=re.match(r'^\(?([A-H])\)?\s*[\.\):：、．]?\s+', s) or re.match(r'^\(?([A-H])[\.\):：、．]\s*', s)
        if m:
            L=m.group(1)
            if not found and L!='A': continue
            if found and ord(L)!=ord(found[-1])+1: continue
            if L not in found: found.append(L)
    return found if len(found)>=2 else []
# ---- report's parser (re-implemented verbatim) ----
def normR(p): return p.replace('\\n','\n').replace('/n','\n')
PATS=[re.compile(r'(?:(?<=^)|(?<=[\s\n(]))\(([A-Z])\)\s*'),
      re.compile(r'^[ \t]*([A-Z])[\.．\)）、:：]\s*', re.M),
      re.compile(r'(?<![A-Za-z0-9])([A-Z])[\.．][ \t]+', re.M)]
def parseR(prob):
    prob=normR(prob); best=[]
    for p in PATS:
        labs=[]
        for m in p.finditer(prob):
            L=m.group(1)
            if L not in labs: labs.append(L)
        exp=[chr(65+i) for i in range(len(labs))]
        if labs==exp and len(labs)>=2 and len(labs)>len(best): best=labs
    return best

at={q:meta[q]['source_metadata']['answer_type'] for q in qids}
kR={}; k2={}
for q in qids:
    if at[q]=='multiple_choice':
        kR[q]=len(parseR(meta[q]['problem'])) or None
        k2[q]=len(parse2(meta[q]['problem'])) or None
    else:
        kR[q]=0; k2[q]=0
mc=[q for q in qids if at[q]=='multiple_choice']
print("MC n:",len(mc))
print("report-parser k dist:", dict(collections.Counter(kR[q] for q in mc)))
print("indep-parser  k dist:", dict(collections.Counter(k2[q] for q in mc)))
dis=[q for q in mc if kR[q]!=k2[q]]
print("k DISAGREEMENTS between parsers:", len(dis))
for q in dis[:15]:
    print("  qid=%s reportk=%s indepk=%s gt=%r"%(q,kR[q],k2[q],meta[q]['ground_truth']))
    print("     problem:", repr(normR(meta[q]['problem']))[:400])
# gold-in-parsed check (report's validation)
viol=[q for q in mc if kR[q] and str(meta[q]['ground_truth']).strip() not in [chr(65+i) for i in range(kR[q])]]
print("report-parser: gold-label outside parsed list:", len(viol))
gtoutside_dist=collections.Counter(str(meta[q]['ground_truth']).strip() for q in mc if kR[q])
print("gold label distribution over parsed MC:", dict(gtoutside_dist))
# indeterminable source census
und=[q for q in mc if not kR[q]]
print("k indeterminable n:", len(und), dict(collections.Counter(meta[q]['source_metadata']['source'] for q in und)))
