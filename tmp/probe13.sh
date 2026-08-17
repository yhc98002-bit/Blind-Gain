#!/bin/bash
R=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd $R
python3 - <<'PY'
import json
for name,label in [("m7_virl_a1_real_seed1","arm1 a1_real (SOLO node, reference)"),
                   ("m7_virl_a2_gray_seed1","arm2 a2_gray (colocated an12)"),
                   ("m7_virl_a2b_noimage_seed1","arm3 a2b_noimage (colocated an29)")]:
    p="checkpoints/m7/%s/experiment_log.jsonl"%name
    try: rows=[json.loads(l) for l in open(p) if l.strip()]
    except FileNotFoundError: print(label,": no log"); continue
    print("=== %s  rows=%d"%(label,len(rows)))
    for r in rows[:2]:
        t=r.get("timing_s",{})
        print("   step=%s step_s=%.1f (=%.2f min)  gen=%.1f old=%.1f ref=%.1f adv=%.1f update_actor=%.1f val=%.1f save=%.1f"%(
            r.get("step"), t.get("step",0), t.get("step",0)/60, t.get("gen",0), t.get("old",0),
            t.get("ref",0), t.get("adv",0), t.get("update_actor",0), t.get("validation",0), t.get("save_checkpoint",0)))
    if len(rows)>2:
        print("   (arm1 step0 for comparison already shown)")
PY
echo
echo "=== eval on GPU4 progress ==="
date -u +%H:%M:%SZ
tail -1 experiments/runs/m5c_sampled_m5c-taskb-step400_an29_gpu4_20260730T122620Z/logs/*.log
