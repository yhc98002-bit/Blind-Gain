#!/usr/bin/env bash
# Gate-1 arm-1 (std) held-out endpoint eval GENERATION chain, per
# scripts/gate1_endpoint_evals_todo.md. Runs on an12 GPUs 0-3 (an29 is
# occupied by the necessity arm; the todo doc names an12 as the substitute).
# SEALING (registered): this chain only LAUNCHES generation and counts
# finished shard-metrics files; it never opens, prints, or copies any
# prediction/metric content. The readout runs only after BOTH arms complete
# and the section-9 acceptance audit passes.
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
LOG="$ROOT/logs/gate1_std_evals_chain.log"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }
log "std eval generation chain start"

# NOTE: the merge launcher prepends ${ROOT}/ to its ACTOR_DIR argument, so it
# must receive the REPO-RELATIVE path (first merge attempt failed on a doubled
# absolute path).
ACTOR_REL="checkpoints/mini_a5/mini_a5_std_seed1/global_step_120/actor"
ACTOR="$ROOT/$ACTOR_REL"
CKPT="$ACTOR/huggingface"
# The trainer writes config/tokenizer into huggingface/ but the WEIGHTS stay in
# FSDP shards until the merge runs (first launch attempt died on exactly this:
# transformers found no model.safetensors). Merge if the index is absent, then
# verify against the F8-arm pin (same 3B architecture): total_size 8131575808,
# 825 weight-map entries.
IDX="$CKPT/model.safetensors.index.json"
if [[ ! -f "$IDX" ]]; then
  log "HF weights missing; launching FSDP->HF merge on an12"
  mout=$(bash scripts/launch_easyr1_checkpoint_merge.sh an12 "$ACTOR_REL" gate1_std_step120 2>&1 | tail -1)
  log "merge launcher -> $mout"
  for i in $(seq 1 40); do
    sleep 30
    [[ -f "$IDX" ]] && break
  done
  [[ -f "$IDX" ]] || { log "merge did not produce index within 20 min; abort"; exit 1; }
  sleep 30   # let shard writes settle before verifying
fi
pin=$(.venv/bin/python -c "import json; d=json.load(open('$IDX')); print(d['metadata']['total_size'], len(d['weight_map']))" 2>/dev/null)
[[ "$pin" == "8131575808 825" ]] || { log "merged index pin mismatch ($pin); abort"; exit 1; }
log "checkpoint verified: merged HF weights present, index pin OK ($pin)"

# an12 0-3 must be idle before we start
busy=$(ssh -o ConnectTimeout=15 an12 "nvidia-smi --query-gpu=index,memory.used --format=csv,noheader,nounits | awk -F', ' '\$1<4 && \$2>1024 {c++} END {print c+0}'" 2>/dev/null)
[[ "${busy:-9}" == "0" ]] || { log "an12 gpus 0-3 not idle (busy=$busy); abort"; exit 1; }

# registered env for every launcher call
unset BLIND_GAINS_PILOT_SOURCE_RUN BLIND_GAINS_PILOT_GLOBAL_STEP BLIND_GAINS_M5_SOURCE_RUN BLIND_GAINS_M5_GLOBAL_STEP
export BLIND_GAINS_EVAL_SEED=0

R19_MANIFEST="experiments/runs/caption_qa_pair_build_fliptrack_v02r19_qwen25vl3b_384_20260710T140200Z/shards/captions_shard_0.jsonl"
R20_MANIFEST="data/fliptrack_r20_source_manifest.jsonl"
CHART_MANIFEST="data/fliptrack_chart_v08_calibration_v1_manifest.jsonl"
CATCH_MANIFEST="data/derived/mini_a5_catch_eval_manifest_v1.jsonl"
CATCH_SHA_EXPECTED="c4bb508f930ec47c9f3a2a4bc905693394f63bf6b4ebbd0f1332eef85afcbe4a"

# catch manifest preflight (rebuild if absent, then verify pin)
if [[ ! -f "$CATCH_MANIFEST" ]]; then
  log "catch manifest absent; rebuilding"
  PYTHONPATH=. .venv/bin/python scripts/build_mini_a5_catch_eval_manifest.py >> "$LOG" 2>&1 || { log "catch manifest rebuild failed"; exit 1; }
fi
sha=$(sha256sum "$CATCH_MANIFEST" | cut -d' ' -f1)
[[ "$sha" == "$CATCH_SHA_EXPECTED" ]] || { log "catch manifest sha mismatch ($sha); abort"; exit 1; }

# wait_metrics RUN_DIR EXPECTED MAX_MIN LABEL
wait_metrics() {
  local d="$1" want="$2" maxmin="$3" lbl="$4" i have
  for i in $(seq 1 "$maxmin"); do
    sleep 60
    have=$(ls "$d/metrics" 2>/dev/null | wc -l)
    if [[ "$have" -ge "$want" ]]; then log "[$lbl] all $want shard metrics present"; return 0; fi
    if grep -ls "Traceback" "$d"/logs/* >/dev/null 2>&1 && [[ $((i % 10)) -eq 0 ]]; then
      log "[$lbl] WARNING traceback present in a worker log at minute $i (workers may still retry)"
    fi
  done
  log "[$lbl] TIMEOUT after $maxmin min (have=$have/$want)"
  return 1
}

run_set() {
  local lbl="$1" nshards="$2" manifest="$3" rundir="$4" gpus="$5"
  log "[$lbl] launching $nshards shards on an12 gpus [$gpus] -> $rundir"
  bash scripts/launch_fliptrack_eval_shards.sh an12 0 "$nshards" "$CKPT" "$manifest" "$rundir" 32 "$gpus" real >> "$LOG" 2>&1 \
    || { log "[$lbl] launcher failed"; return 1; }
  wait_metrics "$rundir" "$nshards" 240 "$lbl"
}

TS=$(date -u +%Y%m%dT%H%M%SZ)
run_set r19      4 "$R19_MANIFEST"   "experiments/runs/mini_a5_gate1_r19_std_step120_real_an12_${TS}"      '0 1 2 3' || exit 1
run_set r20      4 "$R20_MANIFEST"   "experiments/runs/mini_a5_gate1_r20_std_step120_real_an12_${TS}"      '0 1 2 3' || exit 1
run_set chartv08 4 "$CHART_MANIFEST" "experiments/runs/mini_a5_gate1_chartv08_std_step120_real_an12_${TS}" '0 1 2 3' || exit 1
run_set catch    1 "$CATCH_MANIFEST" "experiments/runs/mini_a5_catch_std_step120_real_an12_${TS}"          '3'       || exit 1

log "*** STD ARM GENERATION COMPLETE (4 eval sets; outputs remain sealed until both arms + acceptance audit) ***"
