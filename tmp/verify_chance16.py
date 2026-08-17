import json, re, collections
R="/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/"
def load(p): return [json.loads(l) for l in open(R+p) if l.strip()]
GR={r['qid']:r for r in load("experiments/runs/m11_blind_gemma3_virl4096_real_gemma3_real_s0of1_an29_20260716T191637Z/per_item.jsonl")}
GN={r['qid']:r for r in load("experiments/runs/m11_blind_gemma3_virl4096_none_gemma3_none_s0of1_an29_20260716T200132Z/per_item.jsonl")}
IR={r['qid']:r for r in load("experiments/runs/m11_virl4096_patchbudgetv2_internvl3_real_s0of1_an29_20260717T072527Z/per_item.jsonl")}
qids=sorted(GN)
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
        if labs==[chr(65+i) for i in range(len(labs))] and len(labs)>=2 and len(labs)>len(best): best=labs
    return best
K={q:(len(parseR(GN[q]['problem'])) or None) if GN[q]['source_metadata']['answer_type']=='multiple_choice' else 0 for q in qids}
lead=re.compile(r'^\s*\(?([A-H])\)?\s*[\.\):：、．]')
def credited(r):
    if r['acc_final']: return True
    ex=str(r['extracted_answer'] or ''); m=lead.match(ex)
    return bool(m and m.group(1)==str(r['ground_truth']).strip())
print("Gemma-3: per-k with-image accuracy AS SCORED vs LEADING-LABEL-CREDITED (chance floor = 1/k)")
for kv in (2,3,4,5):
    sub=[q for q in qids if K[q]==kv]
    a=sum(GR[q]['acc_final'] for q in sub)/len(sub); c=sum(credited(GR[q]) for q in sub)/len(sub)
    b=sum(GN[q]['acc_final'] for q in sub)/len(sub); d=sum(credited(GN[q]) for q in sub)/len(sub)
    print("  k=%d n=%-5d with: as-scored %.4f -> credited %.4f | blind: %.4f -> %.4f | floor %.4f  %s"%(
        kv,len(sub),a,c,b,d,1/kv, "ABOVE floor after fix" if c>1/kv else "still below"))
mcdet=[q for q in qids if K[q]]
a=sum(GR[q]['acc_final'] for q in mcdet)/len(mcdet); c=sum(credited(GR[q]) for q in mcdet)/len(mcdet)
b=sum(GN[q]['acc_final'] for q in mcdet)/len(mcdet); d=sum(credited(GN[q]) for q in mcdet)/len(mcdet)
nul=sum(1/K[q] for q in mcdet)/len(mcdet)
print("  POOLED n=%d null=%.4f  as-scored: with %.4f blind %.4f corr %.4f"%(len(mcdet),nul,a,b,(b-nul)/(a-nul)))
print("           credited : with %.4f blind %.4f corr %.4f"%(c,d,(d-nul)/(c-nul)))
print()
print("Gemma-3 k=2 (n=75), with-image, sample extracted answers (as-scored acc = 0/75):")
n=0
for q in qids:
    if K[q]==2 and n<8:
        print("   gt=%r extracted=%r acc=%s"%(GR[q]['ground_truth'], str(GR[q]['extracted_answer'])[:70], GR[q]['acc_final'])); n+=1
print()
print("InternVL3 pooled MC: as-scored with %.4f -> credited %.4f (floor 0.2680)"%(
    sum(IR[q]['acc_final'] for q in mcdet)/len(mcdet), sum(credited(IR[q]) for q in mcdet)/len(mcdet)))
