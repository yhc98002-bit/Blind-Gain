import json, csv, collections, sys, random
import numpy as np
csv.field_size_limit(sys.maxsize)
R="/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/"
def load(p): return [json.loads(l) for l in open(R+p) if l.strip()]

# independent bootstrap: different RNG (python random / MT19937), different seed
def boot(w,b,nul,reps=20000,seed=987654321):
    w=np.asarray(w,float); b=np.asarray(b,float); nul=np.asarray(nul,float); n=len(w)
    rs=np.random.RandomState(seed)
    idx=rs.randint(0,n,size=(reps,n))
    bw=w[idx].mean(1); bb=b[idx].mean(1); bn=nul[idx].mean(1)
    with np.errstate(divide='ignore',invalid='ignore'):
        c=np.where((bw-bn)!=0,(bb-bn)/(bw-bn),np.nan)
    c=c[np.isfinite(c)]
    return np.percentile(c,[2.5,97.5]) if len(c)>=100 else (None,None)

def summ(tag,items):
    w=np.array([i['w'] for i in items],float); b=np.array([i['b'] for i in items],float); nu=np.array([i['nul'] for i in items],float)
    mw,mb,mn=w.mean(),b.mean(),nu.mean()
    den=mw-mn
    corr=(mb-mn)/den if den!=0 else None
    naive=mb/mw if mw!=0 else None
    lo,hi=boot(w,b,nu)
    print("%-58s n=%-5d with=%.4f blind=%.4f null=%.4f naive=%s corr=%s CI=[%s,%s]" % (
        tag,len(items),mw,mb,mn,
        "%.4f"%naive if naive is not None else "None",
        "%.4f"%corr if corr is not None else "None",
        "%.4f"%lo if lo is not None else "None","%.4f"%hi if hi is not None else "None"))
    return dict(n=len(items),mw=mw,mb=mb,mn=mn,naive=naive,corr=corr,lo=lo,hi=hi)

# ---------- MMStar, k from source TSV (independent route) ----------
with open(R+"data/vlmevalkit/MMStar_VLMEVAL.tsv", newline='', encoding='utf-8') as f:
    tsv={str(r['index']): r for r in csv.DictReader(f, delimiter='\t')}
tsvk={i:[c for c in "ABCD" if str(r.get(c) or "").strip() not in ("","nan","None")] for i,r in tsv.items()}

MM={"3B":("experiments/runs/vlmevalkit_mmstar3b_adapted_an29_20260710T004416Z/postprocessed_v2/rows.jsonl",
          "experiments/runs/layer1_blind_mmstar3b_an29_20260710T023019Z/predictions.jsonl"),
    "7B":("experiments/runs/vlmevalkit_mmstar7b_adapted_an29_20260710T005355Z/postprocessed_v2/rows.jsonl",
          "experiments/runs/layer1_blind_mmstar7b_an29_20260710T023019Z/predictions.jsonl")}
print("="*40,"MMStar (k from SOURCE TSV, not option_labels)")
for m,(wp,bp) in MM.items():
    W={r['index']:r for r in load(wp)}; B={r['index']:r for r in load(bp)}
    print(m,"n_with",len(W),"n_blind",len(B),"ids equal:",set(W)==set(B))
    items=[]
    for i in W:
        labs=tsvk[i]; k=len(labs); gold=str(tsv[i]['answer']).strip()
        gi = gold in labs
        items.append(dict(i=i,k=k,gi=gi,nul=(1.0/k if (k>0 and gi) else 0.0),
                          w=bool(W[i]['acc_final']),b=bool(B[i]['acc_final']),
                          ws=bool(W[i]['acc_strict']),bs=bool(B[i]['acc_strict'])))
    for k in sorted({it['k'] for it in items if it['gi']}):
        summ("MMStar %s k=%d"%(m,k),[it for it in items if it['k']==k and it['gi']])
    summ("MMStar %s pooled ALL"%m, items)
    # gold-not-in-options subgroup
    deg=[it for it in items if not it['gi']]
    print("   deg n=%d  with_sum=%d blind_sum=%d"%(len(deg),sum(i['w'] for i in deg),sum(i['b'] for i in deg)))
    # strict pooled
    st=[dict(w=it['ws'],b=it['bs'],nul=it['nul']) for it in items]
    summ("MMStar %s pooled ALL [STRICT]"%m, st)
