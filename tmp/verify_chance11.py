import csv, sys, collections, hashlib, os, json
csv.field_size_limit(sys.maxsize)
R="/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/"
with open(R+"data/vlmevalkit/MMStar_VLMEVAL.tsv", newline='', encoding='utf-8') as f:
    rows=list(csv.DictReader(f, delimiter='\t'))
defs={
 "strip, exclude '' 'nan' 'None'": lambda v: str(v or "").strip() not in ("","nan","None"),
 "strip, exclude '' only":         lambda v: str(v or "").strip()!="",
 "not None and not ''":            lambda v: v is not None and v!="",
 "pandas-like isna (nan/NaN/NA)":  lambda v: str(v or "").strip().lower() not in ("","nan","none","na","<na>"),
}
for name,f_ in defs.items():
    c=collections.Counter("".join(x for x in "ABCD" if f_(r.get(x))) for r in rows)
    print("%-34s %s" % (name, dict(c)))
print()
print("=== sha256 provenance verification ===")
md=open(R+"reports/chance_corrected_retention_v1.md").read()
import re
bad=0; n=0
for m in re.finditer(r'^\| `(experiments/runs/[^`]+)` \| (\d+) \| `([0-9a-f]{64})` \|$', md, re.M):
    p,b,h=m.group(1),int(m.group(2)),m.group(3)
    ap=R+p
    if not os.path.exists(ap): print("MISSING", p); bad+=1; continue
    sz=os.path.getsize(ap)
    hh=hashlib.sha256(open(ap,'rb').read()).hexdigest()
    n+=1
    if sz!=b or hh!=h:
        print("MISMATCH", p, "size", sz, "vs", b, "sha ok" if hh==h else "SHA DIFF"); bad+=1
print("checked %d provenance rows, %d bad"%(n,bad))
