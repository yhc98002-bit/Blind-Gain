#!/usr/bin/env bash
# HB P2.1 open-form sweep: one model over all 28 hier_v1 dev manifests
# (7 cells x l3/l2/l1/probe), locked decoding (I7: greedy, answer-tags
# contract, max_new_tokens 32 — the registered FlipTrack eval command shape).
# Usage: run_hier_p2_openform.sh MODEL_KEY MODEL_PATH NODE GPU
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
PY=.venv/bin/python

[[ $# -eq 4 || $# -eq 5 ]] || { echo "Usage: $0 MODEL_KEY MODEL_PATH NODE GPU [IMAGE_MODE]" >&2; exit 2; }
MODEL_KEY="$1"; MODEL_PATH="$2"; NODE="$3"; GPU="$4"; IMAGE_MODE="${5:-real}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN="hier_p2_openform_${MODEL_KEY}_${IMAGE_MODE}_${NODE}_gpu${GPU}_${STAMP}"
RUN_DIR="experiments/runs/${RUN}"
LOG="$ROOT/logs/${RUN}.log"
CLAIMS=/dev/shm/blind-gains/gpu_claims
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }

"$PY" scripts/m7_gpu_occupancy_guard.py --node "$NODE" --gpus "$GPU" >> "$LOG" 2>&1 \
  || { log "guard denied $NODE:$GPU; abort"; exit 1; }
payload=$(jq -nc --argjson gpu "$GPU" --arg run_id "$RUN" --argjson pid null \
  --arg dir "$RUN_DIR" --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{gpu:$gpu, run_id:$run_id, pid:$pid, eval_run_dir:$dir, written_utc:$ts,
    written_by:"scripts/run_hier_p2_openform.sh"}')
printf '%s\n' "$payload" | ssh -o BatchMode=yes -o ConnectTimeout=25 "$NODE" \
  "mkdir -p '$CLAIMS' && cat > '$CLAIMS/${NODE}_gpu${GPU}.claim'" \
  || { log "claim write failed; abort"; exit 1; }

mkdir -p "$RUN_DIR"
jq -n --arg run_id "$RUN" --arg model_key "$MODEL_KEY" --arg model_path "$MODEL_PATH" \
  --arg node "$NODE" --argjson gpu "$GPU" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{schema_version:"blind-gains.run-manifest.v1", run_id:$run_id,
    job_type:"hier_p2_openform_sweep", status:"running", node:$node,
    gpu_ids:[$gpu], model_key:$model_key, model_path:$model_path,
    git_hash:$git_hash, seed:0, noise_seed:0, max_new_tokens:32,
    start_time_utc:$started, end_time_utc:null, exit_code:null,
    registration:"docs/registered_hier_benchmark_v1.md §7 + A2",
    deviations:[]}' > "$RUN_DIR/run_manifest.json"

overall_rc=0
for manifest in data/hier_v1_dev/manifest_*.jsonl; do
  name=$(basename "$manifest" .jsonl); name=${name#manifest_}
  out_dir="$RUN_DIR/$name"
  mkdir -p "$out_dir"
  log "cell $name START"
  ssh -o BatchMode=yes -o ConnectTimeout=25 "$NODE" \
    "cd '$ROOT' && source .venv/bin/activate && \
     env PYTHONUNBUFFERED=1 TRANSFORMERS_OFFLINE=1 HF_HOME=$ROOT/artifacts/hf_home \
     CUDA_VISIBLE_DEVICES=$GPU PYTHONPATH=. \
     python scripts/eval_qwen_vl_fliptrack.py \
       --model-path '$MODEL_PATH' --manifest '$manifest' \
       --output '$out_dir/predictions.jsonl' \
       --metrics-output '$out_dir/metrics.json' \
       --image-mode $IMAGE_MODE --seed 0 --noise-seed 0 --max-new-tokens 32" \
    >> "$LOG" 2>&1
  rc=$?
  log "cell $name DONE rc=$rc"
  if [[ $rc -ne 0 ]]; then overall_rc=1; fi
done

"$PY" scripts/finalize_run_manifest.py "$RUN_DIR/run_manifest.json" "$overall_rc" >> "$LOG" 2>&1 \
  || log "finalize_run_manifest failed"
ssh -o ConnectTimeout=25 "$NODE" "rm -f '$CLAIMS/${NODE}_gpu${GPU}.claim'" 2>/dev/null
log "sweep complete overall_rc=$overall_rc"
echo "$RUN_DIR"
exit "$overall_rc"
