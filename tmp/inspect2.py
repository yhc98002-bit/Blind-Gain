import json
from pathlib import Path
ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
res = ROOT/"experiments/runs/blind_solvability_v2_guarded_rescore_anchor_step100_geo3k_real_login_20260712T082107Z/per_item.jsonl"
s400 = ROOT/"experiments/runs/m5_geo3k_step400_an12_gpu0_20260728T053115Z/per_item.jsonl"
R=[json.loads(l) for l in res.open() if json.loads(l)["split"]=="test"]
F=[json.loads(l) for l in s400.open()]
print("n test step100:", len(R), "n step400 rows:", len(F))
print("--- step400 row 0 fields ---")
r=F[0]
for k,v in sorted(r.items()):
    sv=str(v)
    print(" ", k, "=", sv[:160])
print("--- step100 counts of candidate correctness fields ---")
for k in ["greedy_correct","greedy_canonical_correct","greedy_acc_strict"]:
    print(" ", k, sum(1 for x in R if x.get(k)))
print("--- step400 counts ---")
for k in sorted(F[0].keys()):
    v=F[0][k]
    if isinstance(v,bool):
        print(" ", k, sum(1 for x in F if x.get(k)))
