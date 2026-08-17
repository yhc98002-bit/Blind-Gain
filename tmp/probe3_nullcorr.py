import json, os, csv, collections
R="/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"
def load(p):
    return [json.loads(l) for l in open(p) if l.strip()]
csv.field_size_limit(10**9)
tsv=os.path.join(R,"data/vlmevalkit/MMStar_VLMEVAL.tsv")
src={}
with open(tsv,newline='') as f:
    for r in csv.DictReader(f,delimiter='\t'): src[r['index']]=r

for tag,wp,bp in [("3B","experiments/runs/vlmevalkit_mmstar3b_adapted_an29_20260710T004416Z/postprocessed_v2/rows.jsonl","experiments/runs/layer1_blind_mmstar3b_an29_20260710T023019Z/predictions.jsonl"),
                  ("7B","experiments/runs/vlmevalkit_mmstar7b_adapted_an29_20260710T005355Z/postprocessed_v2/rows.jsonl","experiments/runs/layer1_blind_mmstar7b_an29_20260710T023019Z/predictions.jsonl")]:
    W={r['index']:r for r in load(os.path.join(R,wp))}
    B={r['index']:r for r in load(os.path.join(R,bp))}
    grp=collections.defaultdict(lambda: [0,0,0,0,0])  # n, w_final, b_final, w_strict, b_strict
    goldin=collections.Counter()
    for i,b in B.items():
        labs=b.get('option_labels') or []
        k=len(labs)
        gin = b['gold'] in labs
        key=(k,gin)
        g=grp[key]; g[0]+=1; g[1]+=W[i]['acc_final']; g[2]+=b['acc_final']; g[3]+=W[i]['acc_strict']; g[4]+=b['acc_strict']
    print("---",tag)
    for key in sorted(grp):
        n,wf,bf,ws,bs=grp[key]
        print("  k=%s gold_in_options=%s n=%4d  with_final=%.4f blind_final=%.4f with_strict=%.4f blind_strict=%.4f"%(key[0],key[1],n,wf/n,bf/n,ws/n,bs/n))
# how many source rows have non-nan A..D
cnt=collections.Counter()
for i,r in src.items():
    present=tuple(L for L in "ABCD" if str(r.get(L,'nan')).strip().lower() not in ('nan','','none'))
    cnt[present]+=1
print("source option-presence patterns:", dict(cnt))
# for the pattern BCD, check answer col
bad=[i for i,r in src.items() if str(r.get('A','nan')).strip().lower()=='nan' and str(r.get('B','nan')).strip().lower()!='nan']
print("n rows with A=nan but B present:", len(bad), "answers:", collections.Counter(src[i]['answer'] for i in bad))
