#!/usr/bin/env bash
# M7 seed-2 step-100 held-out eval launcher: merge-if-needed + GPU-scope guard
# + reservation claim + the registered ViRL eval recipe (mirrors eval_launch()
# in scripts/m7_completion_chain.sh, seed-2 checkpoint paths).
# Usage: launch_m7_seed2_eval.sh ARM COND NODE GPU
#   ARM  ∈ {a1_real, a2_gray, a2b_noimage, a3_caption}
#   COND ∈ {real, gray, none, caption} (matched condition for the arm)
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
PY=.venv/bin/python
LOG="$ROOT/logs/m7_seed2_evals.log"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }
CLAIMS_DIR=/dev/shm/blind-gains/gpu_claims

[[ $# -eq 4 ]] || { echo "Usage: $0 ARM COND NODE GPU" >&2; exit 2; }
ARM="$1"; COND="$2"; NODE="$3"; GPU="$4"
LABEL="m7_seed2_${ARM}_step100_eval"
ACTOR_REL="checkpoints/m7/m7_virl_${ARM}_seed2/global_step_100/actor"
HF="$ROOT/$ACTOR_REL/huggingface"
IDX="$HF/model.safetensors.index.json"

log "[$ARM] seed-2 eval request: cond=$COND node=$NODE gpu=$GPU"

# 1) merge if needed (merge launcher requires the repo-relative actor path)
if [[ ! -f "$IDX" ]]; then
  log "[$ARM] merging FSDP -> HF on $NODE"
  mout=$(bash scripts/launch_easyr1_checkpoint_merge.sh "$NODE" "$ACTOR_REL" "m7_${ARM}_seed2_step100" 2>&1 | tail -1)
  log "[$ARM] merge launcher -> $mout"
  for i in $(seq 1 40); do sleep 30; [[ -f "$IDX" ]] && break; done
  [[ -f "$IDX" ]] || { log "[$ARM] merge produced no index in 20 min; abort"; exit 1; }
  sleep 30
fi
pin=$($PY -c "import json; d=json.load(open('$IDX')); print(d['metadata']['total_size'], len(d['weight_map']))" 2>/dev/null)
[[ "$pin" == "8131575808 825" ]] || { log "[$ARM] merged index pin mismatch ($pin); abort"; exit 1; }
log "[$ARM] merged HF verified ($pin)"

# 2) guard -> claim -> re-check (TOCTOU discipline)
"$PY" scripts/m7_gpu_occupancy_guard.py --node "$NODE" --gpus "$GPU" >> "$LOG" 2>&1 \
  || { log "[$ARM] guard denied $NODE:$GPU; abort"; exit 1; }
payload=$(jq -nc --argjson gpu "$GPU" --arg run_id "$LABEL" --argjson pid null \
  --arg dir "" --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{gpu:$gpu, run_id:$run_id, pid:$pid, eval_run_dir:$dir, written_utc:$ts,
    written_by:"scripts/launch_m7_seed2_eval.sh"}')
printf '%s\n' "$payload" | ssh -o BatchMode=yes -o ConnectTimeout=25 "$NODE" \
  "mkdir -p '$CLAIMS_DIR' && cat > '$CLAIMS_DIR/${NODE}_gpu${GPU}.claim'" \
  || { log "[$ARM] claim write failed; abort"; exit 1; }
"$PY" scripts/m7_gpu_occupancy_guard.py --node "$NODE" --gpus "$GPU" \
  --ignore-claim-run-id "$LABEL" >> "$LOG" 2>&1 \
  || { ssh -o ConnectTimeout=25 "$NODE" "rm -f '$CLAIMS_DIR/${NODE}_gpu${GPU}.claim'"; log "[$ARM] post-claim re-check denied; abort"; exit 1; }

# 3) launch the registered eval recipe
caption_env=""
[[ "$COND" == caption ]] && caption_env="data/virl39k_caption_store_3b_main_v2.jsonl"
out=$(VIRL_MANIFEST=data/virl39k_m7_heldout_v3_eval.jsonl \
      VIRL_SAMPLE_SPEC=reports/virl39k_m7_heldout_v3_sample.json \
      VIRL_SPLITS=train \
      VIRL_MODEL_PATH="checkpoints/m7/m7_virl_${ARM}_seed2/global_step_100/actor/huggingface" \
      VIRL_MODEL_REVISION="m7_virl_${ARM}_seed2@global_step_100" \
      VIRL_RUN_PREFIX=m7_step100_heldout_seed2 \
      VIRL_JOB_TYPE=r3_m7_step100_heldout_arm_eval \
      ${caption_env:+VIRL_CAPTION_SHARDS="$caption_env"} \
      bash scripts/launch_virl39k_blind_v1_condition.sh "$NODE" "$GPU" "$COND" "${ARM}_seed2" 2>>"$LOG")
rc=$?
run_dir=$(printf '%s\n' "$out" | tail -1)
log "[$ARM] eval launcher rc=$rc run_dir=$run_dir"
if [[ $rc -ne 0 || -z "$run_dir" || ! -f "$run_dir/run_manifest.json" ]]; then
  ssh -o ConnectTimeout=25 "$NODE" "rm -f '$CLAIMS_DIR/${NODE}_gpu${GPU}.claim'"
  log "[$ARM] eval launch failed; claim released; abort"
  exit 1
fi

# 4) stamp the runner pid into the claim so it holds past the 30-min expiry
pid=$(head -1 "$run_dir/pids/"*.pid 2>/dev/null || true)
payload=$(jq -nc --argjson gpu "$GPU" --arg run_id "$LABEL" --argjson pid "${pid:-null}" \
  --arg dir "$run_dir" --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{gpu:$gpu, run_id:$run_id, pid:$pid, eval_run_dir:$dir, written_utc:$ts,
    written_by:"scripts/launch_m7_seed2_eval.sh"}')
printf '%s\n' "$payload" | ssh -o BatchMode=yes -o ConnectTimeout=25 "$NODE" \
  "cat > '$CLAIMS_DIR/${NODE}_gpu${GPU}.claim'" || true
log "[$ARM] eval running: $run_dir"
echo "$run_dir"
