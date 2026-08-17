import json, csv, collections, sys
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
def summ(tag,items,key=('w','b')):
    w=np.array([i[key[0]] for i in items],float); b=np.array([i[key[1]] for i in items],float); nu=np.array([i['nul'] for i in items],float)
    mw,mb,mn=w.mean(),b.mean(),nu.mean(); den=mw-mn
    corr=(mb-mn)/den if den!=0 else float('nan'); naive=mb/mw if mw!=0 else float('nan')
    lo,hi=boot(w,b,nu)
    print("%-52s n=%-5d with=%.4f blind=%.4f null=%.4f naive=%.4f corr=%.4f CI=[%.4f,%.4f]"%(tag,len(items),mw,mb,mn,naive,corr,lo,hi))

# --- MathVista: independent route -> derive MC/k from the source TSV, not option_labels/question_type ---
with open(R+"data/vlmevalkit/MathVista_LOCAL.tsv", newline='', encoding='utf-8') as f:
    rd=csv.DictReader(f, delimiter='\t'); print("MathVista TSV cols:", rd.fieldnames)
    mvt={str(r['index']): r for r in rd}
print("MathVista TSV n:", len(mvt))
sample=list(mvt.items())[0]
print("sample row keys/vals:", {k:(str(v)[:80]) for k,v in sample[1].items()})
