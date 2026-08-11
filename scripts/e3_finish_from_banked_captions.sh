#!/usr/bin/env bash
# Complete Track-4 premise-v2 E3 from the BANKED captioner pass.
#
# Stage A (the registered captioner command) already completed:
#   experiments/runs/track4_premise_v2_caption_store_an29_20260811T155104Z
#   run_manifest status=complete, 480 caption rows (640 image files / 480 distinct sha256)
# The registered runner then aborted at stage B because
# scripts/launch_caption_store_merge.sh required >=2 shards while the registered
# E3 command uses 1 (arity check `-lt 4`, now fixed to `-lt 3`).
#
# This script runs stages B, C and D only — the same registered underlying
# commands the aborted runner logged verbatim — and does NOT re-caption.
# It RUNS AND RECORDS ONLY; the registered per-type verdict (caption member
# accuracy <= blind-floor threshold + 0.10) is read by a separate instrument.
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
LOG="$ROOT/logs/track4_gates/e3_finish_from_banked_captions.log"
mkdir -p "$(dirname "$LOG")"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }

NODE=an29; GPU=3
CLAIMS=/dev/shm/blind-gains/gpu_claims
DATA=data/track4_premise_v2_dev_v1
QA_MODEL=artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct
CAP_RUN=experiments/runs/track4_premise_v2_caption_store_an29_20260811T155104Z
E3_RUN=experiments/runs/track4_premise_v2_e3_an29_20260811T155104Z
COVERAGE="$E3_RUN/merge_inputs/coverage_release_480.jsonl"
SHARD="$CAP_RUN/shards/store_shard_0.jsonl"
TS=$(date -u +%Y%m%dT%H%M%SZ)
OUT_DIR="$E3_RUN/finish_${TS}"
RUN_ID="t4v2_e3_finish_${TS}"
mkdir -p "$OUT_DIR"

log "=== E3 finish-from-banked-captions start (git $(git rev-parse --short HEAD)) ==="
log "caption store: $CAP_RUN (banked, not re-run)"

for f in "$COVERAGE" "$SHARD" "$DATA/caption_qa_inputs/manifest.jsonl" "$DATA/caption_qa_inputs/key.jsonl" "$QA_MODEL"; do
  [[ -e "$f" ]] || { log "FATAL missing input: $f"; exit 1; }
done
n_cap=$(wc -l < "$SHARD")
n_cov=$(wc -l < "$COVERAGE")
log "preflight: caption rows=$n_cap coverage rows=$n_cov"
[[ "$n_cap" == "480" ]] || { log "FATAL expected 480 caption rows, found $n_cap"; exit 1; }

# ---- STAGE B: merge (registered wrapper, now accepting a single shard) ------
log "STAGE B: merge via scripts/launch_caption_store_merge.sh"
merge_out=$(bash scripts/launch_caption_store_merge.sh track4_premise_v2_dev_v1 "$COVERAGE" "$SHARD" 2>&1)
rc=$?
printf '%s\n' "$merge_out" >> "$LOG"
log "STAGE B rc=$rc"
[[ $rc -eq 0 ]] || { log "*** E3 ABORTED at stage B (merge) ***"; exit 1; }

MERGE_DIR=$(ls -td experiments/runs/caption_store_merge_track4_premise_v2_dev_v1_* 2>/dev/null | head -1)
MERGED="$MERGE_DIR/captions.jsonl"
log "merge dir: $MERGE_DIR"
for i in $(seq 1 60); do [[ -s "$MERGED" ]] && break; sleep 10; done
[[ -s "$MERGED" ]] || { log "*** E3 ABORTED: merged captions not produced ($MERGED) ***"; exit 1; }
log "merged captions: $(wc -l < "$MERGED") rows"
if [[ -s "$MERGE_DIR/summary.json" ]]; then
  cc=$(python3 -c "import json;print(json.load(open('$MERGE_DIR/summary.json')).get('coverage_complete'))" 2>/dev/null)
  log "merge summary coverage_complete=$cc"
  [[ "$cc" == "True" ]] || { log "*** E3 ABORTED: coverage_complete is not true ***"; exit 1; }
fi

# ---- STAGE C: QA build restricted to the 320-member causal release ----------
QA="$OUT_DIR/caption_qa.jsonl"
log "STAGE C: build_caption_qa_pairs.py --allow-extra-captions"
.venv/bin/python scripts/build_caption_qa_pairs.py \
  --release-manifest "$DATA/caption_qa_inputs/manifest.jsonl" \
  --key-file "$DATA/caption_qa_inputs/key.jsonl" \
  --caption-store "$MERGED" \
  --output "$QA" \
  --summary "$OUT_DIR/caption_qa_build_summary.json" \
  --allow-extra-captions >> "$LOG" 2>&1
rc=$?
log "STAGE C rc=$rc -> $QA ($(wc -l < "$QA" 2>/dev/null || echo 0) rows)"
[[ $rc -eq 0 && -s "$QA" ]] || { log "*** E3 ABORTED at stage C (QA build) ***"; exit 1; }

# ---- STAGE D: caption-QA FlipTrack eval, 3B base ---------------------------
log "STAGE D: guard + claim $NODE gpu $GPU"
.venv/bin/python scripts/m7_gpu_occupancy_guard.py --node "$NODE" --gpus "$GPU" >> "$LOG" 2>&1 \
  || { log "*** E3 ABORTED: guard denied $NODE:$GPU ***"; exit 1; }
payload=$(jq -nc --argjson gpu "$GPU" --arg run_id "$RUN_ID" --argjson pid null \
  --arg dir "$OUT_DIR" --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{gpu:$gpu, run_id:$run_id, pid:$pid, eval_run_dir:$dir, written_utc:$ts, written_by:"scripts/e3_finish_from_banked_captions.sh"}')
printf '%s\n' "$payload" | ssh -o BatchMode=yes -o ConnectTimeout=25 "$NODE" \
  "mkdir -p '$CLAIMS' && cat > '$CLAIMS/${NODE}_gpu${GPU}.claim'" || { log "claim write failed"; exit 1; }
.venv/bin/python scripts/m7_gpu_occupancy_guard.py --node "$NODE" --gpus "$GPU" \
  --ignore-claim-run-id "$RUN_ID" >> "$LOG" 2>&1 \
  || { ssh -o ConnectTimeout=25 "$NODE" "rm -f '$CLAIMS/${NODE}_gpu${GPU}.claim'"; log "*** E3 ABORTED: post-claim re-check denied ***"; exit 1; }
log "guard+claim ok"

ssh -o BatchMode=yes -o ConnectTimeout=25 "$NODE" \
  "cd '$ROOT' && env PYTHONUNBUFFERED=1 TRANSFORMERS_OFFLINE=1 HF_HOME='$ROOT/artifacts/hf_home' CUDA_VISIBLE_DEVICES=$GPU '$ROOT/.venv/bin/python' scripts/eval_caption_qa_fliptrack.py --model-path '$QA_MODEL' --input '$QA' --output '$OUT_DIR/caption_qa_predictions.jsonl' --metrics-output '$OUT_DIR/caption_qa_metrics.json' --max-new-tokens 32" >> "$LOG" 2>&1
rc=$?
ssh -o ConnectTimeout=25 "$NODE" "rm -f '$CLAIMS/${NODE}_gpu${GPU}.claim'" 2>/dev/null || true
log "STAGE D rc=$rc; claim released"

if [[ $rc -eq 0 && -s "$OUT_DIR/caption_qa_predictions.jsonl" ]]; then
  log "*** E3 GENERATION COMPLETE — predictions at $OUT_DIR/caption_qa_predictions.jsonl"
  log "    ($(wc -l < "$OUT_DIR/caption_qa_predictions.jsonl") rows); per-type verdict read separately ***"
  printf '%s\n' "$OUT_DIR" > logs/track4_gates/e3_finish_out_dir
else
  log "*** E3 ABORTED at stage D (eval) rc=$rc ***"
fi
