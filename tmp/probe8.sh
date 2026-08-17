#!/bin/bash
R=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd $R
python3 - <<'PY'
import json
p="checkpoints/m7/m7_virl_a1_real_seed1/experiment_log.jsonl"
rows=[json.loads(l) for l in open(p) if l.strip()]
steps=[r.get("step") for r in rows]
print("n rows:",len(rows),"first step:",steps[0],"last step:",steps[-1])
print("timing_s keys sample:", sorted(rows[-1].get("timing_s",{}).keys()))
tot=[r.get("timing_s",{}).get("step") for r in rows]
print("per-step 'step' seconds, last 12:", [None if t is None else round(t,1) for t in tot[-12:]])
import statistics
vals=[t for t in tot if isinstance(t,(int,float))]
if vals:
    print("count",len(vals),"mean_s",round(statistics.mean(vals),1),"median_s",round(statistics.median(vals),1))
    print("mean_min",round(statistics.mean(vals)/60,2),"median_min",round(statistics.median(vals)/60,2))
    print("last10 mean_min",round(statistics.mean(vals[-10:])/60,2))
    print("first10 mean_min",round(statistics.mean(vals[:10])/60,2))
    print("sum_hours",round(sum(vals)/3600,2))
PY
echo
echo "=== file mtime of experiment_log.jsonl (UTC) and now ==="
date -u -r checkpoints/m7/m7_virl_a1_real_seed1/experiment_log.jsonl +%Y-%m-%dT%H:%M:%SZ
date -u +%Y-%m-%dT%H:%M:%SZ
echo
echo "=== eval progress re-check ==="
for d in experiments/runs/m5c_sampled_m5c-taskb-step400_an29_gpu4_20260730T122620Z experiments/runs/m5c_sampled_m5c-taskb-step100-repro_an29_gpu5_20260730T122701Z; do
  echo "$(basename $d): $(tail -1 $d/logs/*.log)"
done
