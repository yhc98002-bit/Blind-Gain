#!/bin/bash
export PATH=$HOME/.local/bin:$PATH
R=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
A4=$R/experiments/runs/m7_virl_a3_caption_seed1_an29_20260730T121906Z
echo "=== ARM4 logs dir ==="
ls -la $A4/logs $A4/pids
echo
echo "=== ARM4 log tail (OOM evidence) ==="
for f in $A4/logs/*; do echo "----- $f  ($(wc -l < $f) lines)"; tail -40 "$f"; done
echo
echo "=== ARM4 OOM grep ==="
grep -n -iE "out of memory|OutOfMemoryError|CUDA error|Traceback" $A4/logs/* | head -20
