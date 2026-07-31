#!/usr/bin/env bash
# M7 completion chain -- turns the three finishing training arms into R3's
# final data with no human in the loop.
#
# Per arm, when checkpoint_tracker.json reaches last_global_step 100 AND the
# trainer pid recorded in the arm's run dir has exited:
#   1. CLOSE the arm's run manifest post-hoc via
#      scripts/close_orphaned_run_manifest.py (the arms were launched at
#      ed4aa96 through scripts/launch_m7_virl_arm.sh, which exec-d
#      verl.trainer.main directly and never self-finalizes; arm 1 was closed
#      the same way).  The manifest is never hand-edited.
#   2. MERGE global_step_100 FSDP model shards to HF weights via
#      scripts/launch_easyr1_checkpoint_merge.sh (CPU-only, self-finalizing
#      through run_manifest_job.py), then verify
#      model.safetensors.index.json against the verified 3B shape
#      (825 weight-map entries / 8,131,575,808 bytes -- arm 1's merge).
#   3. LAUNCH the arm's step-100 held-out eval on a GPU the arm itself
#      vacated (derived from the arm's own run_manifest gpu_ids, re-checked
#      via scripts/m7_gpu_occupancy_guard.py, reserved with a claim file
#      under /dev/shm/blind-gains/gpu_claims BEFORE launching), using
#      scripts/launch_virl39k_blind_v1_condition.sh with the exact VIRL_*
#      override set the step-0 waiter used (tmp/launch_m7_step0.sh), with
#      only VIRL_MODEL_PATH/REVISION, run prefix and job type changed.
#      One GPU per condition, matching step-0 exactly.
#   4. When all four step-100 evals are complete, run the full R3 readout
#      (scripts/build_m7_r3_readout.py).  The readout is fail-closed; if its
#      readiness gate refuses, the refusal is the logged result.
#
# A1 (already trained, merged, verified) starts directly at EVAL_LAUNCH and
# may use an idle an29 GPU (6/7/5) immediately.
#
# Modes:
#   launch-a1   launch the A1-real step-100 eval now, verify it generates
#   run         the long-lived waiter (setsid+nohup on a compute node)
#   status      print per-arm state and exit
#
# State machine per arm (persisted in logs/m7_completion_chain_state/):
#   TRAIN_WAIT -> CLOSE -> MERGE_LAUNCH -> MERGE_WAIT -> EVAL_LAUNCH
#   -> EVAL_WAIT -> DONE   (any unrecoverable error -> FAILED, loudly)
#
# Deadlines: training wait 30 h per arm (the task's ~30 h bound applies to
# the unbounded wait); merge 45 min; eval 16 h; global hard stop 48 h.  The
# global stop exceeds 30 h deliberately: measured cadence at build time
# (a2_gray ~27.5 min/step at step 55) projects its eval finishing ~31-33 h
# out, so a 30 h global kill would cut the last eval mid-flight.  Recorded
# here as a deviation from the literal "~30 h".
set -uo pipefail

ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
PY="$ROOT/.venv/bin/python"
LOG_DIR="$ROOT/logs"
LOG="$LOG_DIR/m7_completion_chain.log"
STATE_DIR="$LOG_DIR/m7_completion_chain_state"
PID_FILE="$LOG_DIR/m7_completion_chain.pid"
CLAIMS_DIR=/dev/shm/blind-gains/gpu_claims
mkdir -p "$LOG_DIR" "$STATE_DIR"

POLL_SECONDS=300
TRAIN_WAIT_LIMIT_S=$((30 * 3600))
MERGE_LIMIT_S=$((45 * 60))
EVAL_LIMIT_S=$((16 * 3600))
GLOBAL_LIMIT_S=$((48 * 3600))

# The verified 3B merged shape (arm 1's checkpoint, independently verified).
EXPECT_INDEX_BYTES=8131575808
EXPECT_INDEX_ENTRIES=825
HELDOUT_ROWS=4239

ARMS=(a1_real a2_gray a2b_noimage a3_caption)

declare -A TRAIN_RUN_DIR=(
  [a1_real]=experiments/runs/m7_virl_a1_real_seed1_an12_20260728T102036Z
  [a2_gray]=experiments/runs/m7_virl_a2_gray_seed1_an12_20260730T121803Z
  [a2b_noimage]=experiments/runs/m7_virl_a2b_noimage_seed1_an29_20260730T121834Z
  [a3_caption]=experiments/runs/m7_virl_a3_caption_seed1_an12_20260730T131311Z
)
declare -A ARM_COND=(
  [a1_real]=real [a2_gray]=gray [a2b_noimage]=none [a3_caption]=caption
)
declare -A ARM_TAG=([a1_real]=a1 [a2_gray]=a2 [a2b_noimage]=a2b [a3_caption]=a3)
# Eval node: the node whose GPUs the arm itself vacates (a1 trained on an12
# 0-3, which a3_caption now occupies, so a1 evaluates on the idle an29 GPUs
# the finished C5 cells vacated -- explicitly authorised).
declare -A EVAL_NODE=(
  [a1_real]=an29 [a2_gray]=an12 [a2b_noimage]=an29 [a3_caption]=an12
)
# a1's candidates are fixed; the other arms derive candidates from their own
# training manifest gpu_ids at eval time (the waiter is the only claimant of
# just-freed GPUs by construction).
declare -A EVAL_GPU_OVERRIDE=([a1_real]="6 7 5")
declare -A STEP0_RUN_DIR=(
  [a1_real]=experiments/runs/m7_step0_heldout_base_real_an29_20260730T154447Z
  [a2_gray]=experiments/runs/m7_step0_heldout_base_gray_an29_20260730T154458Z
  [a2b_noimage]=experiments/runs/m7_step0_heldout_base_none_an29_20260730T154501Z
  [a3_caption]=experiments/runs/m7_step0_heldout_base_caption_an29_20260730T154503Z
)

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >> "$LOG"; }

sget() { # sget <arm> <key> [default]
  local f="$STATE_DIR/$1.$2"
  if [[ -s "$f" ]]; then cat "$f"; else printf '%s' "${3:-}"; fi
}
sset() { # sset <arm> <key> <value>
  printf '%s' "$3" > "$STATE_DIR/$1.$2.tmp" && mv "$STATE_DIR/$1.$2.tmp" "$STATE_DIR/$1.$2"
}

init_states() {
  local arm
  for arm in "${ARMS[@]}"; do
    if [[ ! -s "$STATE_DIR/$arm.state" ]]; then
      if [[ "$arm" == a1_real ]]; then sset "$arm" state EVAL_LAUNCH
      else sset "$arm" state TRAIN_WAIT; fi
    fi
  done
}

fail_arm() { # fail_arm <arm> <message>
  log "[$1] FAILED: $2"
  log "[$1] FAILED: this arm's chain is stopped; the R3 readout can never fire; human attention required"
  sset "$1" state FAILED
}

# ssh liveness: prints alive|dead|unknown
pid_state() { # pid_state <node> <pid>
  local rc
  ssh -o BatchMode=yes -o ConnectTimeout=25 "$1" "kill -0 $2" >/dev/null 2>&1
  rc=$?
  if [[ $rc -eq 0 ]]; then printf alive
  elif [[ $rc -eq 1 ]]; then printf dead
  else printf unknown; fi
}

bump_retry() { # bump_retry <arm> <key> <max> -> rc 1 when budget exhausted
  local n
  n=$(sget "$1" "$2" 0)
  n=$((n + 1))
  sset "$1" "$2" "$n"
  [[ $n -le $3 ]]
}

# ---------------------------------------------------------------------------
# Step 1: post-hoc manifest close, exactly as arm 1 was closed
# ---------------------------------------------------------------------------
close_arm() { # close_arm <arm>; moves state on success
  local arm="$1" run_dir manifest node pid tracker exp_log train_log status
  run_dir="${TRAIN_RUN_DIR[$arm]}"
  manifest="$run_dir/run_manifest.json"
  node=$(jq -r '.node' "$manifest")
  pid=$(cat "$run_dir"/pids/*.pid 2>/dev/null | head -1)
  tracker="checkpoints/m7/m7_virl_${arm}_seed1/checkpoint_tracker.json"
  exp_log="checkpoints/m7/m7_virl_${arm}_seed1/experiment_log.jsonl"
  train_log=$(jq -r '.stdout_stderr_log' "$manifest")

  status=$(jq -r '.status' "$manifest")
  if [[ "$status" == "complete" ]]; then
    log "[$arm] manifest already complete; skipping close"
    sset "$arm" state MERGE_LAUNCH
    return 0
  fi

  # Evidence checks (the waiter never closes with exit 0 on unverified state)
  local step lines missing="" s
  step=$(jq -r '.last_global_step' "$tracker" 2>/dev/null)
  if [[ "$step" != "100" ]]; then
    log "[$arm] close blocked: tracker last_global_step=$step != 100 (re-checking next cycle)"
    sset "$arm" state TRAIN_WAIT
    return 0
  fi
  for s in 20 40 60 80 100; do
    [[ -d "checkpoints/m7/m7_virl_${arm}_seed1/global_step_$s" ]] || missing+=" global_step_$s"
  done
  local r
  for r in 0 1 2 3; do
    [[ -s "checkpoints/m7/m7_virl_${arm}_seed1/global_step_100/actor/model_world_size_4_rank_${r}.pt" ]] \
      || missing+=" actor/model_world_size_4_rank_${r}.pt"
  done
  if [[ -n "$missing" ]]; then
    fail_arm "$arm" "tracker says step 100 but artifacts are missing:$missing"
    return 0
  fi
  local bad
  bad=$(tail -c 41943040 "$train_log" 2>/dev/null \
        | grep -acE 'Traceback \(most recent call last\)|CUDA out of memory|torch.OutOfMemoryError|ncclSystemError' || true)
  if [[ "$bad" != "0" ]]; then
    fail_arm "$arm" "trainer log final 40MB contains $bad error marker line(s) ($train_log); refusing to close with exit 0"
    return 0
  fi
  lines=$(wc -l < "$exp_log")

  local prov reason
  prov="INFERRED, not observed: the run was launched by scripts/launch_m7_virl_arm.sh at ed4aa96, which exec-d verl.trainer.main directly, so no wrapper captured the process exit status. Basis: checkpoint_tracker.json last_global_step=100, all five registered checkpoints global_step_{20,40,60,80,100} present with four actor model shards at step 100, experiment_log.jsonl has ${lines} lines, no Traceback / CUDA OOM / NCCL error marker in the final 40 MB of ${train_log}, and pid ${pid} is gone from ${node}. Closed autonomously by scripts/m7_completion_chain.sh."
  reason="M7 arm launched through the pre-runner scripts/launch_m7_virl_arm.sh, which never self-finalizes; closed post-hoc by the M7 completion chain after the tracker reached step 100 and the trainer pid exited, exactly as arm 1 (m7_virl_a1_real_seed1_an12_20260728T102036Z) was closed."

  log "[$arm] closing run manifest (tracker=100, pid $pid dead on $node, log lines=$lines)"
  if "$PY" scripts/close_orphaned_run_manifest.py "$manifest" \
      --exit-code 0 \
      --exit-code-provenance "$prov" \
      --completion-evidence "checkpoints/m7/m7_virl_${arm}_seed1/global_step_100" \
      --completion-evidence "$tracker" \
      --completion-evidence "$exp_log" \
      --completion-evidence "$train_log" \
      --expected-artifact "$ROOT/$run_dir/reward_shadow.jsonl" \
      --expected-artifact "$ROOT/checkpoints/m7/m7_virl_${arm}_seed1/experiment_log.jsonl" \
      --expected-artifact "$ROOT/checkpoints/m7/m7_virl_${arm}_seed1/checkpoint_tracker.json" \
      --reason "$reason" >> "$LOG" 2>&1; then
    log "[$arm] manifest closed; status now $(jq -r '.status' "$manifest")"
    sset "$arm" state MERGE_LAUNCH
  else
    log "[$arm] close attempt refused/failed (see above)"
    if ! bump_retry "$arm" close_retries 5; then
      fail_arm "$arm" "close_orphaned_run_manifest.py failed 5 times"
    fi
  fi
}

# ---------------------------------------------------------------------------
# Step 2: merge to HF weights
# ---------------------------------------------------------------------------
merged_index_ok() { # merged_index_ok <arm>
  local idx="checkpoints/m7/m7_virl_${1}_seed1/global_step_100/actor/huggingface/model.safetensors.index.json"
  [[ -s "$idx" ]] || return 1
  jq -e --argjson b "$EXPECT_INDEX_BYTES" --argjson n "$EXPECT_INDEX_ENTRIES" \
     '(.metadata.total_size == $b) and ((.weight_map | length) == $n)' "$idx" >/dev/null 2>&1
}

merge_launch() { # merge_launch <arm>
  local arm="$1" node actor out rc run_dir
  node=$(jq -r '.node' "${TRAIN_RUN_DIR[$arm]}/run_manifest.json")
  actor="checkpoints/m7/m7_virl_${arm}_seed1/global_step_100/actor"
  if merged_index_ok "$arm"; then
    log "[$arm] merged HF checkpoint already present and index-verified; skipping merge"
    sset "$arm" state EVAL_LAUNCH
    return 0
  fi
  log "[$arm] launching checkpoint merge on $node ($actor)"
  out=$(bash scripts/launch_easyr1_checkpoint_merge.sh "$node" "$actor" "m7_${ARM_TAG[$arm]}_step100" 2>>"$LOG")
  rc=$?
  run_dir=$(printf '%s\n' "$out" | tail -1)
  log "[$arm] merge launcher rc=$rc run_dir=$run_dir"
  if [[ $rc -eq 0 && -n "$run_dir" && -f "$run_dir/run_manifest.json" ]]; then
    sset "$arm" merge_run_dir "$run_dir"
    sset "$arm" merge_started "$(date -u +%s)"
    sset "$arm" state MERGE_WAIT
  else
    if ! bump_retry "$arm" merge_retries 3; then
      fail_arm "$arm" "merge launcher failed 3 times (last rc=$rc)"
    fi
  fi
}

merge_wait() { # merge_wait <arm>
  local arm="$1" mdir status started now
  mdir=$(sget "$arm" merge_run_dir)
  status=$(jq -r '.status' "$mdir/run_manifest.json" 2>/dev/null)
  case "$status" in
    complete)
      if merged_index_ok "$arm"; then
        log "[$arm] merge complete and index verified: total_size=$EXPECT_INDEX_BYTES entries=$EXPECT_INDEX_ENTRIES ($mdir)"
        sset "$arm" state EVAL_LAUNCH
      else
        fail_arm "$arm" "merge manifest complete but model.safetensors.index.json does not match the verified 3B shape (${EXPECT_INDEX_ENTRIES} entries / ${EXPECT_INDEX_BYTES} bytes)"
      fi
      ;;
    fail)
      fail_arm "$arm" "merge run failed ($mdir); log tail: $(tail -3 "$mdir"/logs/*.log 2>/dev/null | tr '\n' ' | ')"
      ;;
    running)
      started=$(sget "$arm" merge_started 0)
      now=$(date -u +%s)
      if (( now - started > MERGE_LIMIT_S )); then
        fail_arm "$arm" "merge exceeded $((MERGE_LIMIT_S / 60)) min ($mdir)"
      fi
      ;;
    *)
      log "[$arm] merge manifest unreadable status=$status ($mdir); re-checking next cycle"
      ;;
  esac
}

# ---------------------------------------------------------------------------
# Step 3: step-100 held-out eval on the arm's own vacated GPUs
# ---------------------------------------------------------------------------
write_claim() { # write_claim <node> <gpu> <label> <pid-or-null> <eval_run_dir>
  local payload
  payload=$(jq -nc --argjson gpu "$2" --arg run_id "$3" --argjson pid "$4" \
    --arg dir "$5" --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '{gpu:$gpu, run_id:$run_id, pid:$pid, eval_run_dir:$dir, written_utc:$ts,
      written_by:"scripts/m7_completion_chain.sh"}')
  printf '%s\n' "$payload" | ssh -o BatchMode=yes -o ConnectTimeout=25 "$1" \
    "mkdir -p '$CLAIMS_DIR' && cat > '$CLAIMS_DIR/${1}_gpu${2}.claim'"
}

remove_claim() { # remove_claim <node> <gpu>
  ssh -o BatchMode=yes -o ConnectTimeout=25 "$1" "rm -f '$CLAIMS_DIR/${1}_gpu${2}.claim'" \
    || log "WARN: could not remove claim ${1}_gpu${2} (will expire by age/pid)"
}

eval_launch() { # eval_launch <arm>
  local arm="$1" node cond tag label candidates g out rc run_dir pidf pid tries
  node="${EVAL_NODE[$arm]}"
  cond="${ARM_COND[$arm]}"
  tag="${ARM_TAG[$arm]}"
  label="m7_chain_${arm}_step100_eval"

  if [[ ! -s "checkpoints/m7/m7_virl_${arm}_seed1/global_step_100/actor/huggingface/config.json" ]]; then
    fail_arm "$arm" "merged HF dir lacks config.json; cannot evaluate"
    return 0
  fi

  if [[ -n "${EVAL_GPU_OVERRIDE[$arm]:-}" ]]; then
    candidates="${EVAL_GPU_OVERRIDE[$arm]}"
  else
    # the GPUs this arm itself vacated, from its own run manifest
    candidates=$(jq -r '.gpu_ids[]' "${TRAIN_RUN_DIR[$arm]}/run_manifest.json" | tr '\n' ' ')
  fi
  log "[$arm] eval launch: node=$node cond=$cond candidates=[$candidates]"

  for g in $candidates; do
    # 1. GPU-scope guard (compute apps + live-trainer manifests + claims)
    if ! "$PY" scripts/m7_gpu_occupancy_guard.py --node "$node" --gpus "$g" >> "$LOG" 2>&1; then
      log "[$arm] guard denied $node:$g; trying next candidate"
      continue
    fi
    # 2. reservation claim BEFORE launching (closes the TOCTOU window)
    if ! write_claim "$node" "$g" "$label" null ""; then
      log "[$arm] could not write claim on $node gpu$g; trying next candidate"
      continue
    fi
    # 3. re-check ignoring our own claim
    if ! "$PY" scripts/m7_gpu_occupancy_guard.py --node "$node" --gpus "$g" \
         --ignore-claim-run-id "$label" >> "$LOG" 2>&1; then
      log "[$arm] post-claim re-check denied $node:$g; releasing claim"
      remove_claim "$node" "$g"
      continue
    fi
    # 4. launch through the extended step-0 launcher with the step-0 override
    #    set (tmp/launch_m7_step0.sh), model path swapped to the merged ckpt
    local caption_env=""
    [[ "$cond" == caption ]] && caption_env="data/virl39k_caption_store_3b_main_v2.jsonl"
    out=$(VIRL_MANIFEST=data/virl39k_m7_heldout_v3_eval.jsonl \
          VIRL_SAMPLE_SPEC=reports/virl39k_m7_heldout_v3_sample.json \
          VIRL_SPLITS=train \
          VIRL_MODEL_PATH="checkpoints/m7/m7_virl_${arm}_seed1/global_step_100/actor/huggingface" \
          VIRL_MODEL_REVISION="m7_virl_${arm}_seed1@global_step_100" \
          VIRL_RUN_PREFIX=m7_step100_heldout \
          VIRL_JOB_TYPE=r3_m7_step100_heldout_arm_eval \
          ${caption_env:+VIRL_CAPTION_SHARDS="$caption_env"} \
          bash scripts/launch_virl39k_blind_v1_condition.sh "$node" "$g" "$cond" "$tag" 2>>"$LOG")
    rc=$?
    run_dir=$(printf '%s\n' "$out" | tail -1)
    log "[$arm] eval launcher rc=$rc run_dir=$run_dir"
    if [[ $rc -ne 0 || -z "$run_dir" || ! -f "$run_dir/run_manifest.json" ]]; then
      remove_claim "$node" "$g"
      log "[$arm] eval launch failed on $node:$g; trying next candidate"
      continue
    fi
    # 5. stamp the runner pid into the claim so it stays held past 30 min
    pidf="$run_dir/pids/${node}_gpu${g}.pid"
    pid=""
    for tries in 1 2 3 4 5 6; do
      [[ -s "$pidf" ]] && { pid=$(cat "$pidf"); break; }
      sleep 5
    done
    if [[ -n "$pid" && "$(pid_state "$node" "$pid")" == alive ]]; then
      write_claim "$node" "$g" "$label" "$pid" "$run_dir" \
        || log "WARN: [$arm] claim pid-stamp failed; claim expires in 30 min but the eval holds GPU memory by then"
      log "[$arm] eval running: $run_dir (node=$node gpu=$g pid=$pid)"
      sset "$arm" eval_run_dir "$run_dir"
      sset "$arm" eval_node_gpu "$node $g"
      sset "$arm" eval_started "$(date -u +%s)"
      sset "$arm" state EVAL_WAIT
      return 0
    else
      log "[$arm] eval runner pid not confirmed alive (pidf=$pidf pid='$pid'); releasing claim; manifest left for inspection: $run_dir"
      remove_claim "$node" "$g"
      if ! bump_retry "$arm" eval_launch_retries 5; then
        fail_arm "$arm" "eval launch failed 5 times"
      fi
      return 0
    fi
  done
  log "[$arm] no candidate GPU passed the guard this cycle; retrying next cycle"
  if ! bump_retry "$arm" eval_gpu_wait 72; then # 72 cycles * 5 min = 6 h
    fail_arm "$arm" "no eval GPU became free within 6 h of the arm finishing"
  fi
}

eval_wait() { # eval_wait <arm>
  local arm="$1" edir status started now ng rows
  edir=$(sget "$arm" eval_run_dir)
  status=$(jq -r '.status' "$edir/run_manifest.json" 2>/dev/null)
  case "$status" in
    complete)
      rows=$(wc -l < "$edir/per_item.jsonl" 2>/dev/null || echo 0)
      log "[$arm] eval complete: $edir per_item rows=$rows (expected $HELDOUT_ROWS; the readout gate is authoritative)"
      ng=$(sget "$arm" eval_node_gpu)
      [[ -n "$ng" ]] && remove_claim ${ng}
      sset "$arm" state DONE
      ;;
    fail)
      fail_arm "$arm" "step-100 eval failed ($edir); log tail: $(tail -3 "$edir"/logs/*.log 2>/dev/null | tr '\n' ' | ')"
      ng=$(sget "$arm" eval_node_gpu)
      [[ -n "$ng" ]] && remove_claim ${ng}
      ;;
    running)
      started=$(sget "$arm" eval_started 0)
      now=$(date -u +%s)
      if (( now - started > EVAL_LIMIT_S )); then
        fail_arm "$arm" "eval exceeded $((EVAL_LIMIT_S / 3600)) h ($edir)"
      fi
      ;;
    *)
      log "[$arm] eval manifest unreadable status=$status ($edir); re-checking next cycle"
      ;;
  esac
}

# ---------------------------------------------------------------------------
# Step 4: full R3 readout
# ---------------------------------------------------------------------------
run_readout() {
  local rc args=() arm
  for arm in "${ARMS[@]}"; do
    args+=(--step0 "$arm=${STEP0_RUN_DIR[$arm]}")
  done
  for arm in "${ARMS[@]}"; do
    args+=(--step100 "$arm=$(sget "$arm" eval_run_dir)")
  done
  log "READOUT: all four step-100 evals complete; running scripts/build_m7_r3_readout.py (full mode)"
  log "READOUT invocation: ${args[*]}"
  PYTHONPATH=. "$PY" scripts/build_m7_r3_readout.py "${args[@]}" \
    --json-output reports/m7_r3_readout_v1.json \
    --markdown-output reports/m7_r3_readout_v1.md \
    --artifact-dir reports/m7_r3_readout_v1_artifacts >> "$LOG" 2>&1
  rc=$?
  if [[ $rc -eq 0 ]]; then
    log "READOUT complete rc=0: $(sha256sum reports/m7_r3_readout_v1.json reports/m7_r3_readout_v1.md | tr '\n' ' | ')"
  else
    log "READOUT rc=$rc: the script is fail-closed and fixture-validated; this refusal IS the logged result -- not bypassing"
  fi
  return $rc
}

# ---------------------------------------------------------------------------
# Waiter
# ---------------------------------------------------------------------------
tick_arm() { # one state-machine step for one arm
  local arm="$1" state run_dir node pid ps step
  state=$(sget "$arm" state)
  case "$state" in
    TRAIN_WAIT)
      run_dir="${TRAIN_RUN_DIR[$arm]}"
      node=$(jq -r '.node' "$run_dir/run_manifest.json")
      step=$(jq -r '.last_global_step' "checkpoints/m7/m7_virl_${arm}_seed1/checkpoint_tracker.json" 2>/dev/null)
      pid=$(cat "$run_dir"/pids/*.pid 2>/dev/null | head -1)
      if [[ "$step" == "100" ]]; then
        ps=$(pid_state "$node" "$pid")
        if [[ "$ps" == dead ]]; then
          log "[$arm] tracker=100 and trainer pid $pid has exited on $node -> CLOSE"
          sset "$arm" state CLOSE
        else
          log "[$arm] tracker=100 but trainer pid $pid is $ps on $node; waiting"
        fi
      else
        log "[$arm] TRAIN_WAIT tracker=$step pid=$pid"
        if (( $(date -u +%s) - WAITER_START > TRAIN_WAIT_LIMIT_S )); then
          fail_arm "$arm" "trainer did not reach step 100 within 30 h (tracker=$step)"
        fi
      fi
      ;;
    CLOSE)        close_arm "$arm" ;;
    MERGE_LAUNCH) merge_launch "$arm" ;;
    MERGE_WAIT)   merge_wait "$arm" ;;
    EVAL_LAUNCH)  eval_launch "$arm" ;;
    EVAL_WAIT)    eval_wait "$arm" ;;
    DONE | FAILED) : ;;
    *) fail_arm "$arm" "unknown state '$state'" ;;
  esac
}

run_waiter() {
  # single-instance guard
  if [[ -s "$PID_FILE" ]]; then
    local oldhost oldpid
    read -r oldhost oldpid < "$PID_FILE"
    if [[ -n "${oldpid:-}" && "$(pid_state "$oldhost" "$oldpid")" == alive ]]; then
      echo "waiter already running on $oldhost pid $oldpid; refusing" >&2
      exit 3
    fi
  fi
  printf '%s %s\n' "$(hostname)" "$$" > "$PID_FILE"
  WAITER_START=$(date -u +%s)
  log "WAITER start host=$(hostname) pid=$$ git=$(git rev-parse HEAD) poll=${POLL_SECONDS}s train_wait_limit=30h global_limit=48h"
  local arm
  for arm in "${ARMS[@]}"; do
    log "[$arm] initial state=$(sget "$arm" state) train_run=${TRAIN_RUN_DIR[$arm]} step0=${STEP0_RUN_DIR[$arm]}"
  done

  while :; do
    local all_done=1 any_failed=0 states=""
    for arm in "${ARMS[@]}"; do
      tick_arm "$arm"
      local s
      s=$(sget "$arm" state)
      states+="$arm=$s "
      [[ "$s" == DONE ]] || all_done=0
      [[ "$s" == FAILED ]] && any_failed=1
    done
    log "HEARTBEAT $states"
    if [[ $all_done -eq 1 ]]; then
      run_readout
      local rc=$?
      log "WAITER exiting rc=$rc (chain complete)"
      rm -f "$PID_FILE"
      exit $rc
    fi
    if [[ $any_failed -eq 1 ]]; then
      # keep driving the healthy arms, but if every remaining arm is terminal
      # (DONE or FAILED) the readout can never run: stop loudly.
      local live=0
      for arm in "${ARMS[@]}"; do
        s=$(sget "$arm" state)
        [[ "$s" != DONE && "$s" != FAILED ]] && live=1
      done
      if [[ $live -eq 0 ]]; then
        log "GIVING UP LOUDLY: at least one arm FAILED and no arm is still progressing; the full R3 readout cannot run. States: $states"
        rm -f "$PID_FILE"
        exit 5
      fi
    fi
    if (( $(date -u +%s) - WAITER_START > GLOBAL_LIMIT_S )); then
      log "GIVING UP LOUDLY: global 48 h deadline exceeded. States: $states"
      rm -f "$PID_FILE"
      exit 4
    fi
    sleep "$POLL_SECONDS"
  done
}

# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------
case "${1:-}" in
  launch-a1)
    init_states
    WAITER_START=$(date -u +%s)
    log "LAUNCH-A1 invoked on $(hostname) git=$(git rev-parse HEAD)"
    if [[ "$(sget a1_real state)" != EVAL_LAUNCH ]]; then
      log "LAUNCH-A1: a1_real state is $(sget a1_real state), not EVAL_LAUNCH; nothing to do"
      exit 0
    fi
    eval_launch a1_real
    if [[ "$(sget a1_real state)" != EVAL_WAIT ]]; then
      log "LAUNCH-A1: launch did not reach EVAL_WAIT (state=$(sget a1_real state))"
      exit 1
    fi
    # verify the eval gets past manifest load and starts generating
    edir=$(sget a1_real eval_run_dir)
    ng=$(sget a1_real eval_node_gpu)
    elog="$edir/logs/${ng// /_gpu}.log"
    for i in $(seq 1 30); do
      if grep -aq '"processed"' "$elog" 2>/dev/null; then
        log "LAUNCH-A1: eval is generating: $(grep -a '"processed"' "$elog" | tail -1)"
        echo "$edir"
        exit 0
      fi
      if [[ "$(jq -r '.status' "$edir/run_manifest.json")" == fail ]]; then
        log "LAUNCH-A1: eval failed during startup; see $elog"
        exit 1
      fi
      sleep 30
    done
    log "LAUNCH-A1: no generation progress after 15 min; see $elog"
    exit 1
    ;;
  run)
    init_states
    run_waiter
    ;;
  status)
    for arm in "${ARMS[@]}"; do
      printf '%-12s %-12s merge=%s eval=%s\n' "$arm" "$(sget "$arm" state -)" \
        "$(sget "$arm" merge_run_dir -)" "$(sget "$arm" eval_run_dir -)"
    done
    [[ -s "$PID_FILE" ]] && echo "waiter: $(cat "$PID_FILE")"
    ;;
  *)
    echo "usage: $0 {launch-a1|run|status}" >&2
    exit 2
    ;;
esac
