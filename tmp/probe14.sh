#!/bin/bash
export PATH=$HOME/.local/bin:$PATH
R=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd $R
echo "=== checkpoints/m7/m7_virl_a3_caption_seed1 contents ==="
ls -la --time-style=full-iso checkpoints/m7/m7_virl_a3_caption_seed1
echo
echo "=== newest a3_caption run dirs ==="
ls -1dt --time-style=full-iso experiments/runs/m7_virl_a3_caption* 2>/dev/null | head
for d in $(ls -1dt experiments/runs/m7_virl_a3_caption* 2>/dev/null | head -3); do
  echo "--- $d"; ls -la --time-style=full-iso $d
  [ -f $d/run_manifest.json ] && jq -c '{run_id,status,gpu_ids,git_hash,start_time_utc}' $d/run_manifest.json
done
echo
echo "=== git recent commits ==="
git log --oneline -6
echo "HEAD=$(git rev-parse HEAD)"
echo
echo "=== an29 processes now ==="
ssh -o ConnectTimeout=20 an29 'nvidia-smi --query-gpu=index,memory.used --format=csv,noheader; echo ---; ps -eo pid,etime,args | grep -E "verl.trainer.mai[n]" | cut -c1-190'
