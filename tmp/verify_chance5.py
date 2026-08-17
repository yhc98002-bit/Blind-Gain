import json, csv, collections, sys, ast
import numpy as np
csv.field_size_limit(sys.maxsize)
R="/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/"
def load(p): return [json.loads(l) for l in open(R+p) if l.strip()]
def boot(w,b,nul,reps=20000,seed=13572468):
    w=np.asarray(w,float); b=np.asarray(b,float); nul=np.asarray(nul,float); n=len(w)
    rs=np.random.RandomState(seed); idx=rs.randint(0,n,size=(reps,n))
    bw=w[idx].mean(1); bb=b[idx].mean(1); bn=nul[idx].mean(1)
    with np.errstate(divide='ignore',invalid='ignore'):
        c=np.where((bw-bn)!=0,(bb-bn)/(bw-bn),np.nan)
    c=c[np.isfinite(c)]
    return (np.percentile(c,[2.5,97.5]) if len(c)>=100 else (float('nan'),float('nan')))
def summ(tag,items,wk='w',bk='b'):
    w=np.array([i[wk] for i in items],float); b=np.array([i[bk] for i in items],float); nu=np.array([i['nul'] for i in items],float)
    mw,mb,mn=w.mean(),b.mean(),nu.mean(); den=mw-mn
    corr=(mb-mn)/den if den!=0 else float('nan'); naive=mb/mw if mw!=0 else float('nan')
    lo,hi=boot(w,b,nu)
    print("%-50s n=%-5d with=%.4f blind=%.4f null=%.4f naive=%.4f corr=%.4f CI=[%.4f,%.4f]"%(tag,len(items),mw,mb,mn,naive,corr,lo,hi))

with open(R+"data/vlmevalkit/MathVista_LOCAL.tsv", newline='', encoding='utf-8') as f:
    mvt={str(r['index']): r for r in csv.DictReader(f, delimiter='\t')}
kt={}; qt=collections.Counter()
for i,r in mvt.items():
    ch=ast.literal_eval(r['choices']) if str(r['choices']).strip() else []
    kt[i]=len(ch); qt[(r['question_type'], len(ch))]+=1
print("TSV question_type x n_choices:", dict(qt))
print("TSV k dist (MC only):", dict(collections.Counter(v for v in kt.values() if v)))
print("TSV free-form count:", sum(1 for v in kt.values() if v==0))
# duplicate-choice check
dupch=[i for i,r in mvt.items() if str(r['choices']).strip() and len(set(ast.literal_eval(r['choices'])))!=len(ast.literal_eval(r['choices']))]
print("MC items with duplicate choice TEXT:", len(dupch), dupch[:10])
# answer_type census for free-form
print("free-form answer_type:", dict(collections.Counter(mvt[i]['answer_type'] for i in mvt if kt[i]==0)))

MV={"3B":("experiments/runs/vlmevalkit_postprocess_mathvista3b_20260710T022024Z/rows.jsonl",
          "experiments/runs/layer1_blind_mathvista3b_an29_20260710T023019Z/predictions.jsonl"),
    "7B":("experiments/runs/vlmevalkit_postprocess_mathvista7b_20260710T022024Z/rows.jsonl",
          "experiments/runs/layer1_blind_mathvista7b_an29_20260710T023019Z/predictions.jsonl")}
for m,(wp,bp) in MV.items():
    W={r['index']:r for r in load(wp)}; B={r['index']:r for r in load(bp)}
    print("="*20,m,"n_with",len(W),"n_blind",len(B),"ids equal",set(W)==set(B),"ids==tsv",set(W)==set(mvt))
    items=[]
    for i in W:
        k=kt[i]
        items.append(dict(i=i,k=k,nul=(1.0/k if k else 0.0),
            w=bool(W[i]['acc_final']),b=bool(B[i]['acc_final']),ws=bool(W[i]['acc_strict']),bs=bool(B[i]['acc_strict'])))
    for k in sorted({it['k'] for it in items if it['k']}):
        sub=[it for it in items if it['k']==k]
        if len(sub)>=2: summ("MathVista %s MC k=%d"%(m,k),sub)
        else: 
            print("MathVista %s MC k=%d n=%d (too small for boot)"%(m,k,len(sub)), sub)
    summ("MathVista %s MC pooled"%m,[it for it in items if it['k']])
    summ("MathVista %s free-form"%m,[it for it in items if not it['k']])
    summ("MathVista %s WHOLE (null=0 naive ref)"%m,[dict(w=it['w'],b=it['b'],nul=0.0) for it in items])
    summ("MathVista %s MC pooled [STRICT]"%m,[dict(w=it['ws'],b=it['bs'],nul=it['nul']) for it in items if it['k']])
    summ("MathVista %s free-form [STRICT]"%m,[dict(w=it['ws'],b=it['bs'],nul=0.0) for it in items if not it['k']])
