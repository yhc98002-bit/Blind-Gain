#!/usr/bin/env bash
# Verification probe for M7 launcher fixes. Starts NO training.
export PATH=$HOME/.local/bin:$PATH
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
PY="$ROOT/.venv/bin/python"

echo "===== HOST ====="
hostname
echo "===== GIT ====="
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
echo "-- unpushed vs origin/agent/gate2-recovery:"
git log --oneline origin/agent/gate2-recovery..HEAD | cat
echo "-- unpushed vs origin/master:"
git log --oneline origin/master..HEAD | cat
echo "-- byte-clean check on CRITICAL M7 files:"
git diff --stat HEAD -- scripts/launch_m7_virl_arm.sh scripts/m7_gpu_occupancy_guard.py scripts/build_m7_configs.py docs/registered_m7_seed_scope_v1.md | cat
echo "(empty above = byte-clean at HEAD)"

echo
echo "===== 1. bash -n ====="
bash -n scripts/launch_m7_virl_arm.sh && echo "bash -n: CLEAN"
"$PY" -c 'import py_compile,sys; py_compile.compile("scripts/m7_gpu_occupancy_guard.py", doraise=True); print("py_compile: CLEAN")'

echo
echo "===== 3a. ARM 1 LIVE STATE (before probes) ====="
ssh -o ConnectTimeout=25 an12 "pgrep -a -f 'verl.trainer.mai[n]'" 2>&1 | sed 's/^/  /'
echo "-- arm1 manifest gpu_ids / node:"
for m in experiments/runs/m7_virl_a1_real_seed1*/run_manifest.json; do
  echo "  $m"
  jq -c '{run_id,node,gpu_ids,status,deviations}' "$m" 2>&1 | sed 's/^/    /'
done
