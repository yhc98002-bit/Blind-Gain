#!/usr/bin/env bash
# Guarded single-GPU run of the artifact-attacker gate (now incl. the
# permanent file_size attacker) over the hier coord r2 release.
# Usage: run_hier_r2_attacker_gate.sh NODE GPU
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
PY=.venv/bin/python
[[ $# -eq 2 ]] || { echo "Usage: $0 NODE GPU" >&2; exit 2; }
NODE="$1"; GPU="$2"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="$ROOT/logs/hier_r2_attacker_gate_${NODE}_gpu${GPU}_${STAMP}.log"
CLAIMS=/dev/shm/blind-gains/gpu_claims
RUN_ID="hier_r2_attacker_gate_${STAMP}"

"$PY" scripts/m7_gpu_occupancy_guard.py --node "$NODE" --gpus "$GPU" >> "$LOG" 2>&1 \
  || { echo "guard denied" >> "$LOG"; exit 1; }
jq -nc --argjson gpu "$GPU" --arg run_id "$RUN_ID" --argjson pid null \
  --arg dir "reports" --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{gpu:$gpu, run_id:$run_id, pid:$pid, eval_run_dir:$dir, written_utc:$ts,
    written_by:"scripts/run_hier_r2_attacker_gate.sh"}' | \
  ssh -o BatchMode=yes -o ConnectTimeout=25 "$NODE" \
    "mkdir -p '$CLAIMS' && cat > '$CLAIMS/${NODE}_gpu${GPU}.claim'" \
  || { echo "claim failed" >> "$LOG"; exit 1; }
ssh -o BatchMode=yes -o ConnectTimeout=25 "$NODE" \
  "cd '$ROOT' && source .venv/bin/activate && \
   env PYTHONUNBUFFERED=1 TRANSFORMERS_OFFLINE=1 HF_HOME=$ROOT/artifacts/hf_home \
   CUDA_VISIBLE_DEVICES=$GPU PYTHONPATH=. \
   python -m src.fliptrack.artifact_attackers \
     --release-dir data/hier_v1_dev_r2/attacker_release_hier_coord_v1 \
     --key-file data/hier_v1_dev_r2/attacker_key_hier_coord_v1.jsonl \
     --output reports/hier_r2_attacker_gate_hier_coord_v1.json \
     --dinov2-model facebook/dinov2-small --batch-size 32 \
     --old-input-jsonl data/fliptrack_v01_manifest.jsonl \
     --n-splits 5 --n-bootstrap 1000 --seed 20260710" >> "$LOG" 2>&1
rc=$?
ssh -o ConnectTimeout=25 "$NODE" "rm -f '$CLAIMS/${NODE}_gpu${GPU}.claim'" 2>/dev/null
echo "attacker gate rc=$rc" >> "$LOG"
exit "$rc"
