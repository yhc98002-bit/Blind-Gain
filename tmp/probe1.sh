#!/bin/bash
export PATH=$HOME/.local/bin:$PATH
R=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd $R
echo "=== git ancestry of ed4aa96 ==="
git cat-file -t ed4aa96 2>&1
git merge-base --is-ancestor ed4aa96 HEAD && echo "ed4aa96 IS ancestor of HEAD" || echo "ed4aa96 NOT ancestor of HEAD"
git log --oneline -1 ed4aa96 2>&1
echo
echo "=== branch / remote ==="
git branch --show-current
git log --oneline -1 origin/agent/gate2-recovery 2>&1
echo
echo "=== m7 run dirs (newest 20) ==="
ls -1dt $R/runs/m7_* 2>/dev/null | head -20
echo
echo "=== manifests ==="
for d in $(ls -1dt $R/runs/m7_* 2>/dev/null | head -12); do
  m=$d/run_manifest.json
  if [ -f "$m" ]; then
    echo "--- $m"
    jq -c '{run_id,node,gpu_ids,status,git_commit,started_at,deviations}' "$m" 2>&1
  else
    echo "--- $d : NO run_manifest.json"
  fi
done
