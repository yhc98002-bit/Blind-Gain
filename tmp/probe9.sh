#!/bin/bash
export PATH=$HOME/.local/bin:$PATH
R=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd $R
echo "=== arm1: step 100 checkpoint + process state ==="
ls -la checkpoints/m7/m7_virl_a1_real_seed1/
cat checkpoints/m7/m7_virl_a1_real_seed1/checkpoint_tracker.json
echo
echo "=== arm1 log tail (completion?) ==="
tail -c 1500 experiments/runs/m7_virl_a1_real_seed1_an12_20260728T102036Z/logs/an12.log | tr '\r' '\n' | tail -10
echo
echo "=== how are manifest statuses set? grep for status writes ==="
grep -rn '"status"' scripts/launch_m7_virl_arm.sh | head -20
echo "--- any completion/failure updater scripts:"
ls -1 scripts/ | grep -iE "manifest|status|finali|reap" | head -20
echo
echo "=== full manifest of dead arm4 ==="
jq . experiments/runs/m7_virl_a3_caption_seed1_an29_20260730T121906Z/run_manifest.json
