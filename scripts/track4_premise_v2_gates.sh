#!/usr/bin/env bash
# =============================================================================
# track4_premise_v2_gates.sh — GPU acceptance-gate runner for the track-4
# premise-construct v2 dev batch (data/track4_premise_v2_dev_v1).
#
# WHAT THIS RUNS
#   The four acceptance gates registered in
#   docs/registered_track4_premise_v2_design_v1.md section 7 (I14), in the
#   registered order, strictly sequentially, on exactly ONE GPU (an29 gpu 2):
#
#     E1  difficulty band   : 2x scripts/eval_qwen_vl_fliptrack.py, --image-mode real
#                             (manifest_premise_probe.jsonl, manifest_causal_pairs.jsonl)
#     E2  blind floor       : the same two commands x {no_image, gray} (4 runs)
#     E3  caption stress    : launch_caption_store_shards.sh -> launch_caption_store_merge.sh
#                             -> build_caption_qa_pairs.py -> eval_caption_qa_fliptrack.py
#     E4  attacker check    : launch_artifact_gate_v02.sh (DINOv2 + pixel-stat attackers)
#
# WHAT THIS DOES NOT DO
#   * It does not interpret results.  It RUNS the registered commands and
#     RECORDS raw outputs, return codes, run dirs, node, git hash and UTC
#     times.  Pass/fail judgment against the section-7 criteria is NOT computed
#     here and no criterion is restated as a threshold check in this file.
#   * It does not train anything and launches no training config.  The only
#     GPU work is the four registered gates, all on an29 gpu 2.
#   * It does not fill per-group q_real/q_blind and does not flip
#     blind_solvability.measurement_state in groups_v2.jsonl.  Section 7 refers
#     to "a rescore script" but never names one, and no script on disk
#     implements that flip for the v2 intervention groups (verified 2026-08-11).
#     Judgment is therefore deferred: raw metrics.json files are recorded and
#     data/track4_premise_v2_dev_v1/groups_v2.jsonl is left untouched.
#     If the registration later names such a script, set RESCORE_SCRIPT below;
#     a named-but-missing script is a hard failure (fail-closed).
#
# FAIL-CLOSED SEMANTICS
#   * Preflight (CPU only, before any GPU claim) refuses on: wrong host,
#     missing registered input/model/script, an output path that already
#     exists, a second concurrent runner, or missing jq/venv.
#   * GPU use is guarded exactly as scripts/launch_m7_seed2_eval.sh does:
#     m7_gpu_occupancy_guard.py -> write /dev/shm claim -> guard re-check with
#     --ignore-claim-run-id.  The claim is re-stamped with the live remote pid
#     after each launch and refreshed while waiting, so it holds past the
#     30-minute expiry.  The claim is released on every exit path.
#   * Every step's rc is checked.  A nonzero rc (or a timeout, or a remote pid
#     that dies without writing an rc) logs FAILED, stops the chain, releases
#     the claim, writes the provenance report, and exits 1.  Later gates are
#     NOT attempted after a failure.
#
# MECHANICS NOT FIXED BY THE REGISTRATION (recorded, criteria untouched)
#   * Section 7 writes bare `python`; repo convention is
#     .venv/bin/python with PYTHONPATH=. TRANSFORMERS_OFFLINE=1
#     HF_HOME=$ROOT/artifacts/hf_home CUDA_VISIBLE_DEVICES=2.
#   * eval_qwen_vl_fliptrack.py has no node/GPU placement of its own, so this
#     runner dispatches it to an29 via ssh + nohup and polls an rc file on the
#     shared filesystem.  This script itself must run on a LOGIN node.
#   * E2 says "repeat both E1 commands" with other --image-mode values but
#     registers no distinct output paths (verbatim repetition would refuse to
#     overwrite E1's predictions).  Resolution: sibling subdirectories under
#     the same run dir (premise_probe_no_image/, final_gray/, ...).  Flags and
#     pass criteria are untouched.
#   * E3's launcher defaults GPU_LIST to "0 1 2 3 4 5 6 7"; this runner passes
#     NUM_SHARDS=1 and GPU_LIST="2" so it cannot seize a neighbour's GPUs.
#     MAX_NEW_TOKENS stays at the launcher default (384), as the registered
#     command's trailing args stop at <run_dir>.
#   * E3's merge/QA-build inputs (--release-manifest/--key-file/--summary) are
#     not spelled out in section 7; the only release+key pair in the batch is
#     attacker_release/manifest.jsonl + attacker_key.jsonl.  A CPU preflight
#     checks that those files carry the fields build_caption_qa_pairs.py and
#     merge_caption_stores.py require; if they do not, E3 is recorded BLOCKED
#     and the chain stops there rather than spending GPU hours on a caption
#     store whose registered consumer cannot read this batch.  No substitute
#     script is chosen here — that is an orchestrator decision, not a rerun.
#
# USAGE (do not run in the foreground; long GPU work must be detached):
#   setsid nohup bash /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/\
# BlindGain/scripts/track4_premise_v2_gates.sh </dev/null >/dev/null 2>&1 & disown
#
# OUTPUTS
#   logs/track4_gates/<RUN>.log            runner log (+ per-step .log files)
#   experiments/runs/<RUN>/...             predictions/metrics per gate step
#   reports/track4_premise_v2_gates_run_provenance_v1.json   provenance
# =============================================================================
set -uo pipefail

ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || { echo "cannot cd $ROOT" >&2; exit 1; }
export PATH="$HOME/.local/bin:$PATH"

PY=.venv/bin/python
NODE=an29
GPU=2
LABEL=track4_premise_v2_gates
CLAIMS_DIR=/dev/shm/blind-gains/gpu_claims
CLAIM_PATH="$CLAIMS_DIR/${NODE}_gpu${GPU}.claim"
SSH_OPTS=(-o BatchMode=yes -o ConnectTimeout=25)

BASE=artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct
CAPTIONER=artifacts/models/Qwen/Qwen2.5-VL-7B-Instruct
DATA=data/track4_premise_v2_dev_v1
REGISTRATION=docs/registered_track4_premise_v2_design_v1.md

# Section 7 names no rescore/audit script and none exists on disk; leave empty.
RESCORE_SCRIPT=""

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN="track4_premise_v2_gates_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN}"
CAP_RUN_DIR="experiments/runs/track4_premise_v2_caption_store_${NODE}_${STAMP}"
LOG_DIR=logs/track4_gates
LOG="${LOG_DIR}/${RUN}.log"
STEPS_FILE="${RUN_DIR}/steps.jsonl"
PROVENANCE=reports/track4_premise_v2_gates_run_provenance_v1.json
LOCK_DIR="${LOG_DIR}/.runner_lock"

POLL_SECONDS=30
CLAIM_REFRESH_SECONDS=600
LIVENESS_SECONDS=300
EVAL_TIMEOUT_SECONDS=21600     # 6 h per 3B eval step
CAPTION_TIMEOUT_SECONDS=43200  # 12 h for the 7B caption store (640 images, 1 GPU)
ATTACKER_TIMEOUT_SECONDS=21600 # 6 h for the artifact gate

CLAIM_HELD=0
CHAIN_STATUS=running
CHAIN_FAILED_STEP=""

mkdir -p "$LOG_DIR" || { echo "cannot mkdir $LOG_DIR" >&2; exit 1; }

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >> "$LOG"; }
utc() { date -u +%Y-%m-%dT%H:%M:%SZ; }

cleanup_lock() { rmdir "$LOCK_DIR" 2>/dev/null || true; }

# --- provenance -------------------------------------------------------------
record_step() {
  # name gate registered_ref command start end rc status log artifacts_json
  jq -nc \
    --arg step "$1" --arg gate "$2" --arg ref "$3" --arg command "$4" \
    --arg start "$5" --arg end "$6" --argjson rc "$7" --arg status "$8" \
    --arg steplog "$9" --argjson artifacts "${10}" \
    --arg node "$NODE" --argjson gpu "$GPU" \
    '{step:$step, gate:$gate, registered_ref:$ref, node:$node, gpu:$gpu,
      command:$command, start_utc:$start, end_utc:$end, rc:$rc,
      status:$status, log:$steplog, artifacts:$artifacts}' >> "$STEPS_FILE"
}

write_provenance() {
  local dirty steps_arg
  dirty="$(git status --porcelain | jq -Rsc 'split("\n") | map(select(length > 0))')"
  [[ -s "$STEPS_FILE" ]] || printf '' > "$STEPS_FILE"
  steps_arg="$STEPS_FILE"
  jq -n \
    --arg schema "blind-gains.track4-premise-v2-gates-run-provenance.v1" \
    --arg run_id "$RUN" \
    --arg registration "$REGISTRATION" \
    --arg registration_section "7 (I14) acceptance gates E1-E4" \
    --arg root "$ROOT" \
    --arg launch_host "$(hostname)" \
    --arg node "$NODE" \
    --argjson gpu "$GPU" \
    --arg git_hash "$GIT_HASH" \
    --argjson git_dirty "$dirty" \
    --arg base_model "$BASE" \
    --arg captioner "$CAPTIONER" \
    --arg data "$DATA" \
    --arg run_dir "$RUN_DIR" \
    --arg caption_run_dir "$CAP_RUN_DIR" \
    --arg merge_run_dir "${MERGE_RUN_DIR:-}" \
    --arg attacker_run_dir "${ATTACKER_RUN_DIR:-}" \
    --arg runner "scripts/track4_premise_v2_gates.sh" \
    --arg claim_path "$CLAIM_PATH" \
    --arg claim_run_id "$LABEL" \
    --arg log "$LOG" \
    --arg start_utc "$RUN_START_UTC" \
    --arg end_utc "$(utc)" \
    --arg status "$CHAIN_STATUS" \
    --arg failed_step "$CHAIN_FAILED_STEP" \
    --slurpfile steps "$steps_arg" \
    '{
      schema_version: $schema,
      run_id: $run_id,
      job_type: "track4_premise_v2_acceptance_gates_e1_e4",
      registration: {document: $registration, section: $registration_section},
      runner_script: $runner,
      root: $root,
      launch_host: $launch_host,
      node: $node,
      gpu: $gpu,
      gpu_claim: {path: $claim_path, run_id: $claim_run_id},
      git_hash: $git_hash,
      git_dirty_paths: $git_dirty,
      base_model: $base_model,
      captioner_model: $captioner,
      data_batch: $data,
      run_dir: $run_dir,
      caption_store_run_dir: $caption_run_dir,
      caption_merge_run_dir: (if $merge_run_dir == "" then null else $merge_run_dir end),
      attacker_gate_run_dir: (if $attacker_run_dir == "" then null else $attacker_run_dir end),
      runner_log: $log,
      start_utc: $start_utc,
      end_utc: $end_utc,
      chain_status: $status,
      failed_step: (if $failed_step == "" then null else $failed_step end),
      steps: $steps,
      judgment: {
        computed_here: false,
        note: "Runner records raw outputs only. Section-7 pass criteria are not evaluated in this script and no result is interpreted here."
      },
      rescore_step: {
        named_by_registration: false,
        script: null,
        ran: false,
        note: "Section 7 refers to an unnamed rescore script for per-group q_real/q_blind and the measurement_state flip; no such script exists on disk. groups_v2.jsonl left untouched; judgment deferred."
      },
      resolutions: [
        "E2 output paths: sibling subdirectories under the same run dir (section 7 registers none; verbatim repetition would refuse to overwrite E1 outputs).",
        "E1/E2 executed with .venv/bin/python, PYTHONPATH=., TRANSFORMERS_OFFLINE=1, HF_HOME=artifacts/hf_home, CUDA_VISIBLE_DEVICES=2, dispatched to an29 (section 7 writes bare python and fixes no placement).",
        "E3 shards=1 and GPU_LIST=\"2\" so the caption store stays inside the one-GPU budget; MAX_NEW_TOKENS left at the launcher default 384.",
        "E3 merge/QA inputs resolved to the batch attacker_release/manifest.jsonl + attacker_key.jsonl (section 7 does not spell them out).",
        "E4 node/gpu resolved to an29 2 per the one-GPU budget."
      ]
    }' > "${PROVENANCE}.partial" \
    && mv "${PROVENANCE}.partial" "$PROVENANCE"
}

# --- claim handling (pattern copied from scripts/launch_m7_seed2_eval.sh) ----
write_claim() {
  # write_claim <pid-or-null> <eval_run_dir>
  local pid="${1:-null}" dir="${2:-}" payload
  [[ "$pid" =~ ^[0-9]+$ ]] || pid=null
  payload=$(jq -nc --argjson gpu "$GPU" --arg run_id "$LABEL" --argjson pid "$pid" \
    --arg dir "$dir" --arg ts "$(utc)" \
    '{gpu:$gpu, run_id:$run_id, pid:$pid, eval_run_dir:$dir, written_utc:$ts,
      written_by:"scripts/track4_premise_v2_gates.sh"}')
  # remote stdout is folded into the log: these helpers are called from inside
  # command substitutions whose stdout carries a step return code.
  printf '%s\n' "$payload" | ssh "${SSH_OPTS[@]}" "$NODE" \
    "mkdir -p '$CLAIMS_DIR' && cat > '$CLAIM_PATH'" >> "$LOG" 2>&1
}

release_claim() {
  if [[ "$CLAIM_HELD" -eq 1 ]]; then
    ssh -o ConnectTimeout=25 "$NODE" "rm -f '$CLAIM_PATH'" >> "$LOG" 2>&1 && CLAIM_HELD=0
    log "claim released: $NODE:$CLAIM_PATH"
  fi
}

fail_stop() {
  # fail_stop <step-name> <message>
  CHAIN_STATUS=failed
  CHAIN_FAILED_STEP="$1"
  log "FAILED [$1]: $2"
  log "chain stopped; no later gate attempted"
  release_claim
  write_provenance
  cleanup_lock
  log "provenance: $PROVENANCE"
  exit 1
}

kill_remote_pid() {
  local pid="$1"
  [[ "$pid" =~ ^[0-9]+$ ]] || return 0
  # pid-scoped only: never a name pattern (a name pattern would match this session)
  ssh "${SSH_OPTS[@]}" "$NODE" "pkill -TERM -P $pid; kill -TERM $pid" >/dev/null 2>&1
  log "sent TERM to remote pid $pid and its children on $NODE"
}

# --- preflight (CPU only, no GPU claimed yet) -------------------------------
RUN_START_UTC="$(utc)"
log "=== track4 premise-v2 acceptance gates E1-E4 ==="
log "runner=scripts/track4_premise_v2_gates.sh run_id=$RUN"
log "registration=$REGISTRATION section 7 (I14); runs and records only, no interpretation"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  log "PREFLIGHT REFUSE: another gate runner holds $LOCK_DIR"
  exit 75
fi
trap cleanup_lock EXIT

HOST="$(hostname)"
case "$HOST" in
  ln*) : ;;
  *) log "PREFLIGHT REFUSE: must run on a login node (got $HOST); GPU work is dispatched to $NODE by ssh"
     cleanup_lock; exit 2 ;;
esac

command -v jq >/dev/null 2>&1 || { log "PREFLIGHT REFUSE: jq not on PATH"; cleanup_lock; exit 2; }
[[ -x "$PY" ]] || { log "PREFLIGHT REFUSE: missing $PY"; cleanup_lock; exit 2; }

GIT_HASH="$(git rev-parse HEAD)"
[[ -n "$GIT_HASH" ]] || { log "PREFLIGHT REFUSE: cannot read git HEAD"; cleanup_lock; exit 2; }
log "git_hash=$GIT_HASH host=$HOST node=$NODE gpu=$GPU"

for required in \
  "$REGISTRATION" \
  "$DATA/manifest_premise_probe.jsonl" \
  "$DATA/manifest_causal_pairs.jsonl" \
  "$DATA/attacker_release/manifest.jsonl" \
  "$DATA/attacker_key.jsonl" \
  scripts/m7_gpu_occupancy_guard.py \
  scripts/eval_qwen_vl_fliptrack.py \
  scripts/eval_caption_qa_fliptrack.py \
  scripts/build_caption_qa_pairs.py \
  scripts/launch_caption_store_shards.sh \
  scripts/launch_caption_store_merge.sh \
  scripts/launch_artifact_gate_v02.sh
do
  [[ -f "$required" ]] || { log "PREFLIGHT REFUSE: missing $required"; cleanup_lock; exit 2; }
done
for required_dir in "$BASE" "$CAPTIONER" "$DATA/images"; do
  [[ -d "$required_dir" ]] || { log "PREFLIGHT REFUSE: missing $required_dir"; cleanup_lock; exit 2; }
done

for collision in "$RUN_DIR" "$CAP_RUN_DIR" "$PROVENANCE" reports/track4_premise_v2_attacker_gate_v1.json; do
  [[ -e "$collision" ]] && { log "PREFLIGHT REFUSE: output path already exists: $collision"; cleanup_lock; exit 2; }
done

if [[ -n "$RESCORE_SCRIPT" && ! -f "$RESCORE_SCRIPT" ]]; then
  log "PREFLIGHT REFUSE: RESCORE_SCRIPT=$RESCORE_SCRIPT named but not on disk"
  cleanup_lock; exit 2
fi

mkdir -p "$RUN_DIR"/{cmds,rc,pids} || { log "PREFLIGHT REFUSE: cannot create $RUN_DIR"; cleanup_lock; exit 2; }
: > "$STEPS_FILE"

# E3 downstream input contract: merge_caption_stores.py needs members[].image_sha256
# on the release manifest; build_caption_qa_pairs.py additionally needs release
# .question and key .source_pair_id + members[].answer.  Checked on CPU up front so
# a caption store is not built for a consumer that cannot read this batch.
E3_CONTRACT_OK=1
E3_CONTRACT_MISSING=""
if ! head -1 "$DATA/attacker_release/manifest.jsonl" \
    | jq -e 'has("question") and (.members[0] | has("image_sha256"))' >/dev/null 2>&1; then
  E3_CONTRACT_OK=0
  E3_CONTRACT_MISSING="attacker_release/manifest.jsonl lacks question and/or members[].image_sha256"
fi
if ! head -1 "$DATA/attacker_key.jsonl" \
    | jq -e 'has("source_pair_id") and (.members[0] | has("answer"))' >/dev/null 2>&1; then
  E3_CONTRACT_OK=0
  E3_CONTRACT_MISSING="${E3_CONTRACT_MISSING:+$E3_CONTRACT_MISSING; }attacker_key.jsonl lacks source_pair_id and/or members[].answer"
fi
log "preflight e3_qa_input_contract ok=$E3_CONTRACT_OK ${E3_CONTRACT_MISSING:-}"
record_step "preflight_e3_qa_input_contract" "E3" "$REGISTRATION#7-E3" \
  "jq field check on $DATA/attacker_release/manifest.jsonl and $DATA/attacker_key.jsonl" \
  "$RUN_START_UTC" "$(utc)" "$([[ $E3_CONTRACT_OK -eq 1 ]] && echo 0 || echo 1)" \
  "$([[ $E3_CONTRACT_OK -eq 1 ]] && echo ok || echo blocked)" "$LOG" \
  "$(jq -nc --arg m "${E3_CONTRACT_MISSING:-}" '{missing_fields: (if $m == "" then null else $m end)}')"

# --- step 0: guard -> claim -> re-check (TOCTOU discipline) ------------------
S=$(utc)
"$PY" scripts/m7_gpu_occupancy_guard.py --node "$NODE" --gpus "$GPU" >> "$LOG" 2>&1
rc=$?
record_step "gpu_guard_precheck" "step0" "CLAUDE.md guarded free-GPU discipline" \
  "$PY scripts/m7_gpu_occupancy_guard.py --node $NODE --gpus $GPU" \
  "$S" "$(utc)" "$rc" "$([[ $rc -eq 0 ]] && echo ok || echo failed)" "$LOG" 'null'
[[ $rc -eq 0 ]] || fail_stop "gpu_guard_precheck" "guard denied $NODE:$GPU (rc=$rc)"

S=$(utc)
write_claim null "$RUN_DIR"
rc=$?
record_step "gpu_claim_write" "step0" "scripts/launch_m7_seed2_eval.sh claim pattern" \
  "write $CLAIM_PATH on $NODE (run_id=$LABEL)" "$S" "$(utc)" "$rc" \
  "$([[ $rc -eq 0 ]] && echo ok || echo failed)" "$LOG" 'null'
[[ $rc -eq 0 ]] || fail_stop "gpu_claim_write" "claim write failed (rc=$rc)"
CLAIM_HELD=1
log "claim written: $NODE:$CLAIM_PATH run_id=$LABEL"

S=$(utc)
"$PY" scripts/m7_gpu_occupancy_guard.py --node "$NODE" --gpus "$GPU" \
  --ignore-claim-run-id "$LABEL" >> "$LOG" 2>&1
rc=$?
record_step "gpu_guard_recheck" "step0" "CLAUDE.md guarded free-GPU discipline" \
  "$PY scripts/m7_gpu_occupancy_guard.py --node $NODE --gpus $GPU --ignore-claim-run-id $LABEL" \
  "$S" "$(utc)" "$rc" "$([[ $rc -eq 0 ]] && echo ok || echo failed)" "$LOG" 'null'
[[ $rc -eq 0 ]] || fail_stop "gpu_guard_recheck" "post-claim re-check denied $NODE:$GPU (rc=$rc)"

# --- remote GPU step helpers ------------------------------------------------
remote_pid=""

launch_remote_gpu_cmd() {
  # launch_remote_gpu_cmd <step-name> <command-string>
  local name="$1" cmd="$2"
  local wrapper="${RUN_DIR}/cmds/${name}.sh"
  local rcfile="${ROOT}/${RUN_DIR}/rc/${name}.rc"
  local pidfile="${ROOT}/${RUN_DIR}/pids/${name}.pid"
  local steplog="${ROOT}/${LOG_DIR}/${RUN}.${name}.log"

  cat > "$wrapper" <<WRAPPER
#!/usr/bin/env bash
# generated by scripts/track4_premise_v2_gates.sh for step ${name}
cd ${ROOT} || exit 1
export PYTHONUNBUFFERED=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=${ROOT}/artifacts/hf_home
export CUDA_VISIBLE_DEVICES=${GPU}
export PYTHONPATH=.
set +e
${cmd}
rc=\$?
printf '%s\n' "\$rc" > ${rcfile}
exit \$rc
WRAPPER
  chmod +x "$wrapper"

  ssh "${SSH_OPTS[@]}" "$NODE" \
    "cd '$ROOT' && (nohup bash '${ROOT}/${wrapper}' > '${steplog}' 2>&1 < /dev/null & echo \$! > '${pidfile}')" \
    >> "$LOG" 2>&1
  local ssh_rc=$?
  remote_pid=""
  local attempt
  for attempt in 1 2 3 4 5; do
    remote_pid="$(head -1 "${RUN_DIR}/pids/${name}.pid" 2>/dev/null || true)"
    [[ "$remote_pid" =~ ^[0-9]+$ ]] && break
    sleep 2
  done
  [[ "$remote_pid" =~ ^[0-9]+$ ]] || remote_pid=""
  return $ssh_rc
}

wait_for_rc_file() {
  # wait_for_rc_file <step-name> <pid> <timeout-seconds>; echoes the rc
  local name="$1" pid="$2" timeout="$3"
  local rcfile="${RUN_DIR}/rc/${name}.rc"
  local waited=0 since_refresh=0 since_liveness=0
  while true; do
    if [[ -s "$rcfile" ]]; then head -1 "$rcfile"; return 0; fi
    sleep "$POLL_SECONDS"
    waited=$((waited + POLL_SECONDS))
    since_refresh=$((since_refresh + POLL_SECONDS))
    since_liveness=$((since_liveness + POLL_SECONDS))
    if [[ $since_refresh -ge $CLAIM_REFRESH_SECONDS ]]; then
      write_claim "$pid" "$RUN_DIR"; since_refresh=0
    fi
    if [[ $since_liveness -ge $LIVENESS_SECONDS ]]; then
      since_liveness=0
      if ! ssh "${SSH_OPTS[@]}" "$NODE" "kill -0 $pid" >/dev/null 2>&1; then
        sleep 15
        if [[ -s "$rcfile" ]]; then head -1 "$rcfile"; return 0; fi
        log "[$name] remote pid $pid is gone and no rc file was written"
        echo 253; return 0
      fi
    fi
    if [[ $waited -ge $timeout ]]; then
      log "[$name] timeout after ${waited}s"
      kill_remote_pid "$pid"
      echo 254; return 0
    fi
  done
}

wait_for_manifest_status() {
  # wait_for_manifest_status <step-name> <manifest-path> <pid-glob-dir> <timeout>; echoes rc
  local name="$1" manifest="$2" piddir="$3" timeout="$4"
  local waited=0 since_refresh=0 status pid
  while true; do
    if [[ -s "$manifest" ]]; then
      status="$(jq -r '.status // "running"' "$manifest" 2>/dev/null || echo running)"
      case "$status" in
        complete) echo 0; return 0 ;;
        fail)     log "[$name] run manifest status=fail ($manifest)"; echo 252; return 0 ;;
      esac
    fi
    sleep "$POLL_SECONDS"
    waited=$((waited + POLL_SECONDS))
    since_refresh=$((since_refresh + POLL_SECONDS))
    if [[ $since_refresh -ge $CLAIM_REFRESH_SECONDS ]]; then
      pid="$(cat "$piddir"/*.pid 2>/dev/null | head -1 || true)"
      write_claim "${pid:-null}" "$RUN_DIR"; since_refresh=0
    fi
    if [[ $waited -ge $timeout ]]; then
      log "[$name] timeout after ${waited}s waiting on $manifest"
      pid="$(cat "$piddir"/*.pid 2>/dev/null | head -1 || true)"
      [[ -n "${pid:-}" ]] && kill_remote_pid "$pid"
      echo 254; return 0
    fi
  done
}

run_gpu_step() {
  # run_gpu_step <step-name> <gate> <registered-ref> <timeout> <artifacts-json> <command>
  local name="$1" gate="$2" ref="$3" timeout="$4" artifacts="$5" cmd="$6"
  local start end step_rc
  start="$(utc)"
  log "[$gate/$name] START on $NODE gpu $GPU: $cmd"
  launch_remote_gpu_cmd "$name" "$cmd"
  if [[ $? -ne 0 || -z "$remote_pid" ]]; then
    record_step "$name" "$gate" "$ref" "$cmd" "$start" "$(utc)" 251 "launch_failed" \
      "${LOG_DIR}/${RUN}.${name}.log" "$artifacts"
    fail_stop "$name" "could not launch on $NODE (ssh rc or empty pid)"
  fi
  log "[$gate/$name] launched pid=$remote_pid log=${LOG_DIR}/${RUN}.${name}.log"
  write_claim "$remote_pid" "$RUN_DIR"
  step_rc="$(wait_for_rc_file "$name" "$remote_pid" "$timeout")"
  end="$(utc)"
  record_step "$name" "$gate" "$ref" "$cmd" "$start" "$end" "${step_rc:-255}" \
    "$([[ "${step_rc:-255}" == "0" ]] && echo ok || echo failed)" \
    "${LOG_DIR}/${RUN}.${name}.log" "$artifacts"
  if [[ "${step_rc:-255}" != "0" ]]; then
    fail_stop "$name" "rc=${step_rc:-255}"
  fi
  log "[$gate/$name] DONE rc=0"
}

run_login_step() {
  # run_login_step <step-name> <gate> <registered-ref> <artifacts-json> <command>
  # CPU-only step executed on this login node; stdout/stderr appended to a step log.
  local name="$1" gate="$2" ref="$3" artifacts="$4" cmd="$5"
  local start end step_rc steplog="${LOG_DIR}/${RUN}.${name}.log"
  start="$(utc)"
  log "[$gate/$name] START (login $HOST): $cmd"
  ( cd "$ROOT" && eval "$cmd" ) >> "$steplog" 2>&1
  step_rc=$?
  end="$(utc)"
  record_step "$name" "$gate" "$ref" "$cmd" "$start" "$end" "$step_rc" \
    "$([[ $step_rc -eq 0 ]] && echo ok || echo failed)" "$steplog" "$artifacts"
  [[ $step_rc -eq 0 ]] || fail_stop "$name" "rc=$step_rc (see $steplog)"
  log "[$gate/$name] DONE rc=0"
}

# =============================================================================
# E1 — difficulty band (section 7, two registered commands, --image-mode real)
# =============================================================================
run_gpu_step "e1_premise_probe_real" "E1" "$REGISTRATION#7-E1-cmd1" \
  "$EVAL_TIMEOUT_SECONDS" \
  "$(jq -nc --arg p "$RUN_DIR/premise_probe/predictions.jsonl" --arg m "$RUN_DIR/premise_probe/metrics.json" '{predictions:$p, metrics:$m}')" \
  "$PY scripts/eval_qwen_vl_fliptrack.py --model-path $BASE \
  --manifest $DATA/manifest_premise_probe.jsonl \
  --output $RUN_DIR/premise_probe/predictions.jsonl \
  --metrics-output $RUN_DIR/premise_probe/metrics.json \
  --image-mode real --seed 0 --noise-seed 0 --max-new-tokens 32"

run_gpu_step "e1_final_real" "E1" "$REGISTRATION#7-E1-cmd2" \
  "$EVAL_TIMEOUT_SECONDS" \
  "$(jq -nc --arg p "$RUN_DIR/final/predictions.jsonl" --arg m "$RUN_DIR/final/metrics.json" '{predictions:$p, metrics:$m}')" \
  "$PY scripts/eval_qwen_vl_fliptrack.py --model-path $BASE \
  --manifest $DATA/manifest_causal_pairs.jsonl \
  --output $RUN_DIR/final/predictions.jsonl \
  --metrics-output $RUN_DIR/final/metrics.json \
  --image-mode real --seed 0 --noise-seed 0 --max-new-tokens 32"

# =============================================================================
# E2 — blind floor (both E1 commands x {no_image, gray}; output subdirs resolved)
# =============================================================================
for mode in no_image gray; do
  run_gpu_step "e2_premise_probe_${mode}" "E2" "$REGISTRATION#7-E2" \
    "$EVAL_TIMEOUT_SECONDS" \
    "$(jq -nc --arg p "$RUN_DIR/premise_probe_${mode}/predictions.jsonl" --arg m "$RUN_DIR/premise_probe_${mode}/metrics.json" '{predictions:$p, metrics:$m}')" \
    "$PY scripts/eval_qwen_vl_fliptrack.py --model-path $BASE \
  --manifest $DATA/manifest_premise_probe.jsonl \
  --output $RUN_DIR/premise_probe_${mode}/predictions.jsonl \
  --metrics-output $RUN_DIR/premise_probe_${mode}/metrics.json \
  --image-mode ${mode} --seed 0 --noise-seed 0 --max-new-tokens 32"

  run_gpu_step "e2_final_${mode}" "E2" "$REGISTRATION#7-E2" \
    "$EVAL_TIMEOUT_SECONDS" \
    "$(jq -nc --arg p "$RUN_DIR/final_${mode}/predictions.jsonl" --arg m "$RUN_DIR/final_${mode}/metrics.json" '{predictions:$p, metrics:$m}')" \
    "$PY scripts/eval_qwen_vl_fliptrack.py --model-path $BASE \
  --manifest $DATA/manifest_causal_pairs.jsonl \
  --output $RUN_DIR/final_${mode}/predictions.jsonl \
  --metrics-output $RUN_DIR/final_${mode}/metrics.json \
  --image-mode ${mode} --seed 0 --noise-seed 0 --max-new-tokens 32"
done

log "E1+E2 predictions and metrics recorded under $RUN_DIR (raw; no rescore, no measurement_state flip)"

# =============================================================================
# E3 — caption stress
# =============================================================================
if [[ $E3_CONTRACT_OK -ne 1 ]]; then
  record_step "e3_caption_store" "E3" "$REGISTRATION#7-E3" \
    "bash scripts/launch_caption_store_shards.sh $NODE 0 1 $CAPTIONER $DATA/images $CAP_RUN_DIR \"$GPU\"" \
    "$(utc)" "$(utc)" 250 "blocked_preflight" "$LOG" \
    "$(jq -nc --arg m "$E3_CONTRACT_MISSING" '{blocked_reason:$m}')"
  fail_stop "e3_caption_store" \
    "E3 blocked by preflight: the registered downstream consumers (merge_caption_stores.py --release-manifest, build_caption_qa_pairs.py) require fields this batch's release/key files do not carry ($E3_CONTRACT_MISSING); not spending GPU hours on an unusable chain, and not substituting another builder here"
fi

run_login_step "e3_caption_store_launch" "E3" "$REGISTRATION#7-E3" \
  "$(jq -nc --arg d "$CAP_RUN_DIR" '{caption_run_dir:$d}')" \
  "bash scripts/launch_caption_store_shards.sh $NODE 0 1 $CAPTIONER $DATA/images $CAP_RUN_DIR \"$GPU\""

S=$(utc)
CAP_MANIFEST="$CAP_RUN_DIR/run_manifest.json"
CAP_PID="$(cat "$CAP_RUN_DIR"/pids/*.pid 2>/dev/null | head -1 || true)"
write_claim "${CAP_PID:-null}" "$RUN_DIR"
log "[E3/e3_caption_store_wait] waiting on $CAP_MANIFEST (pid=${CAP_PID:-unknown})"
rc="$(wait_for_manifest_status "e3_caption_store_wait" "$CAP_MANIFEST" "$CAP_RUN_DIR/pids" "$CAPTION_TIMEOUT_SECONDS")"
record_step "e3_caption_store_wait" "E3" "$REGISTRATION#7-E3" \
  "poll $CAP_MANIFEST until status != running" "$S" "$(utc)" "${rc:-255}" \
  "$([[ "${rc:-255}" == "0" ]] && echo ok || echo failed)" "$LOG" \
  "$(jq -nc --arg s "$CAP_RUN_DIR/shards/store_shard_0.jsonl" '{shard:$s}')"
[[ "${rc:-255}" == "0" ]] || fail_stop "e3_caption_store_wait" "caption store did not complete (rc=${rc:-255})"

run_login_step "e3_caption_merge" "E3" "$REGISTRATION#7-E3" \
  "$(jq -nc --arg s "$CAP_RUN_DIR/shards/store_shard_0.jsonl" '{input_shard:$s}')" \
  "bash scripts/launch_caption_store_merge.sh track4_premise_v2_dev_v1 $DATA/attacker_release/manifest.jsonl $CAP_RUN_DIR/shards/store_shard_0.jsonl"

MERGE_RUN_DIR="$(tail -1 "${LOG_DIR}/${RUN}.e3_caption_merge.log" 2>/dev/null || true)"
if [[ -z "$MERGE_RUN_DIR" || ! -s "$MERGE_RUN_DIR/captions.jsonl" ]]; then
  record_step "e3_caption_merge_resolve" "E3" "$REGISTRATION#7-E3" \
    "resolve merged caption store from launch_caption_store_merge.sh stdout" \
    "$(utc)" "$(utc)" 249 "failed" "${LOG_DIR}/${RUN}.e3_caption_merge.log" \
    "$(jq -nc --arg d "${MERGE_RUN_DIR:-}" '{merge_run_dir:$d}')"
  fail_stop "e3_caption_merge_resolve" "merged caption store not found (merge_run_dir='${MERGE_RUN_DIR:-}')"
fi
log "[E3] merged caption store: $MERGE_RUN_DIR/captions.jsonl"

run_login_step "e3_build_caption_qa" "E3" "$REGISTRATION#7-E3" \
  "$(jq -nc --arg q "$RUN_DIR/caption_qa/qa.jsonl" --arg s "$RUN_DIR/caption_qa/qa_input_summary.json" '{qa:$q, summary:$s}')" \
  "$PY scripts/build_caption_qa_pairs.py --release-manifest $DATA/attacker_release/manifest.jsonl --key-file $DATA/attacker_key.jsonl --caption-store $MERGE_RUN_DIR/captions.jsonl --output $RUN_DIR/caption_qa/qa.jsonl --summary $RUN_DIR/caption_qa/qa_input_summary.json"

run_gpu_step "e3_caption_qa_eval" "E3" "$REGISTRATION#7-E3" \
  "$EVAL_TIMEOUT_SECONDS" \
  "$(jq -nc --arg p "$RUN_DIR/caption_qa/predictions.jsonl" --arg m "$RUN_DIR/caption_qa/metrics.json" '{predictions:$p, metrics:$m}')" \
  "$PY scripts/eval_caption_qa_fliptrack.py --model-path $BASE \
  --input $RUN_DIR/caption_qa/qa.jsonl \
  --output $RUN_DIR/caption_qa/predictions.jsonl \
  --metrics-output $RUN_DIR/caption_qa/metrics.json \
  --max-new-tokens 32"

# =============================================================================
# E4 — attacker check
# =============================================================================
run_login_step "e4_attacker_gate_launch" "E4" "$REGISTRATION#7-E4" \
  "$(jq -nc --arg o "reports/track4_premise_v2_attacker_gate_v1.json" '{report:$o}')" \
  "bash scripts/launch_artifact_gate_v02.sh $NODE $GPU $DATA/attacker_release $DATA/attacker_key.jsonl reports/track4_premise_v2_attacker_gate_v1.json"

ATTACKER_RUN_DIR="$(head -1 "${LOG_DIR}/${RUN}.e4_attacker_gate_launch.log" 2>/dev/null || true)"
if [[ -z "$ATTACKER_RUN_DIR" || ! -s "$ATTACKER_RUN_DIR/run_manifest.json" ]]; then
  record_step "e4_attacker_gate_resolve" "E4" "$REGISTRATION#7-E4" \
    "resolve attacker-gate run dir from launch_artifact_gate_v02.sh stdout" \
    "$(utc)" "$(utc)" 249 "failed" "${LOG_DIR}/${RUN}.e4_attacker_gate_launch.log" \
    "$(jq -nc --arg d "${ATTACKER_RUN_DIR:-}" '{attacker_run_dir:$d}')"
  fail_stop "e4_attacker_gate_resolve" "attacker-gate run dir not found (got '${ATTACKER_RUN_DIR:-}')"
fi
log "[E4] attacker gate run dir: $ATTACKER_RUN_DIR"

S=$(utc)
ATT_PID="$(cat "$ATTACKER_RUN_DIR"/pids/*.pid 2>/dev/null | head -1 || true)"
write_claim "${ATT_PID:-null}" "$RUN_DIR"
rc="$(wait_for_manifest_status "e4_attacker_gate_wait" "$ATTACKER_RUN_DIR/run_manifest.json" "$ATTACKER_RUN_DIR/pids" "$ATTACKER_TIMEOUT_SECONDS")"
record_step "e4_attacker_gate_wait" "E4" "$REGISTRATION#7-E4" \
  "poll $ATTACKER_RUN_DIR/run_manifest.json until status != running" "$S" "$(utc)" "${rc:-255}" \
  "$([[ "${rc:-255}" == "0" ]] && echo ok || echo failed)" "$LOG" \
  "$(jq -nc --arg o "reports/track4_premise_v2_attacker_gate_v1.json" '{report:$o}')"
[[ "${rc:-255}" == "0" ]] || fail_stop "e4_attacker_gate_wait" "attacker gate did not complete (rc=${rc:-255})"

# =============================================================================
# Registered rescore/audit step (only if the registration names one on disk)
# =============================================================================
if [[ -n "$RESCORE_SCRIPT" ]]; then
  run_login_step "registered_rescore" "post" "$REGISTRATION#7-E2-rescore" \
    "$(jq -nc --arg s "$RESCORE_SCRIPT" '{script:$s}')" \
    "$PY $RESCORE_SCRIPT"
else
  record_step "registered_rescore" "post" "$REGISTRATION#7-E2-rescore" \
    "none — section 7 names no rescore script and none exists on disk" \
    "$(utc)" "$(utc)" 'null' "not_run_registration_defers" "$LOG" \
    "$(jq -nc '{groups_file:"data/track4_premise_v2_dev_v1/groups_v2.jsonl", modified:false}')"
  log "no registered rescore script on disk; q_real/q_blind and measurement_state left untouched"
fi

CHAIN_STATUS=complete
log "all four registered gates ran; raw outputs recorded under $RUN_DIR"
release_claim
write_provenance
log "provenance: $PROVENANCE"
log "=== end (no results interpreted by this runner) ==="
cleanup_lock
exit 0
