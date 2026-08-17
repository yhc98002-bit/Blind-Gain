import json, itertools, collections
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
src = ROOT/"experiments/runs/blind_solvability_v2_anchor_step100_geo3k_guarded_real_an12_20260712T053344Z/per_item.jsonl"
res = ROOT/"experiments/runs/blind_solvability_v2_guarded_rescore_anchor_step100_geo3k_real_login_20260712T082107Z/per_item.jsonl"

def load(p):
    return [json.loads(l) for l in p.open()]

S = load(src); R = load(res)
print("n_src", len(S), "n_res", len(R))
# split order
order = [r["split"] for r in S]
runs = [(k, len(list(g))) for k,g in itertools.groupby(order)]
print("split run-length order (src):", runs)
runs_r = [(k, len(list(g))) for k,g in itertools.groupby([r["split"] for r in R])]
print("split run-length order (rescore):", runs_r)

# identity alignment
print("identity aligned:", all((a["split"],a["row_index"])==(b["split"],b["row_index"]) for a,b in zip(S,R)))

# compare sampled_canonical_correct + greedy_canonical_correct on test rows
diff_sample=0; diff_greedy=0; ntest=0
for a,b in zip(S,R):
    if a["split"]!="test": continue
    ntest+=1
    if a["sampled_canonical_correct"]!=b["sampled_canonical_correct"]: diff_sample+=1
    if a["greedy_canonical_correct"]!=b["greedy_canonical_correct"]: diff_greedy+=1
print("test rows:", ntest, "rows where sampled_canonical_correct differs src vs rescore:", diff_sample,
      "greedy_canonical_correct differs:", diff_greedy)

# also responses identical?
same_resp = all(a["sampled_responses"]==b["sampled_responses"] for a,b in zip(S,R))
print("sampled_responses identical src vs rescore:", same_resp)

# what fields exist relevant to correctness
r0 = R[0]
for k in ["greedy_correct","greedy_canonical_correct","greedy_acc_strict","sample_correct","sampled_canonical_correct","sample_correct_count","canonical_sample_correct_count","p_sample","canonical_p_sample","p_i_jeffreys","sample_count","greedy_contract_valid"]:
    v = r0.get(k, "<absent>")
    print(" field", k, "=", (v if not isinstance(v,list) else v))
