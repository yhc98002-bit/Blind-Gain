#!/bin/bash
export PATH=$HOME/.local/bin:$PATH
R=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd $R
echo "=== arm1 experiment_log.jsonl: per-step wallclock ==="
python3 - <<'PY'
import json,datetime
p="checkpoints/m7/m7_virl_a1_real_seed1/experiment_log.jsonl"
rows=[]
for line in open(p):
    line=line.strip()
    if not line: continue
    try: d=json.loads(line)
    except Exception: continue
    rows.append(d)
print("rows:",len(rows))
if rows:
    print("keys of last row:", sorted(rows[-1].keys())[:25])
    for d in rows[-6:]:
        print({k:v for k,v in d.items() if k in ("step","global_step","timestamp","time","wallclock","epoch")})
PY
echo
echo "=== arm1 checkpoint dir mtimes (UTC) + sizes ==="
for s in 20 40 60 80; do
  d=checkpoints/m7/m7_virl_a1_real_seed1/global_step_$s
  echo "$s : $(date -u -r $d +%Y-%m-%dT%H:%M:%SZ) : $(du -sh $d | cut -f1)"
done
echo
echo "=== arm1 checkpoint_tracker.json ==="
cat checkpoints/m7/m7_virl_a1_real_seed1/checkpoint_tracker.json
echo
echo "=== configs: total_episodes / save_freq / n_gpus for all four arms ==="
for a in a1_real a2_gray a2b_noimage a3_caption; do
  echo "--- $a"
  python3 -c "
import yaml
c=yaml.safe_load(open('configs/train/m7_virl_${a}_seed1_3b.yaml'))
t=c['trainer']
print(' n_gpus_per_node',t.get('n_gpus_per_node'),'save_freq',t.get('save_freq'),'total_epochs',t.get('total_epochs'),'save_model_only',t.get('save_model_only'),'max_steps',t.get('max_steps'))
print(' save_checkpoint_path',t.get('save_checkpoint_path'))
"
done
