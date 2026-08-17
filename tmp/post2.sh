#!/usr/bin/env bash
export PATH=$HOME/.local/bin:$PATH
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
echo "=== m7_virl run dirs (all) ==="
ls -1dt experiments/runs/m7_virl_* 2>/dev/null
echo "=== run dirs created in the last 30 min ==="
find experiments/runs -maxdepth 1 -type d -mmin -30 2>/dev/null | head
echo "=== arm 1 step progress ==="
grep -oE '"step": [0-9]+' experiments/runs/m7_virl_a1_real_seed1_an12_20260728T102036Z/logs/an12.log 2>/dev/null | tail -2
grep -oE 'step [0-9]+' experiments/runs/m7_virl_a1_real_seed1_an12_20260728T102036Z/logs/an12.log 2>/dev/null | tail -2
echo "--- last non-progressbar line ---"
grep -av $'\r' experiments/runs/m7_virl_a1_real_seed1_an12_20260728T102036Z/logs/an12.log | grep -aE 'step|Step' | tail -3
echo "=== arm 1 checkpoints on disk ==="
ls -1 checkpoints/m7/m7_virl_a1_real_seed1/
du -sh checkpoints/m7/m7_virl_a1_real_seed1/
echo "=== arm 1 run manifest status ==="
jq -r '{run_id,status,start_time_utc,gpu_ids,config_hash}' experiments/runs/m7_virl_a1_real_seed1_an12_20260728T102036Z/run_manifest.json
