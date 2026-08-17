import json, collections
from pathlib import Path
R=Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
TS="20260730T011842Z"
rank={"cp":R/f"experiments/runs/mini_a5_s1_ranking_cp_step120_real_an29_gpu4_{TS}/scores.jsonl",
      "member":R/f"experiments/runs/mini_a5_s1_ranking_member_step120_real_an29_gpu5_{TS}/scores.jsonl"}
gen={"cp":R/"experiments/runs/mini_a5_f8_r19_cp_step120_real_an29_20260730T004031Z/shards",
     "member":R/"experiments/runs/mini_a5_f8_r19_member_step120_real_an29_20260730T004031Z/shards"}
for arm,p in rank.items():
    rows=[json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    print(arm,"ranking rows",len(rows),"steps",set(r["global_step"] for r in rows),
          "cond",set(r["condition"] for r in rows),"mk",set(r["model_key"] for r in rows),
          "cand_counts",sorted(set(r["candidate_count"] for r in rows)))
    c=collections.Counter(r["template_id"] for r in rows)
    for t in sorted(c):
        sub=[r for r in rows if r["template_id"]==t]
        ps=sum(1 for r in sub if r["pair_success"]); t1=sum(1 for r in sub if r["candidate_pair_top1"])
        # recompute pair_success from margins independently
        ps2=sum(1 for r in sub if r["margin_a"]>0 and r["margin_b"]>0)
        print(f"   {t:<42} n={len(sub)} pair_success={ps}/{len(sub)}={ps/len(sub):.4f} (recomputed_from_margins={ps2}) top1={t1}/{len(sub)}={t1/len(sub):.4f}")
for arm,d in gen.items():
    rows=[]
    for s in sorted(d.glob("shard_*.jsonl")):
        rows+= [json.loads(l) for l in s.read_text().splitlines() if l.strip()]
    print(arm,"gen rows",len(rows),"uniq pair_id",len(set(r["pair_id"] for r in rows)))
    for t in sorted(set(r["template_id"] for r in rows)):
        sub=[r for r in rows if r["template_id"]==t]
        pc=sum(1 for r in sub if r["pair_correct"]); sc=sum(1 for r in sub if r["strict_pair_correct"])
        print(f"   {t:<42} n={len(sub)} pair_correct={pc}/{len(sub)}={pc/len(sub):.4f} strict={sc}/{len(sub)}={sc/len(sub):.4f}")
