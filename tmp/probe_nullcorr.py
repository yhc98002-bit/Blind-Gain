import json, re, collections, os
R = "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"

def load(p):
    out = []
    with open(p) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out

pairs = {
 "mmstar3b": ("experiments/runs/vlmevalkit_mmstar3b_adapted_an29_20260710T004416Z/postprocessed_v2/rows.jsonl",
              "experiments/runs/layer1_blind_mmstar3b_an29_20260710T023019Z/predictions.jsonl"),
 "mmstar7b": ("experiments/runs/vlmevalkit_mmstar7b_adapted_an29_20260710T005355Z/postprocessed_v2/rows.jsonl",
              "experiments/runs/layer1_blind_mmstar7b_an29_20260710T023019Z/predictions.jsonl"),
 "mathvista3b": ("experiments/runs/vlmevalkit_postprocess_mathvista3b_20260710T022024Z/rows.jsonl",
              "experiments/runs/layer1_blind_mathvista3b_an29_20260710T023019Z/predictions.jsonl"),
 "mathvista7b": ("experiments/runs/vlmevalkit_postprocess_mathvista7b_20260710T022024Z/rows.jsonl",
              "experiments/runs/layer1_blind_mathvista7b_an29_20260710T023019Z/predictions.jsonl"),
}
for k,(a,b) in pairs.items():
    pa, pb = os.path.join(R,a), os.path.join(R,b)
    if not os.path.exists(pa): print(k, "MISSING withimage", pa); continue
    if not os.path.exists(pb): print(k, "MISSING blind", pb); continue
    A, B = load(pa), load(pb)
    ia = [r["index"] for r in A]; ib = [r["index"] for r in B]
    sa, sb = set(ia), set(ib)
    print(k, "n_with=%d n_blind=%d uniq_a=%d uniq_b=%d inter=%d onlyA=%d onlyB=%d"%(
        len(A),len(B),len(sa),len(sb),len(sa&sb),len(sa-sb),len(sb-sa)))
    # option label agreement
    da = {r["index"]: r for r in A}; db = {r["index"]: r for r in B}
    dis = 0
    for i in (sa&sb):
        if len(da[i].get("option_labels") or []) != len(db[i].get("option_labels") or []): dis += 1
    print("   option_label length disagreements:", dis)
    print("   sample onlyA:", sorted(sa-sb)[:5], "onlyB:", sorted(sb-sa)[:5])
    print("   A keys:", sorted(A[0].keys()))
    ktab = collections.Counter(len(r.get("option_labels") or []) for r in B)
    print("   blind k dist:", dict(sorted(ktab.items())))
