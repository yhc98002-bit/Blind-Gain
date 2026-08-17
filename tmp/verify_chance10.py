import json, collections, re
import numpy as np
R="/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/"
def load(p): return [json.loads(l) for l in open(R+p) if l.strip()]
ARM={("gemma3","none"):"m11_blind_gemma3_virl4096_none_gemma3_none_s0of1_an29_20260716T200132Z",
     ("gemma3","real"):"m11_blind_gemma3_virl4096_real_gemma3_real_s0of1_an29_20260716T191637Z",
     ("gemma3","caption"):"m11_blind_gemma3_virl4096_caption_gemma3_caption_s0of1_an29_20260716T231512Z",
     ("internvl3","none"):"m11_virl4096_retry1_internvl3_none_s0of1_an12_20260716T170739Z",
     ("internvl3","real"):"m11_virl4096_patchbudgetv2_internvl3_real_s0of1_an29_20260717T072527Z",
     ("internvl3","caption"):"m11_virl4096_retry1_internvl3_caption_s0of1_an12_20260716T170744Z"}
D={k:{r['qid']:r for r in load("experiments/runs/%s/per_item.jsonl"%v)} for k,v in ARM.items()}
meta=D[("gemma3","none")]; qids=sorted(meta)
at={q:meta[q]['source_metadata']['answer_type'] for q in qids}
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
k={q:(len(parseR(meta[q]['problem'])) or None) if at[q]=='multiple_choice' else 0 for q in qids}

def boot(w,b,nul,reps=20000,seed=555000111):
    w=np.asarray(w,float); b=np.asarray(b,float); nul=np.asarray(nul,float); n=len(w)
    rs=np.random.RandomState(seed); idx=rs.randint(0,n,size=(reps,n))
    bw=w[idx].mean(1); bb=b[idx].mean(1); bn=nul[idx].mean(1)
    with np.errstate(divide='ignore',invalid='ignore'):
        c=np.where((bw-bn)!=0,(bb-bn)/(bw-bn),np.nan)
    c2=c[np.isfinite(c)]
    return (np.percentile(c2,[2.5,97.5]) if len(c2)>=100 else (float('nan'),float('nan'))), float(np.mean((bw-bn)<=0))
def summ(tag,ws,bs,nu):
    w=np.array(ws,float); b=np.array(bs,float); n_=np.array(nu,float)
    mw,mb,mn=w.mean(),b.mean(),n_.mean(); den=mw-mn
    corr=(mb-mn)/den if den!=0 else float('nan'); naive=mb/mw if mw!=0 else float('nan')
    (lo,hi),negfrac=boot(w,b,n_)
    print("%-56s n=%-5d with=%.4f blind=%.4f null=%.4f naive=%.4f corr=%.4f CI=[%.4f,%.4f] negden=%.3f"%(tag,len(w),mw,mb,mn,naive,corr,lo,hi,negfrac))

for backend in ("gemma3","internvl3"):
    real=D[(backend,"real")]
    for cond in ("none","caption"):
        bl=D[(backend,cond)]
        print("### %s blind=%s"%(backend,cond))
        mcdet=[q for q in qids if at[q]=='multiple_choice' and k[q]]
        for kk in sorted({k[q] for q in mcdet}):
            sub=[q for q in mcdet if k[q]==kk]
            summ("  MC k=%d"%kk,[real[q]['acc_final'] for q in sub],[bl[q]['acc_final'] for q in sub],[1.0/kk]*len(sub))
        summ("  MC pooled (k determinable)",[real[q]['acc_final'] for q in mcdet],[bl[q]['acc_final'] for q in mcdet],[1.0/k[q] for q in mcdet])
        for a in ("numeric","text_or_expression"):
            sub=[q for q in qids if at[q]==a]
            summ("  free-form %s"%a,[real[q]['acc_final'] for q in sub],[bl[q]['acc_final'] for q in sub],[0.0]*len(sub))
        ff=[q for q in qids if at[q] in ("numeric","text_or_expression")]
        summ("  free-form pooled",[real[q]['acc_final'] for q in ff],[bl[q]['acc_final'] for q in ff],[0.0]*len(ff))
        summ("  WHOLE 4096 naive ref (null=0)",[real[q]['acc_final'] for q in qids],[bl[q]['acc_final'] for q in qids],[0.0]*len(qids))
        summ("  free-form pooled [STRICT]",[real[q]['acc_strict'] for q in ff],[bl[q]['acc_strict'] for q in ff],[0.0]*len(ff))
        und=[q for q in qids if at[q]=='multiple_choice' and not k[q]]
        print("  k-indeterminable n=%d with=%.4f blind=%.4f"%(len(und),sum(real[q]['acc_final'] for q in und)/len(und),sum(bl[q]['acc_final'] for q in und)/len(und)))
print()
print("Gemma-3 acc_strict all-zero check:", {c: sum(D[("gemma3",c)][q]['acc_strict'] for q in qids) for c in ("none","real","caption")})
print("InternVL3 acc_strict sums:", {c: sum(D[("internvl3",c)][q]['acc_strict'] for q in qids) for c in ("none","real","caption")})
