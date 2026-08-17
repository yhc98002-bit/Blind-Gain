#!/usr/bin/env bash
# HB P2.3 caption-stress chain (run detached on a login node from an
# IMMUTABLE copy). Stages are artifact-gated — no pgrep anywhere:
#   S1 wait for the 72B ephemeral checkout (model_checkout.json status=pass)
#   S2 build caption-stress QA inputs (idempotent via its report file)
#   S3 launch the question-blind 72B caption store (an29 GPUs 0-3, TP4)
#   S4 wait for captions.jsonl
#   S5 build caption-QA pairs per family
#   S6 base-3B text QA over caption pairs (an29 gpu0, guard + claim)
#   S7 caption-stress readout
# Usage: hier_caption_stress_chain.sh DOWNLOAD_RUN_DIR
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
PY=.venv/bin/python

[[ $# -eq 1 ]] || { echo "Usage: $0 DOWNLOAD_RUN_DIR" >&2; exit 2; }
DOWNLOAD_RUN="$1"
MODEL_PATH=/dev/shm/blind-gains/models/Qwen2.5-VL-72B-Instruct
NODE=an29
QA_GPU=0
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="$ROOT/logs/hier_caption_stress_chain_${STAMP}.log"
CLAIMS=/dev/shm/blind-gains/gpu_claims
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }
log "chain start download_run=$DOWNLOAD_RUN"

# S1 — checkout pass (poll 60 s, ceiling 6 h)
deadline=$((SECONDS + 21600))
until jq -e '.status == "pass"' "$DOWNLOAD_RUN/model_checkout.json" >/dev/null 2>&1; do
  if jq -e '.status == "failed"' "$DOWNLOAD_RUN/run_manifest.json" >/dev/null 2>&1; then
    log "S1 DOWNLOAD FAILED"; exit 1
  fi
  [[ $SECONDS -gt $deadline ]] && { log "S1 TIMEOUT"; exit 1; }
  sleep 60
done
log "S1 checkout pass ($(jq -r '.total_bytes' "$DOWNLOAD_RUN/model_checkout.json") bytes)"

# S2 — QA inputs (skip if already built)
if [[ ! -f reports/hier_caption_stress_inputs_v1.json ]]; then
  "$PY" scripts/build_hier_caption_stress_inputs.py >> "$LOG" 2>&1 \
    || { log "S2 FAILED"; exit 1; }
fi
log "S2 inputs ready"

# S3 — caption store launch (self-detaching launcher prints the run dir)
CAP_RUN=$(bash scripts/launch_strong_caption_72b.sh "$NODE" 0,1,2,3 \
  "$DOWNLOAD_RUN" "$MODEL_PATH" Qwen/Qwen2.5-VL-72B-Instruct master \
  data/hier_v1_dev/caption_stress_hier_coord_v1/images \
  data/hier_v1_dev/caption_stress_hier_chart_v1/images \
  hier_v1_l3 2>>"$LOG" | tail -1)
[[ -d $CAP_RUN ]] || { log "S3 LAUNCH FAILED: $CAP_RUN"; exit 1; }
log "S3 caption store launched: $CAP_RUN"

# S4 — captions.jsonl (poll 120 s, ceiling 12 h)
deadline=$((SECONDS + 43200))
while [[ ! -s $CAP_RUN/captions.jsonl ]]; do
  if jq -e '.status == "failed"' "$CAP_RUN/run_manifest.json" >/dev/null 2>&1; then
    log "S4 STORE FAILED"; exit 1
  fi
  [[ $SECONDS -gt $deadline ]] && { log "S4 TIMEOUT"; exit 1; }
  sleep 120
done
log "S4 captions ready: $(wc -l < "$CAP_RUN/captions.jsonl") rows"

# S5 — caption-QA pairs (store covers both families -> extra captions allowed)
for fam in hier_coord_v1 hier_chart_v1; do
  "$PY" scripts/build_caption_qa_pairs.py \
    --release-manifest "data/hier_v1_dev/caption_stress_${fam}/manifest.jsonl" \
    --key-file "data/hier_v1_dev/caption_stress_key_${fam}.jsonl" \
    --caption-store "$CAP_RUN/captions.jsonl" \
    --output "data/hier_v1_dev/caption_qa_pairs_${fam}.jsonl" \
    --summary "reports/hier_caption_qa_build_${fam}_v1.json" \
    --allow-extra-captions >> "$LOG" 2>&1 || { log "S5 $fam FAILED"; exit 1; }
done
log "S5 QA pairs built"

# S6 — wait for the store job to release its GPUs, then base-3B QA on gpu0
deadline=$((SECONDS + 7200))
until jq -e '.status == "complete"' "$CAP_RUN/run_manifest.json" >/dev/null 2>&1; do
  [[ $SECONDS -gt $deadline ]] && { log "S6 STORE NEVER FINALIZED"; exit 1; }
  sleep 60
done
"$PY" scripts/m7_gpu_occupancy_guard.py --node "$NODE" --gpus "$QA_GPU" >> "$LOG" 2>&1 \
  || { log "S6 guard denied $NODE:$QA_GPU"; exit 1; }
QA_RUN="experiments/runs/hier_caption_qa_base3b_${NODE}_gpu${QA_GPU}_${STAMP}"
mkdir -p "$QA_RUN"
payload=$(jq -nc --argjson gpu "$QA_GPU" --arg run_id "$(basename "$QA_RUN")" \
  --arg dir "$QA_RUN" --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{gpu:$gpu, run_id:$run_id, pid:null, eval_run_dir:$dir, written_utc:$ts,
    written_by:"scripts/hier_caption_stress_chain.sh"}')
printf '%s\n' "$payload" | ssh -o BatchMode=yes -o ConnectTimeout=25 "$NODE" \
  "mkdir -p '$CLAIMS' && cat > '$CLAIMS/${NODE}_gpu${QA_GPU}.claim'" \
  || { log "S6 claim write failed"; exit 1; }
jq -n --arg run_id "$(basename "$QA_RUN")" --arg node "$NODE" --argjson gpu "$QA_GPU" \
  --arg git_hash "$(git rev-parse HEAD)" --arg cap_run "$CAP_RUN" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{schema_version:"blind-gains.run-manifest.v1", run_id:$run_id,
    job_type:"hier_caption_qa_base3b", status:"running", node:$node,
    gpu_ids:[$gpu], model_key:"base3b",
    model_path:"artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct",
    caption_run:$cap_run, git_hash:$git_hash, max_new_tokens:32,
    start_time_utc:$started, end_time_utc:null, exit_code:null,
    registration:"docs/registered_hier_benchmark_v1.md §7 + A2 (P2.3)",
    deviations:[]}' > "$QA_RUN/run_manifest.json"
overall_rc=0
for fam in hier_coord_v1 hier_chart_v1; do
  log "S6 QA $fam START"
  ssh -o BatchMode=yes -o ConnectTimeout=25 "$NODE" \
    "cd '$ROOT' && source .venv/bin/activate && \
     env PYTHONUNBUFFERED=1 TRANSFORMERS_OFFLINE=1 HF_HOME=$ROOT/artifacts/hf_home \
     CUDA_VISIBLE_DEVICES=$QA_GPU PYTHONPATH=. \
     python scripts/eval_caption_qa_fliptrack.py \
       --model-path artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct \
       --input 'data/hier_v1_dev/caption_qa_pairs_${fam}.jsonl' \
       --output '$QA_RUN/${fam}_predictions.jsonl' \
       --metrics-output '$QA_RUN/${fam}_metrics.json' \
       --max-new-tokens 32" >> "$LOG" 2>&1
  rc=$?
  log "S6 QA $fam DONE rc=$rc"
  [[ $rc -ne 0 ]] && overall_rc=1
done
"$PY" scripts/finalize_run_manifest.py "$QA_RUN/run_manifest.json" "$overall_rc" \
  >> "$LOG" 2>&1 || log "S6 finalize_run_manifest failed"
ssh -o ConnectTimeout=25 "$NODE" "rm -f '$CLAIMS/${NODE}_gpu${QA_GPU}.claim'" 2>/dev/null
[[ $overall_rc -ne 0 ]] && { log "S6 FAILED"; exit 1; }

# S7 — readout
"$PY" scripts/build_hier_caption_stress_readout.py \
  --qa-run "$QA_RUN" --caption-run "$CAP_RUN" >> "$LOG" 2>&1 \
  || { log "S7 FAILED"; exit 1; }
log "CHAIN COMPLETE qa_run=$QA_RUN cap_run=$CAP_RUN"
