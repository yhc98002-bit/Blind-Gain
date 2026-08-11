#!/usr/bin/env bash
# C6 mechanism-at-scale: generate the six FlipTrack cells for the 7B access pair
# (frozen 7B base, C5 A1-real, C5 A2-gray) x (R19, R20 private twin) on an12 0-3.
#
# GENERATION ONLY. No value is read here: the registered C6 readout
# (docs/registered_c6_mechanism_at_scale_v1.md + its instrument) is authored in
# parallel and is the only thing permitted to turn these cells into numbers.
#
# The 7B base is RE-RUN rather than reused: the 2026-07-10 7B base R19 cells
# predate the canonical scoring contract (their rows carry no contract_valid /
# parser_version / prompt_contract_id and their strict == lenient), so they are
# not comparable to arm cells scored under the current contract.
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
LOG="$ROOT/logs/c6_cells_chain.log"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }
log "C6 cell generation start (6 cells, an12 0-3)"

BASE="$ROOT/artifacts/models/Qwen/Qwen2.5-VL-7B-Instruct"
A1="$ROOT/checkpoints/c5/c5_a1_real_seed1_7b/global_step_100/actor/huggingface"
A2="$ROOT/checkpoints/c5/c5_a2_gray_seed1_7b/global_step_100/actor/huggingface"
R19="experiments/runs/caption_qa_pair_build_fliptrack_v02r19_qwen25vl3b_384_20260710T140200Z/shards/captions_shard_0.jsonl"
R20="data/fliptrack_r20_source_manifest.jsonl"
R19_SHA_EXPECTED="e1dde98451e1c7473906637c029713ab4f95ab4f7c915bd035f697953bf2ffb2"

for p in "$BASE/config.json" "$A1/config.json" "$A2/config.json" "$R19" "$R20"; do
  [[ -e "$p" ]] || { log "missing input: $p; abort"; exit 1; }
done
sha=$(sha256sum "$R19" | cut -d' ' -f1)
[[ "$sha" == "$R19_SHA_EXPECTED" ]] || { log "R19 manifest sha mismatch ($sha); abort"; exit 1; }
log "inputs verified; R19 pin OK"

# an12 0-3 must be idle before EACH cell (a2_gray holds 4-7; these evals are
# non-ramping). Wait rather than abort: another driver may already be running a
# C6 cell on these GPUs, and the remaining cells simply queue behind it.
wait_for_gpus() {
  local i busy
  for i in $(seq 1 240); do
    busy=$(ssh -o ConnectTimeout=15 an12 "nvidia-smi --query-gpu=index,memory.used --format=csv,noheader,nounits | awk -F', ' '\$1<4 && \$2>1024 {c++} END {print c+0}'" 2>/dev/null)
    [[ "${busy:-9}" == "0" ]] && return 0
    [[ $((i % 10)) -eq 1 ]] && log "waiting for an12 0-3 (busy=${busy:-?})"
    sleep 60
  done
  log "an12 0-3 still busy after 4 h; abort"
  return 1
}

export BLIND_GAINS_EVAL_SEED=0
unset BLIND_GAINS_PILOT_SOURCE_RUN BLIND_GAINS_PILOT_GLOBAL_STEP BLIND_GAINS_M5_SOURCE_RUN BLIND_GAINS_M5_GLOBAL_STEP

wait_metrics() {
  local d="$1" want="$2" maxmin="$3" lbl="$4" i have
  for i in $(seq 1 "$maxmin"); do
    sleep 60
    have=$(ls "$d/metrics" 2>/dev/null | wc -l)
    [[ "$have" -ge "$want" ]] && { log "[$lbl] all $want shard metrics present"; return 0; }
  done
  log "[$lbl] TIMEOUT after $maxmin min (have=${have:-0}/$want)"
  return 1
}

# adopt_cell LABEL MODEL MANIFEST -> 0 if an existing run dir already covers this
# cell with a manifest that matches the registered spec (same model, same manifest
# hash, 4 shards, complete). Validation is by manifest content, never by name.
adopt_cell() {
  local lbl="$1" model="$2" manifest="$3" mhash d st mp ns
  mhash=$(sha256sum "$manifest" | cut -d' ' -f1)
  for d in $(ls -dt experiments/runs/c6_* 2>/dev/null); do
    [[ -f "$d/run_manifest.json" ]] || continue
    mp=$(jq -r '.model_path // ""' "$d/run_manifest.json" 2>/dev/null)
    [[ "$mp" == "$model" ]] || continue
    [[ "$(jq -r '.data_manifest_hash // ""' "$d/run_manifest.json" 2>/dev/null)" == "$mhash" ]] || continue
    ns=$(ls "$d/metrics" 2>/dev/null | wc -l)
    st=$(jq -r '.status // ""' "$d/run_manifest.json" 2>/dev/null)
    if [[ "$st" == complete && "$ns" -ge 4 ]]; then
      log "[$lbl] ADOPTING banked cell $d (model+manifest-hash match, $ns shard metrics)"
      echo "$d" > "logs/c6_cells/$lbl"; return 0
    fi
    if [[ "$st" == running ]]; then
      log "[$lbl] a matching cell is IN FLIGHT ($d); waiting for it instead of duplicating"
      wait_metrics "$d" 4 90 "$lbl" || return 1
      log "[$lbl] ADOPTING $d after in-flight completion"
      echo "$d" > "logs/c6_cells/$lbl"; return 0
    fi
  done
  return 1
}

run_cell() { # run_cell LABEL MODEL MANIFEST
  local lbl="$1" model="$2" manifest="$3" ts rundir
  adopt_cell "$lbl" "$model" "$manifest" && return 0
  wait_for_gpus || return 1
  ts=$(date -u +%Y%m%dT%H%M%SZ)
  rundir="experiments/runs/c6_${lbl}_an12_${ts}"
  log "[$lbl] launching 4 shards on an12 0-3 -> $rundir"
  bash scripts/launch_fliptrack_eval_shards.sh an12 0 4 "$model" "$manifest" "$rundir" 32 '0 1 2 3' real >> "$LOG" 2>&1 \
    || { log "[$lbl] launcher failed"; return 1; }
  wait_metrics "$rundir" 4 60 "$lbl" || return 1
  echo "$rundir" > "logs/c6_cells/$lbl"
  log "[$lbl] cell banked: $rundir"
}

mkdir -p logs/c6_cells
run_cell r19_base7b   "$BASE" "$R19" || exit 1
run_cell r19_a1real   "$A1"   "$R19" || exit 1
run_cell r19_a2gray   "$A2"   "$R19" || exit 1
run_cell r20_base7b   "$BASE" "$R20" || exit 1
run_cell r20_a1real   "$A1"   "$R20" || exit 1
run_cell r20_a2gray   "$A2"   "$R20" || exit 1

log "*** C6 GENERATION COMPLETE: 6 cells banked (pointers in logs/c6_cells/); values unread pending the registered readout ***"
