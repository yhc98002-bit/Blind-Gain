#!/bin/bash
export PATH=$HOME/.local/bin:$PATH
R=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd $R
echo "=== arms 2/3 manifest provenance (CORRECT keys) ==="
for d in m7_virl_a2_gray_seed1_an12_20260730T121803Z m7_virl_a2b_noimage_seed1_an29_20260730T121834Z; do
  echo "--- $d"
  jq -c '{run_id,node,gpu_ids,status,git_hash,start_time_utc}' experiments/runs/$d/run_manifest.json
done
echo
echo "=== arm1 final state (DO NOT TOUCH) ==="
jq -c '{run_id,node,gpu_ids,status,git_hash,start_time_utc,deviations}' experiments/runs/m7_virl_a1_real_seed1_an12_20260728T102036Z/run_manifest.json
echo "arm1 pid alive?"; ssh -o ConnectTimeout=20 an12 'kill -0 687841 2>/dev/null && echo "687841 ALIVE" || echo "687841 GONE"'
echo
echo "=== arm1 per-step seconds: checkpoint steps vs plain steps ==="
python3 - <<'PY'
import json,statistics
rows=[json.loads(l) for l in open("checkpoints/m7/m7_virl_a1_real_seed1/experiment_log.jsonl") if l.strip()]
ck=[];pl=[]
for r in rows:
    t=r.get("timing_s",{})
    s=t.get("step")
    if s is None: continue
    (ck if t.get("save_checkpoint") else pl).append(s)
print("plain steps n=%d mean_min=%.2f median_min=%.2f"%(len(pl),statistics.mean(pl)/60,statistics.median(pl)/60))
if ck: print("checkpoint steps n=%d mean_min=%.2f  values_min=%s"%(len(ck),statistics.mean(ck)/60,[round(v/60,1) for v in ck]))
print("ALL n=%d mean_min=%.2f total_hours=%.2f"%(len(pl+ck),statistics.mean(pl+ck)/60,sum(pl+ck)/3600))
# solo vs colocated: arm2 landed on an12 at 12:18Z Jul30
PY
