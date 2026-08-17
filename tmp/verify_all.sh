#!/bin/bash
export PATH=$HOME/.local/bin:$PATH
R=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd $R
echo "############ UTC $(date -u +%Y-%m-%dT%H:%M:%SZ)  HEAD=$(git rev-parse --short HEAD)"
echo
echo "===== LIVE TRAINERS PER NODE ====="
for N in an12 an29; do
  echo "--- $N"
  ssh -o ConnectTimeout=20 $N 'ps -eo pid,etime,args | grep -E "verl.trainer.mai[n]" | sed -E "s#.*experiments/runs/([^/]+)/.*#PID_ETIME_RUN: \1#"' 2>&1
  ssh -o ConnectTimeout=20 $N 'ps -eo pid,etime,args | grep -E "verl.trainer.mai[n]" | awk "{print \$1, \$2}"' 2>&1
  ssh -o ConnectTimeout=20 $N 'nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader' 2>&1
done
echo
echo "===== EACH LIVE M7 ARM: manifest + deviations + progress ====="
for d in experiments/runs/m7_virl_a2_gray_seed1_an12_20260730T121803Z \
         experiments/runs/m7_virl_a2b_noimage_seed1_an29_20260730T121834Z \
         experiments/runs/m7_virl_a3_caption_seed1_an12_20260730T131311Z; do
  echo "======================================================="
  echo "RUN DIR: $d"
  jq -r '"run_id      : \(.run_id)\nnode        : \(.node)\ngpu_ids     : \(.gpu_ids|tostring)\nstatus      : \(.status)\ngit_hash    : \(.git_hash)\nstart_utc   : \(.start_time_utc)\nconfig      : \(.config_path)\nckpt_path   : \(.checkpoint_path)"' $d/run_manifest.json
  echo "PID file: $(cat $d/pids/*.pid 2>/dev/null)"
  echo "--- deviations field VERBATIM:"
  jq '.deviations' $d/run_manifest.json
  echo "--- reward_shadow.jsonl:"
  ls -la --time-style=+%H:%M:%SZ $d/reward_shadow.jsonl 2>/dev/null || echo "  (none yet)"
  echo "--- OOM/traceback grep in log:"
  grep -ciE "OutOfMemoryError|Traceback" $d/logs/*.log 2>/dev/null | tail -2
  echo "--- log tail:"
  tail -c 400 $d/logs/*.log 2>/dev/null | tr '\r' '\n' | grep -vE "^\s*$" | tail -2
done
echo
echo "===== ARM1 (finished) FINAL STATE, untouched ====="
jq -r '"run_id \(.run_id)  status \(.status)  end \(.end_time_utc)"' experiments/runs/m7_virl_a1_real_seed1_an12_20260728T102036Z/run_manifest.json
cat checkpoints/m7/m7_virl_a1_real_seed1/checkpoint_tracker.json
