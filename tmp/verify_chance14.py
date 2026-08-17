import json, collections, re, sys
import numpy as np
R="/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/"
def load(p): return [json.loads(l) for l in open(R+p) if l.strip()]
ARM={("gemma3","none"):"m11_blind_gemma3_virl4096_none_gemma3_none_s0of1_an29_20260716T200132Z",
     ("gemma3","real"):"m11_blind_gemma3_virl4096_real_gemma3_real_s0of1_an29_20260716T191637Z",
     ("gemma3","caption"):"m11_blind_gemma3_virl4096_caption_gemma3_caption_s0of1_an29_20260716T231512Z",
     ("internvl3","none"):"m11_virl4096_retry1_internvl3_none_s0of1_an12_20260716T170739Z",
     ("internvl3","real"):"m11_virl4096_patchbudgetv2_internvl3_real_s0of1_an29_20260717T072527Z",
     ("internvl3","caption"):"m11_virl4096_retry1_internvl3_caption_s0of1_an12_20260716T170744Z"}
D={}
for kk,v in ARM.items():
    D[kk]={r['qid']:(bool(r['acc_final']),bool(r['acc_strict'])) for r in load("experiments/runs/%s/per_item.jsonl"%v)}
meta={r['qid']:r for r in load("experiments/runs/%s/per_item.jsonl"%ARM[("gemma3","none")])}
qids=sorted(meta)
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
KK={q:(len(parseR(meta[q]['problem'])) or None) if at[q]=='multiple_choice' else 0 for q in qids}
del meta
def stats(w,b,nu,reps=6000,seed=555000111,chunk=500):
    w=np.asarray(w,float); b=np.asarray(b,float); nu=np.asarray(nu,float); n=len(w)
    mw,mb,mn=w.mean(),b.mean(),nu.mean(); den=mw-mn
    corr=(mb-mn)/den if den!=0 else float('nan'); naive=mb/mw if mw!=0 else float('nan')
    rs=np.random.RandomState(seed); out=[]; neg=0; tot=0
    for s in range(0,reps,chunk):
        c_=min(chunk,reps-s); idx=rs.randint(0,n,size=(c_,n))
        bw=w[idx].mean(1); bb=b[idx].mean(1); bn=nu[idx].mean(1)
        d=bw-bn; neg+=int((d<=0).sum()); tot+=c_
        with np.errstate(divide='ignore',invalid='ignore'):
            r=np.where(d!=0,(bb-bn)/d,np.nan)
        out.append(r[np.isfinite(r)])
    a=np.concatenate(out)
    lo,hi=(np.percentile(a,[2.5,97.5]) if len(a)>=100 else (float('nan'),float('nan')))
    return len(w),mw,mb,mn,naive,corr,lo,hi,neg/tot
def P(tag,qs,arm_w,arm_b,nu,idx=0):
    w=[D[arm_w][q][idx] for q in qs]; b=[D[arm_b][q][idx] for q in qs]
    n,mw,mb,mn,na,co,lo,hi,nf=stats(w,b,nu)
    print("%-52s n=%-5d with=%.4f blind=%.4f null=%.4f naive=%.4f corr=%.4f CI=[%.4f,%.4f] negden=%.3f"%(tag,n,mw,mb,mn,na,co,lo,hi,nf)); sys.stdout.flush()
for backend in ("gemma3","internvl3"):
    for cond in ("none","caption"):
        print("### %s blind=%s"%(backend,cond)); sys.stdout.flush()
        mcdet=[q for q in qids if at[q]=='multiple_choice' and KK[q]]
        for kv in sorted({KK[q] for q in mcdet}):
            sub=[q for q in mcdet if KK[q]==kv]; P("  MC k=%d"%kv,sub,(backend,"real"),(backend,cond),[1.0/kv]*len(sub))
        P("  MC pooled (k determinable)",mcdet,(backend,"real"),(backend,cond),[1.0/KK[q] for q in mcdet])
        for a in ("numeric","text_or_expression"):
            sub=[q for q in qids if at[q]==a]; P("  free-form %s"%a,sub,(backend,"real"),(backend,cond),[0.0]*len(sub))
        ff=[q for q in qids if at[q] in ("numeric","text_or_expression")]
        P("  free-form pooled",ff,(backend,"real"),(backend,cond),[0.0]*len(ff))
        P("  free-form pooled [STRICT]",ff,(backend,"real"),(backend,cond),[0.0]*len(ff),idx=1)
        P("  WHOLE 4096 naive ref",qids,(backend,"real"),(backend,cond),[0.0]*len(qids))
        und=[q for q in qids if at[q]=='multiple_choice' and not KK[q]]
        print("  k-indeterminable n=%d with=%.4f blind=%.4f"%(len(und),sum(D[(backend,'real')][q][0] for q in und)/len(und),sum(D[(backend,cond)][q][0] for q in und)/len(und))); sys.stdout.flush()
print("strict sums:", {(bk,c): sum(D[(bk,c)][q][1] for q in qids) for bk in ("gemma3","internvl3") for c in ("none","real","caption")})
