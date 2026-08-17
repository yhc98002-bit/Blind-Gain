import json, os, re, collections
R="/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"
def load(p): return [json.loads(l) for l in open(p) if l.strip()]
runs={
 ("gemma3","none"):"experiments/runs/m11_blind_gemma3_virl4096_none_gemma3_none_s0of1_an29_20260716T200132Z/per_item.jsonl",
 ("gemma3","real"):"experiments/runs/m11_blind_gemma3_virl4096_real_gemma3_real_s0of1_an29_20260716T191637Z/per_item.jsonl",
 ("gemma3","caption"):"experiments/runs/m11_blind_gemma3_virl4096_caption_gemma3_caption_s0of1_an29_20260716T231512Z/per_item.jsonl",
 ("internvl3","none"):"experiments/runs/m11_virl4096_retry1_internvl3_none_s0of1_an12_20260716T170739Z/per_item.jsonl",
 ("internvl3","real"):"experiments/runs/m11_virl4096_patchbudgetv2_internvl3_real_s0of1_an29_20260717T072527Z/per_item.jsonl",
 ("internvl3","caption"):"experiments/runs/m11_virl4096_retry1_internvl3_caption_s0of1_an12_20260716T170744Z/per_item.jsonl",
}
D={}
for k,p in runs.items():
    fp=os.path.join(R,p)
    print(k, os.path.exists(fp))
    D[k]=load(fp)
    print("   n=",len(D[k]), "uniq qid", len(set(r['qid'] for r in D[k])))
base=set(r['qid'] for r in D[("gemma3","none")])
for k,v in D.items():
    s=set(r['qid'] for r in v)
    print(k,"same qid set as gemma3/none:", s==base)

OPT=re.compile(r'^\s*([A-Z])[\.\)、:]\s')
def parse_k(prob):
    labs=[]
    for line in prob.split("\n"):
        m=OPT.match(line)
        if m: labs.append(m.group(1))
    # also inline "A. xx B. xx"
    if len(labs)<2:
        labs=re.findall(r'(?:^|\s)([A-Z])[\.\)]\s', prob)
    seq=[]
    for L in labs:
        if L not in seq: seq.append(L)
    return seq

mc=[r for r in D[("gemma3","none")] if r['source_metadata']['answer_type']=='multiple_choice']
kc=collections.Counter()
badgold=0
for r in mc:
    seq=parse_k(r['problem'])
    exp=[chr(65+i) for i in range(len(seq))]
    ok = seq==exp and len(seq)>=2
    kc[(len(seq), ok)]+=1
    if ok and r['ground_truth'] not in seq: badgold+=1
print("MC parsed k dist (k, contiguous_from_A):", dict(sorted(kc.items())))
print("gold not in parsed options:", badgold, "of", len(mc))
for r in mc[:2]:
    print("----"); print(r['problem'][:600]); print("GT:", r['ground_truth'], "parsed:", parse_k(r['problem']))
# check non-MC gt samples
for at in ('numeric','text_or_expression'):
    ex=[r for r in D[("gemma3","none")] if r['source_metadata']['answer_type']==at][:3]
    print("==",at,[e['ground_truth'] for e in ex])
