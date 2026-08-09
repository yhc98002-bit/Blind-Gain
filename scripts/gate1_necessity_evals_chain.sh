#!/usr/bin/env bash
# Gate-1 arm-3 (necessity) merge + held-out eval GENERATION chain, per
# scripts/gate1_endpoint_evals_todo.md. Waits for the necessity arm's training
# to complete on an29, then merges the FSDP checkpoint to HF, verifies the
# index pin, and runs the four eval sets on the freed an29 GPUs.
# SEALING (registered): launches generation and counts finished shard-metrics
# files only; never opens prediction/metric content. The readout runs only
# after BOTH arms complete and the section-9 acceptance audit passes.
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
LOG="$ROOT/logs/gate1_necessity_evals_chain.log"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }
log "necessity merge+eval chain start (waiting on training)"

ARM_RUN=experiments/runs/mini_a5_necessity_main_an29_20260807T222122Z
# merge launcher needs the REPO-RELATIVE actor path (it prepends ${ROOT}/)
ACTOR_REL="checkpoints/mini_a5/mini_a5_necessity_seed1/global_step_120/actor"
ACTOR="$ROOT/$ACTOR_REL"
CKPT="$ACTOR/huggingface"
IDX="$CKPT/model.safetensors.index.json"

# 1) wait for training completion (poll 10 min, cap 26 h)
DEADLINE=$(( $(date -u +%s) + 26*3600 ))
while :; do
  (( $(date -u +%s) > DEADLINE )) && { log "training wait deadline; abort"; exit 4; }
  s=$(grep -oE '"status": *"[a-z]+"' "$ARM_RUN/run_manifest.json" 2>/dev/null | tail -1)
  [[ "$s" == *complete* ]] && break
  [[ "$s" == *fail* ]] && { log "necessity training FAILED; abort"; exit 1; }
  sleep 600
done
log "necessity training complete"
sleep 120   # let checkpoint writes settle

# 2) merge FSDP -> HF on an29, verify against the F8-arm pin
if [[ ! -f "$IDX" ]]; then
  log "launching FSDP->HF merge on an29"
  mout=$(bash scripts/launch_easyr1_checkpoint_merge.sh an29 "$ACTOR_REL" gate1_necessity_step120 2>&1 | tail -1)
  log "merge launcher -> $mout"
  for i in $(seq 1 40); do
    sleep 30
    [[ -f "$IDX" ]] && break
  done
  [[ -f "$IDX" ]] || { log "merge did not produce index within 20 min; abort"; exit 1; }
  sleep 30
fi
pin=$(.venv/bin/python -c "import json; d=json.load(open('$IDX')); print(d['metadata']['total_size'], len(d['weight_map']))" 2>/dev/null)
[[ "$pin" == "8131575808 825" ]] || { log "merged index pin mismatch ($pin); abort"; exit 1; }
log "checkpoint verified: merged HF weights present, index pin OK ($pin)"

# 3) an29 gpus 0-3 and 5 must be idle (training just vacated the node)
busy=$(ssh -o ConnectTimeout=15 an29 "nvidia-smi --query-gpu=index,memory.used --format=csv,noheader,nounits | awk -F', ' '\$2>1024 {c++} END {print c+0}'" 2>/dev/null)
[[ "${busy:-9}" == "0" ]] || { log "an29 not idle post-training (busy=$busy); abort"; exit 1; }

# registered env
unset BLIND_GAINS_PILOT_SOURCE_RUN BLIND_GAINS_PILOT_GLOBAL_STEP BLIND_GAINS_M5_SOURCE_RUN BLIND_GAINS_M5_GLOBAL_STEP
export BLIND_GAINS_EVAL_SEED=0

R19_MANIFEST="experiments/runs/caption_qa_pair_build_fliptrack_v02r19_qwen25vl3b_384_20260710T140200Z/shards/captions_shard_0.jsonl"
R20_MANIFEST="data/fliptrack_r20_source_manifest.jsonl"
CHART_MANIFEST="data/fliptrack_chart_v08_calibration_v1_manifest.jsonl"
CATCH_MANIFEST="data/derived/mini_a5_catch_eval_manifest_v1.jsonl"
CATCH_SHA_EXPECTED="c4bb508f930ec47c9f3a2a4bc905693394f63bf6b4ebbd0f1332eef85afcbe4a"
sha=$(sha256sum "$CATCH_MANIFEST" | cut -d' ' -f1)
[[ "$sha" == "$CATCH_SHA_EXPECTED" ]] || { log "catch manifest sha mismatch ($sha); abort"; exit 1; }

wait_metrics() {
  local d="$1" want="$2" maxmin="$3" lbl="$4" i have
  for i in $(seq 1 "$maxmin"); do
    sleep 60
    have=$(ls "$d/metrics" 2>/dev/null | wc -l)
    if [[ "$have" -ge "$want" ]]; then log "[$lbl] all $want shard metrics present"; return 0; fi
    if grep -ls "Traceback" "$d"/logs/* >/dev/null 2>&1 && [[ $((i % 10)) -eq 0 ]]; then
      log "[$lbl] WARNING traceback present in a worker log at minute $i"
    fi
  done
  log "[$lbl] TIMEOUT after $maxmin min (have=$have/$want)"
  return 1
}

run_set() {
  local lbl="$1" nshards="$2" manifest="$3" rundir="$4" gpus="$5"
  log "[$lbl] launching $nshards shards on an29 gpus [$gpus] -> $rundir"
  bash scripts/launch_fliptrack_eval_shards.sh an29 0 "$nshards" "$CKPT" "$manifest" "$rundir" 32 "$gpus" real >> "$LOG" 2>&1 \
    || { log "[$lbl] launcher failed"; return 1; }
  wait_metrics "$rundir" "$nshards" 240 "$lbl"
}

TS=$(date -u +%Y%m%dT%H%M%SZ)
run_set r19      4 "$R19_MANIFEST"   "experiments/runs/mini_a5_gate1_r19_necessity_step120_real_an29_${TS}"      '0 1 2 3' || exit 1
run_set r20      4 "$R20_MANIFEST"   "experiments/runs/mini_a5_gate1_r20_necessity_step120_real_an29_${TS}"      '0 1 2 3' || exit 1
run_set chartv08 4 "$CHART_MANIFEST" "experiments/runs/mini_a5_gate1_chartv08_necessity_step120_real_an29_${TS}" '0 1 2 3' || exit 1
run_set catch    1 "$CATCH_MANIFEST" "experiments/runs/mini_a5_catch_necessity_step120_real_an29_${TS}"          '5'       || exit 1

log "*** NECESSITY ARM GENERATION COMPLETE (4 eval sets; outputs remain sealed until acceptance audit passes) ***"
