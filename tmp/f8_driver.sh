#!/usr/bin/env bash
# F8 Mini-A5 endpoint evaluation driver.
# 6 cells, 3 stages, an29 only. Runs under setsid+nohup ON an29.
# Follows reports/f8_eval_plan_v1.json exactly (unbound launcher path).
set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"

ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 90

# Plan section execution.env_vars_that_must_be_UNSET
unset BLIND_GAINS_PILOT_SOURCE_RUN BLIND_GAINS_PILOT_GLOBAL_STEP
unset BLIND_GAINS_M5_SOURCE_RUN BLIND_GAINS_M5_GLOBAL_STEP

RUN_TS="20260730T004031Z"
STATE="$ROOT/logs/mini_a5_f8_driver_${RUN_TS}"
mkdir -p "$STATE"
DRIVER_LOG="$STATE/driver.log"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" >> "$DRIVER_LOG"; }

CP="$ROOT/checkpoints/mini_a5/mini_a5_cp_seed1/global_step_120/actor/huggingface"
MEMBER="$ROOT/checkpoints/mini_a5/mini_a5_same_data_seed1/global_step_120/actor/huggingface"
R19M="experiments/runs/caption_qa_pair_build_fliptrack_v02r19_qwen25vl3b_384_20260710T140200Z/shards/captions_shard_0.jsonl"
R20M="data/fliptrack_r20_source_manifest.jsonl"
CHM="data/fliptrack_chart_v08_calibration_v1_manifest.jsonl"

RD_C1="experiments/runs/mini_a5_f8_r19_cp_step120_real_an29_${RUN_TS}"
RD_C2="experiments/runs/mini_a5_f8_r19_member_step120_real_an29_${RUN_TS}"
RD_C3="experiments/runs/mini_a5_f8_r20_cp_step120_real_an29_${RUN_TS}"
RD_C4="experiments/runs/mini_a5_f8_r20_member_step120_real_an29_${RUN_TS}"
RD_C5="experiments/runs/mini_a5_f8_chartv08_cp_step120_real_an29_${RUN_TS}"
RD_C6="experiments/runs/mini_a5_f8_chartv08_member_step120_real_an29_${RUN_TS}"

log "driver start host=$(hostname) run_ts=${RUN_TS} pid=$$"
git rev-parse HEAD > "$STATE/git_head_at_launch.txt" 2>&1
git status --porcelain > "$STATE/git_status_porcelain_at_launch.txt" 2>&1
log "git_head=$(cat "$STATE/git_head_at_launch.txt")"
log "git_status_lines=$(wc -l < "$STATE/git_status_porcelain_at_launch.txt")"
env | grep -E '^BLIND_GAINS_(PILOT|M5)_' > "$STATE/binding_env_check.txt" 2>&1
log "binding_env_vars_present=$(wc -l < "$STATE/binding_env_check.txt")"

launch_cell() {  # cell model manifest run_dir gpus
  local cell="$1" model="$2" manifest="$3" rd="$4" gpus="$5" rc
  log "LAUNCH ${cell} rd=${rd} gpus='${gpus}' manifest=${manifest}"
  BLIND_GAINS_EVAL_SEED=0 bash scripts/launch_fliptrack_eval_shards.sh \
    an29 0 4 "$model" "$manifest" "$rd" 32 "$gpus" real \
    > "$STATE/${cell}.launch.out" 2> "$STATE/${cell}.launch.err"
  rc=$?
  echo "$rc" > "$STATE/${cell}.launcher_exit_code"
  log "LAUNCH ${cell} launcher_exit_code=${rc}"
  return $rc
}

wait_cell() {  # run_dir  -> echoes final status
  local rd="$1" st deadline
  deadline=$(( $(date +%s) + 10800 ))
  while :; do
    st="$(jq -r '.status' "${rd}/run_manifest.json" 2>/dev/null)"
    if [[ "$st" == "complete" || "$st" == "fail" ]]; then echo "$st"; return 0; fi
    if [[ $(date +%s) -ge $deadline ]]; then echo "driver_timeout"; return 0; fi
    sleep 20
  done
}

abort() {
  log "ABORT: $*"
  echo "aborted" > "$STATE/DRIVER_STATUS"
  exit 1
}

run_stage() {  # stage cellA modelA manA rdA gpusA cellB modelB manB rdB gpusB
  local stage="$1"
  local cA="$2" mA="$3" nA="$4" rA="$5" gA="$6"
  local cB="$7" mB="$8" nB="$9" rB="${10}" gB="${11}"
  log "==== STAGE ${stage} begin ===="
  launch_cell "$cA" "$mA" "$nA" "$rA" "$gA" || abort "stage ${stage} launcher failed for ${cA}"
  sleep 5
  launch_cell "$cB" "$mB" "$nB" "$rB" "$gB" || abort "stage ${stage} launcher failed for ${cB}"
  local sA sB
  sA="$(wait_cell "$rA")"; log "STAGE ${stage} ${cA} status=${sA}"
  sB="$(wait_cell "$rB")"; log "STAGE ${stage} ${cB} status=${sB}"
  echo "$sA" > "$STATE/${cA}.final_status"
  echo "$sB" > "$STATE/${cB}.final_status"
  [[ "$sA" == "complete" && "$sB" == "complete" ]] || abort "stage ${stage} did not reach complete (${cA}=${sA}, ${cB}=${sB})"
  log "==== STAGE ${stage} complete ===="
}

run_stage 1 F8-C1 "$CP" "$R19M" "$RD_C1" "0 1 2 3" \
             F8-C2 "$MEMBER" "$R19M" "$RD_C2" "4 5 6 7"

run_stage 2 F8-C3 "$CP" "$R20M" "$RD_C3" "0 1 2 3" \
             F8-C4 "$MEMBER" "$R20M" "$RD_C4" "4 5 6 7"

run_stage 3 F8-C5 "$CP" "$CHM" "$RD_C5" "0 1 2 3" \
             F8-C6 "$MEMBER" "$CHM" "$RD_C6" "4 5 6 7"

log "ALL SIX CELLS COMPLETE"
echo "done" > "$STATE/DRIVER_STATUS"
exit 0
