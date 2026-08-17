#!/usr/bin/env bash
export PATH=$HOME/.local/bin:$PATH
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
echo "=== any a2_gray run dir created? ==="
ls -1d experiments/runs/*a2_gray* 2>/dev/null || echo "NONE (guard fired before mkdir)"
echo "=== a2_gray checkpoint dir? ==="
ls -1d checkpoints/m7/* 2>/dev/null
echo "=== exact guard source (launcher lines 61-75) ==="
sed -n '61,75p' scripts/launch_m7_virl_arm.sh
echo "=== arm 1 progress (last 3 step lines) ==="
grep -oE 'step:[0-9]+' experiments/runs/m7_virl_a1_real_seed1_an12_20260728T102036Z/logs/an12.log 2>/dev/null | tail -3
tail -2 experiments/runs/m7_virl_a1_real_seed1_an12_20260728T102036Z/logs/an12.log
echo "=== arm 1 log mtime (now: $(date -u +%Y-%m-%dT%H:%M:%SZ)) ==="
stat -c '%y %n' experiments/runs/m7_virl_a1_real_seed1_an12_20260728T102036Z/logs/an12.log
