#!/usr/bin/env bash
# HB P2.1 candidate-ranking sweep: one model over the 14 hier ranking configs.
# Usage: run_hier_p2_ranking.sh MODEL_KEY NODE GPU [CONDITION]
# CONDITION defaults to real; no_image gives the blind candidate-ranking floor.
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
PY=.venv/bin/python

[[ $# -eq 3 || $# -eq 4 ]] || { echo "Usage: $0 MODEL_KEY NODE GPU [CONDITION]" >&2; exit 2; }
MODEL_KEY="$1"; NODE="$2"; GPU="$3"; CONDITION="${4:-real}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN="hier_p2_ranking_${MODEL_KEY}_${CONDITION}_${NODE}_gpu${GPU}_${STAMP}"
RUN_DIR="experiments/runs/${RUN}"
LOG="$ROOT/logs/${RUN}.log"
CLAIMS=/dev/shm/blind-gains/gpu_claims
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }

"$PY" scripts/m7_gpu_occupancy_guard.py --node "$NODE" --gpus "$GPU" >> "$LOG" 2>&1 \
  || { log "guard denied $NODE:$GPU; abort"; exit 1; }
payload=$(jq -nc --argjson gpu "$GPU" --arg run_id "$RUN" --argjson pid null \
  --arg dir "$RUN_DIR" --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{gpu:$gpu, run_id:$run_id, pid:$pid, eval_run_dir:$dir, written_utc:$ts,
    written_by:"scripts/run_hier_p2_ranking.sh"}')
printf '%s\n' "$payload" | ssh -o BatchMode=yes -o ConnectTimeout=25 "$NODE" \
  "mkdir -p '$CLAIMS' && cat > '$CLAIMS/${NODE}_gpu${GPU}.claim'" \
  || { log "claim write failed; abort"; exit 1; }

mkdir -p "$RUN_DIR"
jq -n --arg run_id "$RUN" --arg model_key "$MODEL_KEY" --arg node "$NODE" \
  --arg condition "$CONDITION" \
  --argjson gpu "$GPU" --arg git_hash "$(git rev-parse HEAD)" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{schema_version:"blind-gains.run-manifest.v1", run_id:$run_id,
    job_type:"hier_p2_ranking_sweep", status:"running", node:$node,
    gpu_ids:[$gpu], model_key:$model_key, condition:$condition, git_hash:$git_hash,
    start_time_utc:$started, end_time_utc:null, exit_code:null,
    registration:"docs/registered_hier_benchmark_v1.md §7 + A2",
    deviations:[]}' > "$RUN_DIR/run_manifest.json"

overall_rc=0
for config in configs/eval/hier_p2_ranking_v1_*.json; do
  name=$(basename "$config" .json); name=${name#hier_p2_ranking_v1_}
  out="$RUN_DIR/${name}.jsonl"
  log "cell $name START"
  ssh -o BatchMode=yes -o ConnectTimeout=25 "$NODE" \
    "cd '$ROOT' && source .venv/bin/activate && \
     env PYTHONUNBUFFERED=1 TRANSFORMERS_OFFLINE=1 HF_HOME=$ROOT/artifacts/hf_home \
     CUDA_VISIBLE_DEVICES=$GPU PYTHONPATH=. \
     python scripts/eval_qwen_vl_visual_evidence_ranking.py \
       --config '$config' --model-key '$MODEL_KEY' --condition $CONDITION \
       --cache-dir '$RUN_DIR/cache' \
       --output '$out'" >> "$LOG" 2>&1
  rc=$?
  log "cell $name DONE rc=$rc"
  if [[ $rc -ne 0 ]]; then overall_rc=1; fi
done

"$PY" scripts/finalize_run_manifest.py "$RUN_DIR/run_manifest.json" "$overall_rc" >> "$LOG" 2>&1 \
  || log "finalize_run_manifest failed"
ssh -o ConnectTimeout=25 "$NODE" "rm -f '$CLAIMS/${NODE}_gpu${GPU}.claim'" 2>/dev/null
log "ranking sweep complete overall_rc=$overall_rc"
echo "$RUN_DIR"
exit "$overall_rc"
