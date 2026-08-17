#!/bin/bash
export PATH=$HOME/.local/bin:$PATH
R=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
echo "=== newest m7 run dirs ==="
ls -1dt $R/experiments/runs/m7_* 2>/dev/null | head -10
echo
for d in $(ls -1dt $R/experiments/runs/m7_* 2>/dev/null | head -6); do
  echo "===== $d"
  m=$d/run_manifest.json
  if [ -f "$m" ]; then
    jq '{run_id,node,gpu_ids,status,git_commit,started_at,deviations}' "$m" 2>&1
  else echo "NO MANIFEST"; fi
  echo "-- files:"; ls -la $d | head -25
done
