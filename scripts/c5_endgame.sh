#!/usr/bin/env bash
# C5 / R4 endgame waiter.
#
# Watches both 7B arms to step 100, then per arm: verify the self-finalized
# manifest, merge the fp32 model shards to HF (CPU-only), verify the index
# against the registered 7B shape, and launch the arm's two geo3k eval cells
# (test real + test gray) via the same guarded launcher that produced the
# banked base cells. All evals run on an12; an29 carries nothing after A1's
# merge, so it is cleaned and declared SAFE TO RELEASE at that moment.
# After A2-gray's merge frees an12's training quad and no 7B trainer remains
# on an12, M7 a1_real seed 2 is relaunched there (placement rule satisfied:
# no colocation with a 7B host-offload arm).
#
# Fail-closed: any unexpected state stops that arm's chain and logs loudly.
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"

LOG="$ROOT/logs/c5_endgame.log"
STATE="$ROOT/logs/c5_endgame_state"
mkdir -p "$STATE"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }

A2_RUN=experiments/runs/c5_a2_gray_seed1_7b_an12_20260803T151727Z
A1_RUN=experiments/runs/c5_a1_real_seed1_7b_an29_20260804T004126Z
A2_CKPT=checkpoints/c5/c5_a2_gray_seed1_7b
A1_CKPT=checkpoints/c5/c5_a1_real_seed1_7b
MODEL_7B_INDEX_SIZE=16584333312

DEADLINE=$(( $(date -u +%s) + 40*3600 ))
log "endgame start; A2 run=$A2_RUN A1 run=$A1_RUN"

st()  { cat "$STATE/$1" 2>/dev/null || echo WAIT; }
set_st() { echo "$2" > "$STATE/$1"; log "[$1] -> $2"; }

merge_and_verify() {  # arm_label ckpt_dir node
  local label="$1" ckpt="$2" node="$3"
  log "[$label] merging on $node"
  local out rc
  out=$(bash scripts/launch_easyr1_checkpoint_merge.sh "$node" "$ckpt/global_step_100/actor" "c5_${label}_step100" 2>&1 | tail -1)
  rc=$?
  log "[$label] merge launcher rc=$rc $out"
  [[ $rc -ne 0 ]] && return 1
  local i
  for i in $(seq 1 30); do
    if .venv/bin/python - "$ckpt/global_step_100/actor/huggingface/model.safetensors.index.json" <<'PYEOF'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
    assert d["metadata"]["total_size"] == 16584333312, d["metadata"]["total_size"]
    assert len(d["weight_map"]) > 400
except Exception:
    raise SystemExit(1)
PYEOF
    then log "[$label] merge verified: total_size=16584333312"; return 0; fi
    sleep 60
  done
  log "[$label] MERGE VERIFY TIMEOUT"; return 1
}

launch_cell() {  # arm_label model_path cond gpu
  local label="$1" mp="$2" cond="$3" gpu="$4"
  local out
  out=$(bash scripts/launch_blind_solvability_v2_condition.sh an12 "$gpu" "$cond" "$mp" "c5_7b_${label}" 2>&1 | tail -1)
  log "[$label] cell $cond on an12:$gpu -> $out"
  [[ "$out" == experiments/runs/* ]] && echo "$out" > "$STATE/cell_${label}_${cond}" && return 0
  return 1
}

while :; do
  now=$(date -u +%s); (( now > DEADLINE )) && { log "DEADLINE 40h; stopping"; exit 4; }

  # ---------- A2-gray chain (an12) ----------
  case "$(st a2)" in
    WAIT)
      s=$(jq -r '.status' "$A2_RUN/run_manifest.json" 2>/dev/null)
      t=$(grep -o '"last_global_step": *[0-9]*' "$A2_CKPT/checkpoint_tracker.json" | grep -o '[0-9]*')
      log "[a2] status=$s tracker=$t"
      if [[ "$s" == "complete" && "$t" == "100" ]]; then set_st a2 MERGE
      elif [[ "$s" == "fail" ]]; then set_st a2 FAILED
      fi ;;
    MERGE)
      if merge_and_verify a2_gray "$A2_CKPT" an12; then set_st a2 CELLS; else set_st a2 FAILED; fi ;;
    CELLS)
      # an12 training quad is free now; launch A2's two cells on 0,1 and seed-2 on 4-7
      launch_cell a2_gray "$A2_CKPT/global_step_100/actor/huggingface" real 0 || set_st a2 FAILED
      sleep 30
      launch_cell a2_gray "$A2_CKPT/global_step_100/actor/huggingface" gray 1 || set_st a2 FAILED
      [[ "$(st a2)" == CELLS ]] && set_st a2 EVAL_WAIT
      if [[ "$(st seed2)" == WAIT ]]; then
        n7b=$(ssh -o ConnectTimeout=15 an12 "pgrep -af 'verl.trainer.mai[n]'" 2>/dev/null | grep -c 7b || true)
        if [[ "${n7b:-0}" -eq 0 ]]; then
          out=$(bash scripts/launch_m7_virl_arm.sh a1_real 2 an12 4,5,6,7 2>&1 | tail -1)
          log "[seed2] relaunch on an12 4-7 -> $out"
          [[ "$out" == experiments/runs/* ]] && set_st seed2 RUNNING || set_st seed2 LAUNCH_FAILED
        else
          log "[seed2] 7B trainer still on an12; holding"
        fi
      fi ;;
    EVAL_WAIT)
      done_n=0
      for c in real gray; do
        d=$(cat "$STATE/cell_a2_gray_$c" 2>/dev/null); [[ -z "$d" ]] && continue
        [[ "$(jq -r '.status' "$d/run_manifest.json" 2>/dev/null)" == "complete" ]] && done_n=$((done_n+1))
      done
      log "[a2] eval cells complete: $done_n/2"
      [[ $done_n -eq 2 ]] && set_st a2 DONE ;;
  esac

  # ---------- A1-real chain (an29 -> release) ----------
  case "$(st a1)" in
    WAIT)
      s=$(jq -r '.status' "$A1_RUN/run_manifest.json" 2>/dev/null)
      t=$(grep -o '"last_global_step": *[0-9]*' "$A1_CKPT/checkpoint_tracker.json" | grep -o '[0-9]*')
      log "[a1] status=$s tracker=$t"
      if [[ "$s" == "complete" && "$t" == "100" ]]; then set_st a1 MERGE
      elif [[ "$s" == "fail" ]]; then set_st a1 FAILED
      fi ;;
    MERGE)
      if merge_and_verify a1_real "$A1_CKPT" an29; then set_st a1 RELEASE_AN29; else set_st a1 FAILED; fi ;;
    RELEASE_AN29)
      ssh -o ConnectTimeout=15 an29 "rm -rf /dev/shm/blind-gains 2>/dev/null; true"
      left=$(ssh -o ConnectTimeout=15 an29 "pgrep -fc 'verl.trainer.mai[n]|run_blind_solvabilit[y]'" 2>/dev/null || echo 0)
      gpu=$(ssh -o ConnectTimeout=15 an29 "nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | sort -n | tail -1" 2>/dev/null)
      log "[a1] an29 cleanup: remaining procs=$left max_gpu_mem=${gpu}MiB"
      log "*** AN29 IS SAFE TO RELEASE: A1-real trained+merged; weights on shared storage; /dev/shm cleaned; no project processes remain ***"
      set_st a1 CELLS ;;
    CELLS)
      launch_cell a1_real "$A1_CKPT/global_step_100/actor/huggingface" real 2 || set_st a1 FAILED
      sleep 30
      launch_cell a1_real "$A1_CKPT/global_step_100/actor/huggingface" gray 3 || set_st a1 FAILED
      [[ "$(st a1)" == CELLS ]] && set_st a1 EVAL_WAIT ;;
    EVAL_WAIT)
      done_n=0
      for c in real gray; do
        d=$(cat "$STATE/cell_a1_real_$c" 2>/dev/null); [[ -z "$d" ]] && continue
        [[ "$(jq -r '.status' "$d/run_manifest.json" 2>/dev/null)" == "complete" ]] && done_n=$((done_n+1))
      done
      log "[a1] eval cells complete: $done_n/2"
      [[ $done_n -eq 2 ]] && set_st a1 DONE ;;
  esac

  if [[ "$(st a1)" == DONE && "$(st a2)" == DONE ]]; then
    log "ALL SIX R4 CELLS ON DISK (4 arm cells + 2 banked base cells). R4 readout is unblocked."
    exit 0
  fi
  if [[ "$(st a1)" == FAILED || "$(st a2)" == FAILED ]]; then
    log "GIVING UP LOUDLY: a1=$(st a1) a2=$(st a2); human attention required"
    exit 5
  fi
  sleep 300
done
