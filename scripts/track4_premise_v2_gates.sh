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
# GATE INDEPENDENCE (the four gates are independent in the registration)
#   Section 7 registers E1-E4 as four separate acceptance gates.  No gate
#   consumes another gate's outputs: E1/E2 read the two pair manifests, E3 reads
#   the caption-QA release+key and the image directory, E4 reads the attacker
#   release+key.  Therefore a blocked or failed gate is RECORDED and the runner
#   moves on to the next gate; it never causes an independent gate to be
#   skipped.  Steps WITHIN one gate are still strictly ordered and a failed step
#   aborts only its own gate (E3's caption store must exist before E3's merge).
#   The run's exit code is 0 only when every gate the run ATTEMPTED completed;
#   otherwise 1, with per-gate status, blocked reason and failing step in the
#   provenance.  chain_status separates the two cases that exit 0 covers:
#   "complete" (all four attempted and ran) vs "selected_complete" (GATES_ONLY
#   narrowed the run; the gates it skipped are neither run nor judged here).
#   Infrastructure failures that make ALL GPU gates impossible (wrong host, no
#   jq/venv, GPU guard denial, claim write failure) still abort the whole run.
#
# WHAT THIS DOES NOT DO
#   * It does not interpret results.  It RUNS the registered commands and
#     RECORDS raw outputs, return codes, run dirs, node, git hash and UTC
#     times.  Pass/fail judgment against the section-7 criteria is NOT computed
#     here and no criterion is restated as a threshold check in this file.
#     A gate's "status" in this runner means "did the registered command run",
#     never "did the batch pass the gate".
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
#   * It never regenerates or mutates the dev batch.
#
# FAIL-CLOSED SEMANTICS
#   * Run-level preflight (CPU only, before any GPU claim) refuses on: wrong
#     host, missing jq/venv/guard script, a runner-owned output path that
#     already exists, or a second concurrent runner.
#   * Per-gate preflight (CPU only) checks THAT GATE's own inputs and blocks
#     only that gate.  A gate blocked on CPU never spends GPU time.
#   * GPU use is guarded exactly as scripts/launch_m7_seed2_eval.sh does:
#     m7_gpu_occupancy_guard.py -> write /dev/shm claim -> guard re-check with
#     --ignore-claim-run-id.  The claim is re-stamped with the live remote pid
#     after each launch and refreshed while waiting, so it holds past the
#     30-minute expiry.  The claim is taken once, held across all gates, and
#     released on every exit path.
#   * Every step's rc is checked.  A nonzero rc (or a timeout, or a remote pid
#     that dies without writing an rc) logs FAILED and aborts ITS OWN GATE.
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
#   * E3's merge/QA-build inputs (--release-manifest/--key-file) are not spelled
#     out in section 7.  The batch's attacker_release/attacker_key are packaged
#     for E4 and deliberately carry neither the question nor the answers, so
#     they cannot feed E3 — and widening them would leak exactly what attacker
#     packaging exists to withhold.  This runner therefore points E3 at the
#     derived caption-QA export produced by
#     scripts/build_track4_premise_v2_caption_qa_inputs.py from
#     manifest_causal_pairs.jsonl (a new artifact at a new path; the batch is
#     not mutated).  E3's preflight verifies that export's field contract.
#   * The runner's own provenance file is per-run (stamped).  A fixed path made
#     every rerun refuse at preflight once the first run had written it; the
#     path is a runner artifact, not a section-7 registered output.  E4's
#     registered output path reports/track4_premise_v2_attacker_gate_v1.json is
#     unchanged and is checked in E4's own preflight.
#
# USAGE (do not run in the foreground; long GPU work must be detached):
#   setsid nohup bash /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/\
# BlindGain/scripts/track4_premise_v2_gates.sh </dev/null >/dev/null 2>&1 & disown
#
#   GATES_ONLY="E3 E4" (or "E3,E4") restricts THIS run to the named gates, so a
#   run whose earlier gates already ran and were recorded in their own run dir
#   is not repeated on the GPU.  It changes no registered command and no pass
#   criterion; an unnamed gate is recorded not_selected, never "ok" and never
#   "blocked", and this run makes no claim about it.  Unknown names refuse.
#
# OUTPUTS
#   logs/track4_gates/<RUN>.log            runner log (+ per-step .log files)
#   experiments/runs/<RUN>/...             predictions/metrics per gate step
#   reports/track4_premise_v2_gates_run_provenance_<RUN>.json   provenance
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
# GATES_DATA_DIR override (2026-08-16, item 4): the branch-(c)+balance
# regeneration re-runs E1/E2 on data/track4_premise_v2_dev_v2 with this same
# instrument. Default is the registered v1 batch; behavior unchanged unless
# the env var is set. The derived tag keeps per-batch run ids and merge tags
# distinct so no v1 artifact can be overwritten.
DATA="${GATES_DATA_DIR:-data/track4_premise_v2_dev_v1}"
DATA_TAG="$(basename "$DATA")"
REGISTRATION=docs/registered_track4_premise_v2_design_v1.md

# E3 inputs: the derived caption-QA release+key (NOT the attacker files).
E3_RELEASE_MANIFEST="$DATA/caption_qa_inputs/manifest.jsonl"
E3_KEY_FILE="$DATA/caption_qa_inputs/key.jsonl"
# E4 inputs: the packaged attacker release+key, exactly as section 7 spells out.
E4_RELEASE_DIR="$DATA/attacker_release"
E4_KEY_FILE="$DATA/attacker_key.jsonl"
E4_REPORT=reports/track4_premise_v2_attacker_gate_v1.json

# Section 7 names no rescore/audit script and none exists on disk; leave empty.
RESCORE_SCRIPT=""

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN="track4_premise_v2_gates_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN}"
CAP_RUN_DIR="experiments/runs/track4_premise_v2_caption_store_${NODE}_${STAMP}"
LOG_DIR=logs/track4_gates
LOG="${LOG_DIR}/${RUN}.log"
STEPS_FILE="${RUN_DIR}/steps.jsonl"
PROVENANCE="reports/track4_premise_v2_gates_run_provenance_${RUN}.json"
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

GATES=(E1 E2 E3 E4)
declare -A GATE_STATUS=([E1]=pending [E2]=pending [E3]=pending [E4]=pending)
declare -A GATE_REASON=([E1]="" [E2]="" [E3]="" [E4]="")
declare -A GATE_FAILED_STEP=([E1]="" [E2]="" [E3]="" [E4]="")

# Optional per-run gate selection; empty means every registered gate (default).
# Parsed and applied further down, once log() exists.  See the USAGE header:
# this selects what THIS run attempts and never edits a command or a criterion.
GATES_ONLY="${GATES_ONLY:-}"

LAST_STEP_NAME=""
LAST_STEP_RC=""

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

gates_json() {
  jq -nc \
    --arg e1 "${GATE_STATUS[E1]}" --arg e1r "${GATE_REASON[E1]}" --arg e1s "${GATE_FAILED_STEP[E1]}" \
    --arg e2 "${GATE_STATUS[E2]}" --arg e2r "${GATE_REASON[E2]}" --arg e2s "${GATE_FAILED_STEP[E2]}" \
    --arg e3 "${GATE_STATUS[E3]}" --arg e3r "${GATE_REASON[E3]}" --arg e3s "${GATE_FAILED_STEP[E3]}" \
    --arg e4 "${GATE_STATUS[E4]}" --arg e4r "${GATE_REASON[E4]}" --arg e4s "${GATE_FAILED_STEP[E4]}" \
    'def g($s; $r; $f): {status:$s,
                         reason:(if $r == "" then null else $r end),
                         failed_step:(if $f == "" then null else $f end)};
     {E1: g($e1; $e1r; $e1s), E2: g($e2; $e2r; $e2s),
      E3: g($e3; $e3r; $e3s), E4: g($e4; $e4r; $e4s)}'
}

gates_with_status() {
  # gates_with_status <status> -> JSON array of gate names
  local want="$1" acc="" g
  for g in "${GATES[@]}"; do
    [[ "${GATE_STATUS[$g]}" == "$want" ]] && acc="${acc}${g}"$'\n'
  done
  printf '%s' "$acc" | jq -Rsc 'split("\n") | map(select(length > 0))'
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
    --arg e3_release "$E3_RELEASE_MANIFEST" \
    --arg e3_key "$E3_KEY_FILE" \
    --arg e4_release "$E4_RELEASE_DIR" \
    --arg e4_key "$E4_KEY_FILE" \
    --arg runner "scripts/track4_premise_v2_gates.sh" \
    --arg claim_path "$CLAIM_PATH" \
    --arg claim_run_id "$LABEL" \
    --arg log "$LOG" \
    --arg start_utc "$RUN_START_UTC" \
    --arg end_utc "$(utc)" \
    --arg status "$CHAIN_STATUS" \
    --arg failed_step "$CHAIN_FAILED_STEP" \
    --argjson gates "$(gates_json)" \
    --argjson gates_complete "$(gates_with_status ok)" \
    --argjson gates_failed "$(gates_with_status failed)" \
    --argjson gates_blocked "$(gates_with_status blocked)" \
    --argjson gates_not_attempted "$(gates_with_status not_attempted)" \
    --argjson gates_not_selected "$(gates_with_status not_selected)" \
    --arg gates_only "$GATES_ONLY" \
    --arg gates_selected "${GATES_SELECTED:-}" \
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
      gate_inputs: {
        e1_e2_manifests: ["\($data)/manifest_premise_probe.jsonl", "\($data)/manifest_causal_pairs.jsonl"],
        e3_release_manifest: $e3_release,
        e3_key_file: $e3_key,
        e3_image_dir: "\($data)/images",
        e4_release_dir: $e4_release,
        e4_key_file: $e4_key
      },
      run_dir: $run_dir,
      caption_store_run_dir: $caption_run_dir,
      caption_merge_run_dir: (if $merge_run_dir == "" then null else $merge_run_dir end),
      attacker_gate_run_dir: (if $attacker_run_dir == "" then null else $attacker_run_dir end),
      runner_log: $log,
      start_utc: $start_utc,
      end_utc: $end_utc,
      chain_status: $status,
      gates: $gates,
      gates_complete: $gates_complete,
      gates_failed: $gates_failed,
      gates_blocked: $gates_blocked,
      gates_not_attempted: $gates_not_attempted,
      gates_not_selected: $gates_not_selected,
      gate_selection: {
        gates_only: (if $gates_only == "" then null else $gates_only end),
        gates_attempted_this_run: ($gates_selected | split(" ") | map(select(length > 0))),
        note: "A not_selected gate was not run here and is not judged here. This run makes no claim about it; its status lives in whatever run did attempt it."
      },
      gate_independence: "E1-E4 are independent registered gates; a blocked or failed gate is recorded and never skips another gate. Steps inside one gate remain ordered and abort only that gate.",
      failed_step: (if $failed_step == "" then null else $failed_step end),
      steps: $steps,
      judgment: {
        computed_here: false,
        note: "Runner records raw outputs only. Section-7 pass criteria are not evaluated in this script and no result is interpreted here. A gate status of \"ok\" means the registered commands ran, not that the batch passed."
      },
      rescore_step: {
        named_by_registration: false,
        script: null,
        ran: false,
        note: "Section 7 refers to an unnamed rescore script for per-group q_real/q_blind and the measurement_state flip; no such script exists on disk. groups_v2.jsonl left untouched; judgment deferred."
      },
      resolutions: [
        "Gates E1-E4 run independently; a blocked/failed gate is recorded and the next gate is still attempted (section 7 registers four separate gates and no gate consumes another gate output).",
        "E2 output paths: sibling subdirectories under the same run dir (section 7 registers none; verbatim repetition would refuse to overwrite E1 outputs).",
        "E1/E2 executed with .venv/bin/python, PYTHONPATH=., TRANSFORMERS_OFFLINE=1, HF_HOME=artifacts/hf_home, CUDA_VISIBLE_DEVICES=2, dispatched to an29 (section 7 writes bare python and fixes no placement).",
        "E3 shards=1 and GPU_LIST=\"2\" so the caption store stays inside the one-GPU budget; MAX_NEW_TOKENS left at the launcher default 384.",
        "E3 merge/QA inputs resolved to the derived caption-QA export (scripts/build_track4_premise_v2_caption_qa_inputs.py over manifest_causal_pairs.jsonl); the attacker release/key carry neither question nor answers by design and are not widened.",
        "E4 node/gpu resolved to an29 2 per the one-GPU budget; E4 preflight checks only the fields src/fliptrack/artifact_attackers.py actually reads.",
        "Runner provenance path is per-run (stamped) so a rerun is not blocked by a previous runs provenance file; E4 registered output path is unchanged."
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

# --- gate bookkeeping -------------------------------------------------------
gate_block() {
  # gate_block <gate> <reason>   (CPU preflight refusal; no GPU spent)
  # A gate excluded from this run by GATES_ONLY keeps its not_selected status.
  # Its preflight still runs and is still recorded (the diagnostic is free and
  # worth having), but "this run did not attempt it" must never be overwritten
  # by "blocked" — that would be this run making a claim it did not test.
  [[ "${GATE_STATUS[$1]}" == "not_selected" ]] && return 0
  GATE_STATUS[$1]=blocked
  GATE_REASON[$1]="$2"
  log "BLOCKED [$1]: $2"
  log "gate $1 not attempted; independent gates still run"
}

gate_fail() {
  # gate_fail <gate> <step> <reason>
  GATE_STATUS[$1]=failed
  GATE_FAILED_STEP[$1]="$2"
  GATE_REASON[$1]="$3"
  [[ -n "$CHAIN_FAILED_STEP" ]] || CHAIN_FAILED_STEP="$2"
  log "FAILED [$1/$2]: $3"
  log "gate $1 aborted at $2; independent gates still run"
}

gate_ok() {
  GATE_STATUS[$1]=ok
  log "GATE $1 complete (commands ran and were recorded; not judged here)"
}

abort_run() {
  # abort_run <step-name> <message>   (infrastructure failure: no gate can run)
  CHAIN_STATUS=aborted
  CHAIN_FAILED_STEP="$1"
  log "ABORTED [$1]: $2"
  local g
  for g in "${GATES[@]}"; do
    if [[ "${GATE_STATUS[$g]}" == "pending" ]]; then
      GATE_STATUS[$g]=not_attempted
      GATE_REASON[$g]="run aborted at $1: $2"
    fi
  done
  log "run aborted before any gate could use the GPU"
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

# --- run-level preflight (CPU only, no GPU claimed yet) ----------------------
RUN_START_UTC="$(utc)"
log "=== track4 premise-v2 acceptance gates E1-E4 ==="
log "runner=scripts/track4_premise_v2_gates.sh run_id=$RUN"
log "registration=$REGISTRATION section 7 (I14); runs and records only, no interpretation"
log "gate independence: a blocked/failed gate never skips another gate"

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

for required in "$REGISTRATION" scripts/m7_gpu_occupancy_guard.py; do
  [[ -f "$required" ]] || { log "PREFLIGHT REFUSE: missing $required"; cleanup_lock; exit 2; }
done

for collision in "$RUN_DIR" "$CAP_RUN_DIR" "$PROVENANCE"; do
  [[ -e "$collision" ]] && { log "PREFLIGHT REFUSE: output path already exists: $collision"; cleanup_lock; exit 2; }
done

if [[ -n "$RESCORE_SCRIPT" && ! -f "$RESCORE_SCRIPT" ]]; then
  log "PREFLIGHT REFUSE: RESCORE_SCRIPT=$RESCORE_SCRIPT named but not on disk"
  cleanup_lock; exit 2
fi

mkdir -p "$RUN_DIR"/{cmds,rc,pids,preflight} || { log "PREFLIGHT REFUSE: cannot create $RUN_DIR"; cleanup_lock; exit 2; }
: > "$STEPS_FILE"

# --- gate selection for this run (default: every registered gate) ------------
# Fail-closed: an unrecognised name refuses the whole run rather than silently
# running a different set of gates than the operator asked for.
# BEGIN_GATE_SELECTION (executed verbatim by tests/test_track4_premise_v2_gates_independence.py)
if [[ -n "$GATES_ONLY" ]]; then
  declare -A GATE_WANTED=()
  # read -ra, not an unquoted expansion: the latter would glob-expand a value
  # like "*" against the repo root and silently select whatever it matched.
  IFS=' ' read -r -a GATES_ONLY_LIST <<< "${GATES_ONLY//,/ }"
  for want in ${GATES_ONLY_LIST[@]+"${GATES_ONLY_LIST[@]}"}; do
    [[ -n "$want" ]] || continue
    case " ${GATES[*]} " in
      *" $want "*) GATE_WANTED[$want]=1 ;;
      *) log "PREFLIGHT REFUSE: GATES_ONLY names unknown gate '$want' (registered gates: ${GATES[*]})"
         cleanup_lock; exit 2 ;;
    esac
  done
  if [[ ${#GATE_WANTED[@]} -eq 0 ]]; then
    log "PREFLIGHT REFUSE: GATES_ONLY='$GATES_ONLY' selects no registered gate"
    cleanup_lock; exit 2
  fi
  GATES_SELECTED=""
  for gate in "${GATES[@]}"; do
    if [[ -n "${GATE_WANTED[$gate]:-}" ]]; then
      GATES_SELECTED="${GATES_SELECTED}${GATES_SELECTED:+ }$gate"
    else
      GATE_STATUS[$gate]=not_selected
      GATE_REASON[$gate]="not selected for this run (GATES_ONLY='$GATES_ONLY'); this run neither ran nor judged it"
    fi
  done
  log "gate selection: GATES_ONLY='$GATES_ONLY' -> this run attempts [$GATES_SELECTED]; the others are recorded not_selected and are not claimed either way"
else
  GATES_SELECTED="${GATES[*]}"
  log "gate selection: none given; all ${#GATES[@]} registered gates attempted"
fi
# END_GATE_SELECTION

# =============================================================================
# PER-GATE PREFLIGHTS (CPU only; each blocks at most its own gate)
# =============================================================================
append_reason() {
  # append_reason <existing> <new>  -> prints the joined reason
  if [[ -z "$1" ]]; then printf '%s' "$2"; else printf '%s; %s' "$1" "$2"; fi
}

# --- E1/E2: the two pair manifests, the eval script, and the 3B model --------
E1_E2_MISSING=""
for required in scripts/eval_qwen_vl_fliptrack.py \
                "$DATA/manifest_premise_probe.jsonl" \
                "$DATA/manifest_causal_pairs.jsonl"; do
  [[ -f "$required" ]] || E1_E2_MISSING="$(append_reason "$E1_E2_MISSING" "missing file: $required")"
done
[[ -d "$BASE" ]] || E1_E2_MISSING="$(append_reason "$E1_E2_MISSING" "missing model dir: $BASE")"

for gate in E1 E2; do
  S=$(utc)
  record_step "preflight_${gate,,}_eval_inputs" "$gate" "$REGISTRATION#7-${gate}" \
    "existence check on scripts/eval_qwen_vl_fliptrack.py, $DATA/manifest_premise_probe.jsonl, $DATA/manifest_causal_pairs.jsonl, $BASE" \
    "$S" "$(utc)" "$([[ -z "$E1_E2_MISSING" ]] && echo 0 || echo 1)" \
    "$([[ -z "$E1_E2_MISSING" ]] && echo ok || echo blocked)" "$LOG" \
    "$(jq -nc --arg m "$E1_E2_MISSING" '{missing: (if $m == "" then null else $m end)}')"
  [[ -z "$E1_E2_MISSING" ]] || gate_block "$gate" "$E1_E2_MISSING"
done

# --- E3: the caption-QA release+key contract AND caption coverage ------------
# build_caption_qa_pairs.py -> src/captioning/qa_pairs.py::build_caption_qa_rows
# reads, per release row: pair_id, question, members[].member_id,
# members[].image_path, members[].image_sha256 (exactly two unique members); per
# key row: pair_id, source_pair_id, members[].member_id, members[].source_side
# (exactly {a,b}), members[].answer.  scripts/merge_caption_stores.py reads
# members[].image_sha256 off the same release manifest AND requires the caption
# store to cover the release hash set EXACTLY: src/captioning/store.py
# merge_caption_rows raises "caption hash coverage mismatch" when the store has
# any missing OR any extra hash, and there is no override flag.  The registered
# E3 command captions all of $DATA/images, so that image set must equal the
# release's image set or the merge dies after the GPU pass is already paid for.
E3_MISSING=""
E3_COVERAGE_JSON='null'
for required in "$E3_RELEASE_MANIFEST" "$E3_KEY_FILE" \
                scripts/eval_caption_qa_fliptrack.py \
                scripts/build_caption_qa_pairs.py \
                scripts/launch_caption_store_shards.sh \
                scripts/launch_caption_store_merge.sh; do
  [[ -f "$required" ]] || E3_MISSING="$(append_reason "$E3_MISSING" "missing file: $required")"
done
for required_dir in "$BASE" "$CAPTIONER" "$DATA/images"; do
  [[ -d "$required_dir" ]] || E3_MISSING="$(append_reason "$E3_MISSING" "missing dir: $required_dir")"
done

if [[ -z "$E3_MISSING" ]]; then
  if ! jq -s -e 'length > 0 and all(.[];
        has("pair_id") and has("question") and (.members | length) == 2
        and all(.members[]; has("member_id") and has("image_path") and has("image_sha256")))' \
      "$E3_RELEASE_MANIFEST" >/dev/null 2>&1; then
    E3_MISSING="$(append_reason "$E3_MISSING" "$E3_RELEASE_MANIFEST does not satisfy the build_caption_qa_pairs.py release contract (pair_id, question, two members with member_id/image_path/image_sha256)")"
  fi
  if ! jq -s -e 'length > 0 and all(.[];
        has("pair_id") and has("source_pair_id") and (.members | length) == 2
        and all(.members[]; has("member_id") and has("source_side") and has("answer"))
        and ([.members[].source_side] | sort) == ["a","b"])' \
      "$E3_KEY_FILE" >/dev/null 2>&1; then
    E3_MISSING="$(append_reason "$E3_MISSING" "$E3_KEY_FILE does not satisfy the build_caption_qa_pairs.py key contract (pair_id, source_pair_id, two members with member_id/source_side{a,b}/answer)")"
  fi
fi

if [[ -z "$E3_MISSING" ]]; then
  E3_IMG_HASHES="$RUN_DIR/preflight/e3_image_dir_hashes.txt"
  E3_REL_HASHES="$RUN_DIR/preflight/e3_release_hashes.txt"
  find "$DATA/images" -type f -print0 | sort -z | xargs -0 sha256sum 2>/dev/null \
    | awk '{print $1}' | sort -u > "$E3_IMG_HASHES"
  jq -r '.members[].image_sha256' "$E3_RELEASE_MANIFEST" | sort -u > "$E3_REL_HASHES"
  E3_N_IMG_FILES="$(find "$DATA/images" -type f | wc -l)"
  E3_N_IMG_HASHES="$(wc -l < "$E3_IMG_HASHES")"
  E3_N_REL_HASHES="$(wc -l < "$E3_REL_HASHES")"
  E3_N_MISSING="$(comm -23 "$E3_REL_HASHES" "$E3_IMG_HASHES" | wc -l)"
  E3_N_EXTRA="$(comm -13 "$E3_REL_HASHES" "$E3_IMG_HASHES" | wc -l)"
  E3_COVERAGE_JSON="$(jq -nc \
    --argjson files "$E3_N_IMG_FILES" --argjson image_hashes "$E3_N_IMG_HASHES" \
    --argjson release_hashes "$E3_N_REL_HASHES" \
    --argjson missing "$E3_N_MISSING" --argjson extra "$E3_N_EXTRA" \
    --arg imglist "$E3_IMG_HASHES" --arg rellist "$E3_REL_HASHES" \
    '{image_dir_files:$files, image_dir_distinct_sha256:$image_hashes,
      release_distinct_sha256:$release_hashes,
      release_hashes_without_image_file:$missing,
      image_hashes_outside_release:$extra,
      image_hash_list:$imglist, release_hash_list:$rellist}')"
  if [[ "$E3_N_MISSING" -ne 0 || "$E3_N_EXTRA" -ne 0 ]]; then
    E3_MISSING="$(append_reason "$E3_MISSING" "caption coverage mismatch: the registered E3 command captions $DATA/images ($E3_N_IMG_FILES files, $E3_N_IMG_HASHES distinct sha256) but $E3_RELEASE_MANIFEST covers $E3_N_REL_HASHES sha256 (missing=$E3_N_MISSING extra=$E3_N_EXTRA); src/captioning/store.py::merge_caption_rows raises on either and has no override flag, so the merge would fail after the whole GPU caption pass")"
  fi
fi

S=$(utc)
record_step "preflight_e3_qa_input_contract" "E3" "$REGISTRATION#7-E3" \
  "field-contract check on $E3_RELEASE_MANIFEST and $E3_KEY_FILE (build_caption_qa_pairs.py reader) plus caption-hash coverage of $DATA/images against the release" \
  "$S" "$(utc)" "$([[ -z "$E3_MISSING" ]] && echo 0 || echo 1)" \
  "$([[ -z "$E3_MISSING" ]] && echo ok || echo blocked)" "$LOG" \
  "$(jq -nc --arg m "$E3_MISSING" --argjson cov "$E3_COVERAGE_JSON" \
     '{missing: (if $m == "" then null else $m end), caption_coverage: $cov}')"
[[ -z "$E3_MISSING" ]] || gate_block E3 "$E3_MISSING"

# --- E4: the attacker release+key contract ----------------------------------
# E4's ONLY reader is src/fliptrack/artifact_attackers.py::
# build_packaged_member_table (lines 274-296), which consumes exactly:
#   release manifest.jsonl : row["pair_id"], row["members"][].["member_id"],
#                            row["members"][].["image_path"]   (joined as
#                            release_dir / image_path)
#   key file               : row["pair_id"], row["template_id"],
#                            key["members"][].["member_id"],
#                            key["members"][].["source_side"]
# verbatim:
#   pair_id = str(row["pair_id"]); key = keys[pair_id]
#   member_key = {str(member["member_id"]): member for member in key["members"]}
#   for member in row["members"]:
#       private = member_key[str(member["member_id"])]
#       paths.append(str(release_dir / str(member["image_path"])))
#       labels.append(0 if private["source_side"] == "a" else 1)
#       templates.append(str(key["template_id"]))
# It reads NO question, NO image_sha256, NO answer and NO source_pair_id.  Those
# belong to E3's caption-QA contract and must never be required of — or added
# to — the attacker-visible files: the question and the answers are exactly what
# attacker packaging withholds.
E4_MISSING=""
for required in scripts/launch_artifact_gate_v02.sh \
                "$E4_RELEASE_DIR/manifest.jsonl" "$E4_KEY_FILE"; do
  [[ -f "$required" ]] || E4_MISSING="$(append_reason "$E4_MISSING" "missing file: $required")"
done
if [[ -z "$E4_MISSING" ]]; then
  if ! jq -s -e 'length > 0 and all(.[];
        has("pair_id") and (.members | length) == 2
        and all(.members[]; has("member_id") and has("image_path")))' \
      "$E4_RELEASE_DIR/manifest.jsonl" >/dev/null 2>&1; then
    E4_MISSING="$(append_reason "$E4_MISSING" "$E4_RELEASE_DIR/manifest.jsonl does not satisfy the artifact_attackers.py release contract (pair_id, two members with member_id/image_path)")"
  fi
  if ! jq -s -e 'length > 0 and all(.[];
        has("pair_id") and has("template_id") and (.members | length) == 2
        and all(.members[]; has("member_id") and has("source_side")))' \
      "$E4_KEY_FILE" >/dev/null 2>&1; then
    E4_MISSING="$(append_reason "$E4_MISSING" "$E4_KEY_FILE does not satisfy the artifact_attackers.py key contract (pair_id, template_id, two members with member_id/source_side)")"
  fi
fi
[[ -e "$E4_REPORT" ]] && E4_MISSING="$(append_reason "$E4_MISSING" "registered output path already exists: $E4_REPORT")"

S=$(utc)
record_step "preflight_e4_attacker_input_contract" "E4" "$REGISTRATION#7-E4" \
  "field-contract check on $E4_RELEASE_DIR/manifest.jsonl and $E4_KEY_FILE against src/fliptrack/artifact_attackers.py::build_packaged_member_table, plus output-path collision check on $E4_REPORT" \
  "$S" "$(utc)" "$([[ -z "$E4_MISSING" ]] && echo 0 || echo 1)" \
  "$([[ -z "$E4_MISSING" ]] && echo ok || echo blocked)" "$LOG" \
  "$(jq -nc --arg m "$E4_MISSING" \
     '{missing: (if $m == "" then null else $m end),
       reader: "src/fliptrack/artifact_attackers.py::build_packaged_member_table",
       fields_checked: {release: ["pair_id","members[].member_id","members[].image_path"],
                        key: ["pair_id","template_id","members[].member_id","members[].source_side"]}}')"
[[ -z "$E4_MISSING" ]] || gate_block E4 "$E4_MISSING"

# --- do any gates remain? ----------------------------------------------------
GATES_RUNNABLE=0
for gate in "${GATES[@]}"; do
  [[ "${GATE_STATUS[$gate]}" == "pending" ]] && GATES_RUNNABLE=$((GATES_RUNNABLE + 1))
done
if [[ $GATES_RUNNABLE -eq 0 ]]; then
  CHAIN_STATUS=no_gate_runnable
  log "every gate is blocked by its own CPU preflight; no GPU claimed, nothing launched"
  write_provenance
  cleanup_lock
  log "provenance: $PROVENANCE"
  exit 1
fi
log "gates runnable after preflight: $GATES_RUNNABLE of ${#GATES[@]}"

# --- step 0: guard -> claim -> re-check (TOCTOU discipline) ------------------
S=$(utc)
"$PY" scripts/m7_gpu_occupancy_guard.py --node "$NODE" --gpus "$GPU" >> "$LOG" 2>&1
rc=$?
record_step "gpu_guard_precheck" "step0" "CLAUDE.md guarded free-GPU discipline" \
  "$PY scripts/m7_gpu_occupancy_guard.py --node $NODE --gpus $GPU" \
  "$S" "$(utc)" "$rc" "$([[ $rc -eq 0 ]] && echo ok || echo failed)" "$LOG" 'null'
[[ $rc -eq 0 ]] || abort_run "gpu_guard_precheck" "guard denied $NODE:$GPU (rc=$rc)"

S=$(utc)
write_claim null "$RUN_DIR"
rc=$?
record_step "gpu_claim_write" "step0" "scripts/launch_m7_seed2_eval.sh claim pattern" \
  "write $CLAIM_PATH on $NODE (run_id=$LABEL)" "$S" "$(utc)" "$rc" \
  "$([[ $rc -eq 0 ]] && echo ok || echo failed)" "$LOG" 'null'
[[ $rc -eq 0 ]] || abort_run "gpu_claim_write" "claim write failed (rc=$rc)"
CLAIM_HELD=1
log "claim written: $NODE:$CLAIM_PATH run_id=$LABEL"

S=$(utc)
"$PY" scripts/m7_gpu_occupancy_guard.py --node "$NODE" --gpus "$GPU" \
  --ignore-claim-run-id "$LABEL" >> "$LOG" 2>&1
rc=$?
record_step "gpu_guard_recheck" "step0" "CLAUDE.md guarded free-GPU discipline" \
  "$PY scripts/m7_gpu_occupancy_guard.py --node $NODE --gpus $GPU --ignore-claim-run-id $LABEL" \
  "$S" "$(utc)" "$rc" "$([[ $rc -eq 0 ]] && echo ok || echo failed)" "$LOG" 'null'
[[ $rc -eq 0 ]] || abort_run "gpu_guard_recheck" "post-claim re-check denied $NODE:$GPU (rc=$rc)"

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
  # Records the step and RETURNS its rc.  The caller (a gate function) decides
  # what a failure means for its own gate; no other gate is affected.
  local name="$1" gate="$2" ref="$3" timeout="$4" artifacts="$5" cmd="$6"
  local start end step_rc
  LAST_STEP_NAME="$name"
  start="$(utc)"
  log "[$gate/$name] START on $NODE gpu $GPU: $cmd"
  launch_remote_gpu_cmd "$name" "$cmd"
  if [[ $? -ne 0 || -z "$remote_pid" ]]; then
    record_step "$name" "$gate" "$ref" "$cmd" "$start" "$(utc)" 251 "launch_failed" \
      "${LOG_DIR}/${RUN}.${name}.log" "$artifacts"
    LAST_STEP_RC=251
    log "[$gate/$name] could not launch on $NODE (ssh rc or empty pid)"
    return 251
  fi
  log "[$gate/$name] launched pid=$remote_pid log=${LOG_DIR}/${RUN}.${name}.log"
  write_claim "$remote_pid" "$RUN_DIR"
  step_rc="$(wait_for_rc_file "$name" "$remote_pid" "$timeout")"
  end="$(utc)"
  record_step "$name" "$gate" "$ref" "$cmd" "$start" "$end" "${step_rc:-255}" \
    "$([[ "${step_rc:-255}" == "0" ]] && echo ok || echo failed)" \
    "${LOG_DIR}/${RUN}.${name}.log" "$artifacts"
  LAST_STEP_RC="${step_rc:-255}"
  if [[ "${step_rc:-255}" != "0" ]]; then
    return "${step_rc:-255}"
  fi
  log "[$gate/$name] DONE rc=0"
  return 0
}

run_login_step() {
  # run_login_step <step-name> <gate> <registered-ref> <artifacts-json> <command>
  # CPU-only step executed on this login node; stdout/stderr appended to a step log.
  # Records the step and RETURNS its rc (see run_gpu_step).
  local name="$1" gate="$2" ref="$3" artifacts="$4" cmd="$5"
  local start end step_rc steplog="${LOG_DIR}/${RUN}.${name}.log"
  LAST_STEP_NAME="$name"
  start="$(utc)"
  log "[$gate/$name] START (login $HOST): $cmd"
  ( cd "$ROOT" && eval "$cmd" ) >> "$steplog" 2>&1
  step_rc=$?
  end="$(utc)"
  record_step "$name" "$gate" "$ref" "$cmd" "$start" "$end" "$step_rc" \
    "$([[ $step_rc -eq 0 ]] && echo ok || echo failed)" "$steplog" "$artifacts"
  LAST_STEP_RC="$step_rc"
  [[ $step_rc -eq 0 ]] || { log "[$gate/$name] rc=$step_rc (see $steplog)"; return "$step_rc"; }
  log "[$gate/$name] DONE rc=0"
  return 0
}

# =============================================================================
# E1 — difficulty band (section 7, two registered commands, --image-mode real)
# =============================================================================
gate_e1() {
  run_gpu_step "e1_premise_probe_real" "E1" "$REGISTRATION#7-E1-cmd1" \
    "$EVAL_TIMEOUT_SECONDS" \
    "$(jq -nc --arg p "$RUN_DIR/premise_probe/predictions.jsonl" --arg m "$RUN_DIR/premise_probe/metrics.json" '{predictions:$p, metrics:$m}')" \
    "$PY scripts/eval_qwen_vl_fliptrack.py --model-path $BASE \
  --manifest $DATA/manifest_premise_probe.jsonl \
  --output $RUN_DIR/premise_probe/predictions.jsonl \
  --metrics-output $RUN_DIR/premise_probe/metrics.json \
  --image-mode real --seed 0 --noise-seed 0 --max-new-tokens 32" \
    || { gate_fail E1 "$LAST_STEP_NAME" "rc=$LAST_STEP_RC"; return 1; }

  run_gpu_step "e1_final_real" "E1" "$REGISTRATION#7-E1-cmd2" \
    "$EVAL_TIMEOUT_SECONDS" \
    "$(jq -nc --arg p "$RUN_DIR/final/predictions.jsonl" --arg m "$RUN_DIR/final/metrics.json" '{predictions:$p, metrics:$m}')" \
    "$PY scripts/eval_qwen_vl_fliptrack.py --model-path $BASE \
  --manifest $DATA/manifest_causal_pairs.jsonl \
  --output $RUN_DIR/final/predictions.jsonl \
  --metrics-output $RUN_DIR/final/metrics.json \
  --image-mode real --seed 0 --noise-seed 0 --max-new-tokens 32" \
    || { gate_fail E1 "$LAST_STEP_NAME" "rc=$LAST_STEP_RC"; return 1; }

  gate_ok E1
  return 0
}

# =============================================================================
# E2 — blind floor (both E1 commands x {no_image, gray}; output subdirs resolved)
# =============================================================================
gate_e2() {
  local mode
  for mode in no_image gray; do
    run_gpu_step "e2_premise_probe_${mode}" "E2" "$REGISTRATION#7-E2" \
      "$EVAL_TIMEOUT_SECONDS" \
      "$(jq -nc --arg p "$RUN_DIR/premise_probe_${mode}/predictions.jsonl" --arg m "$RUN_DIR/premise_probe_${mode}/metrics.json" '{predictions:$p, metrics:$m}')" \
      "$PY scripts/eval_qwen_vl_fliptrack.py --model-path $BASE \
  --manifest $DATA/manifest_premise_probe.jsonl \
  --output $RUN_DIR/premise_probe_${mode}/predictions.jsonl \
  --metrics-output $RUN_DIR/premise_probe_${mode}/metrics.json \
  --image-mode ${mode} --seed 0 --noise-seed 0 --max-new-tokens 32" \
      || { gate_fail E2 "$LAST_STEP_NAME" "rc=$LAST_STEP_RC"; return 1; }

    run_gpu_step "e2_final_${mode}" "E2" "$REGISTRATION#7-E2" \
      "$EVAL_TIMEOUT_SECONDS" \
      "$(jq -nc --arg p "$RUN_DIR/final_${mode}/predictions.jsonl" --arg m "$RUN_DIR/final_${mode}/metrics.json" '{predictions:$p, metrics:$m}')" \
      "$PY scripts/eval_qwen_vl_fliptrack.py --model-path $BASE \
  --manifest $DATA/manifest_causal_pairs.jsonl \
  --output $RUN_DIR/final_${mode}/predictions.jsonl \
  --metrics-output $RUN_DIR/final_${mode}/metrics.json \
  --image-mode ${mode} --seed 0 --noise-seed 0 --max-new-tokens 32" \
      || { gate_fail E2 "$LAST_STEP_NAME" "rc=$LAST_STEP_RC"; return 1; }
  done
  gate_ok E2
  return 0
}

# =============================================================================
# E3 — caption stress
# =============================================================================
gate_e3() {
  local rc cap_manifest cap_pid S

  run_login_step "e3_caption_store_launch" "E3" "$REGISTRATION#7-E3" \
    "$(jq -nc --arg d "$CAP_RUN_DIR" '{caption_run_dir:$d}')" \
    "bash scripts/launch_caption_store_shards.sh $NODE 0 1 $CAPTIONER $DATA/images $CAP_RUN_DIR \"$GPU\"" \
    || { gate_fail E3 "$LAST_STEP_NAME" "rc=$LAST_STEP_RC"; return 1; }

  S=$(utc)
  cap_manifest="$CAP_RUN_DIR/run_manifest.json"
  cap_pid="$(cat "$CAP_RUN_DIR"/pids/*.pid 2>/dev/null | head -1 || true)"
  write_claim "${cap_pid:-null}" "$RUN_DIR"
  log "[E3/e3_caption_store_wait] waiting on $cap_manifest (pid=${cap_pid:-unknown})"
  rc="$(wait_for_manifest_status "e3_caption_store_wait" "$cap_manifest" "$CAP_RUN_DIR/pids" "$CAPTION_TIMEOUT_SECONDS")"
  record_step "e3_caption_store_wait" "E3" "$REGISTRATION#7-E3" \
    "poll $cap_manifest until status != running" "$S" "$(utc)" "${rc:-255}" \
    "$([[ "${rc:-255}" == "0" ]] && echo ok || echo failed)" "$LOG" \
    "$(jq -nc --arg s "$CAP_RUN_DIR/shards/store_shard_0.jsonl" '{shard:$s}')"
  if [[ "${rc:-255}" != "0" ]]; then
    gate_fail E3 "e3_caption_store_wait" "caption store did not complete (rc=${rc:-255})"
    return 1
  fi

  run_login_step "e3_caption_merge" "E3" "$REGISTRATION#7-E3" \
    "$(jq -nc --arg s "$CAP_RUN_DIR/shards/store_shard_0.jsonl" --arg r "$E3_RELEASE_MANIFEST" '{input_shard:$s, release_manifest:$r}')" \
    "bash scripts/launch_caption_store_merge.sh $DATA_TAG $E3_RELEASE_MANIFEST $CAP_RUN_DIR/shards/store_shard_0.jsonl" \
    || { gate_fail E3 "$LAST_STEP_NAME" "rc=$LAST_STEP_RC"; return 1; }

  # launch_caption_store_merge.sh prints its RUN_DIR as the last stdout line;
  # match the run-id prefix instead of trusting line position (ssh/profile
  # chatter on stdout would poison a positional read).
  MERGE_RUN_DIR="$(grep -E '^experiments/runs/caption_store_merge_[A-Za-z0-9_.-]+$' \
    "${LOG_DIR}/${RUN}.e3_caption_merge.log" 2>/dev/null | tail -1 || true)"
  if [[ -z "$MERGE_RUN_DIR" || ! -s "$MERGE_RUN_DIR/captions.jsonl" ]]; then
    record_step "e3_caption_merge_resolve" "E3" "$REGISTRATION#7-E3" \
      "resolve merged caption store from launch_caption_store_merge.sh stdout" \
      "$(utc)" "$(utc)" 249 "failed" "${LOG_DIR}/${RUN}.e3_caption_merge.log" \
      "$(jq -nc --arg d "${MERGE_RUN_DIR:-}" '{merge_run_dir:$d}')"
    gate_fail E3 "e3_caption_merge_resolve" "merged caption store not found (merge_run_dir='${MERGE_RUN_DIR:-}')"
    return 1
  fi
  log "[E3] merged caption store: $MERGE_RUN_DIR/captions.jsonl"

  run_login_step "e3_build_caption_qa" "E3" "$REGISTRATION#7-E3" \
    "$(jq -nc --arg q "$RUN_DIR/caption_qa/qa.jsonl" --arg s "$RUN_DIR/caption_qa/qa_input_summary.json" '{qa:$q, summary:$s}')" \
    "$PY scripts/build_caption_qa_pairs.py --release-manifest $E3_RELEASE_MANIFEST --key-file $E3_KEY_FILE --caption-store $MERGE_RUN_DIR/captions.jsonl --output $RUN_DIR/caption_qa/qa.jsonl --summary $RUN_DIR/caption_qa/qa_input_summary.json" \
    || { gate_fail E3 "$LAST_STEP_NAME" "rc=$LAST_STEP_RC"; return 1; }

  run_gpu_step "e3_caption_qa_eval" "E3" "$REGISTRATION#7-E3" \
    "$EVAL_TIMEOUT_SECONDS" \
    "$(jq -nc --arg p "$RUN_DIR/caption_qa/predictions.jsonl" --arg m "$RUN_DIR/caption_qa/metrics.json" '{predictions:$p, metrics:$m}')" \
    "$PY scripts/eval_caption_qa_fliptrack.py --model-path $BASE \
  --input $RUN_DIR/caption_qa/qa.jsonl \
  --output $RUN_DIR/caption_qa/predictions.jsonl \
  --metrics-output $RUN_DIR/caption_qa/metrics.json \
  --max-new-tokens 32" \
    || { gate_fail E3 "$LAST_STEP_NAME" "rc=$LAST_STEP_RC"; return 1; }

  gate_ok E3
  return 0
}

# =============================================================================
# E4 — attacker check
# =============================================================================
gate_e4() {
  local rc att_pid S

  run_login_step "e4_attacker_gate_launch" "E4" "$REGISTRATION#7-E4" \
    "$(jq -nc --arg o "$E4_REPORT" '{report:$o}')" \
    "bash scripts/launch_artifact_gate_v02.sh $NODE $GPU $E4_RELEASE_DIR $E4_KEY_FILE $E4_REPORT" \
    || { gate_fail E4 "$LAST_STEP_NAME" "rc=$LAST_STEP_RC"; return 1; }

  # launch_artifact_gate_v02.sh prints its RUN_DIR first, then pid_file=/log=;
  # match the run-id prefix rather than the line position.
  ATTACKER_RUN_DIR="$(grep -E '^experiments/runs/artifact_gate_v02_[A-Za-z0-9_.-]+$' \
    "${LOG_DIR}/${RUN}.e4_attacker_gate_launch.log" 2>/dev/null | head -1 || true)"
  if [[ -z "$ATTACKER_RUN_DIR" || ! -s "$ATTACKER_RUN_DIR/run_manifest.json" ]]; then
    record_step "e4_attacker_gate_resolve" "E4" "$REGISTRATION#7-E4" \
      "resolve attacker-gate run dir from launch_artifact_gate_v02.sh stdout" \
      "$(utc)" "$(utc)" 249 "failed" "${LOG_DIR}/${RUN}.e4_attacker_gate_launch.log" \
      "$(jq -nc --arg d "${ATTACKER_RUN_DIR:-}" '{attacker_run_dir:$d}')"
    gate_fail E4 "e4_attacker_gate_resolve" "attacker-gate run dir not found (got '${ATTACKER_RUN_DIR:-}')"
    return 1
  fi
  log "[E4] attacker gate run dir: $ATTACKER_RUN_DIR"

  S=$(utc)
  att_pid="$(cat "$ATTACKER_RUN_DIR"/pids/*.pid 2>/dev/null | head -1 || true)"
  write_claim "${att_pid:-null}" "$RUN_DIR"
  rc="$(wait_for_manifest_status "e4_attacker_gate_wait" "$ATTACKER_RUN_DIR/run_manifest.json" "$ATTACKER_RUN_DIR/pids" "$ATTACKER_TIMEOUT_SECONDS")"
  record_step "e4_attacker_gate_wait" "E4" "$REGISTRATION#7-E4" \
    "poll $ATTACKER_RUN_DIR/run_manifest.json until status != running" "$S" "$(utc)" "${rc:-255}" \
    "$([[ "${rc:-255}" == "0" ]] && echo ok || echo failed)" "$LOG" \
    "$(jq -nc --arg o "$E4_REPORT" '{report:$o}')"
  if [[ "${rc:-255}" != "0" ]]; then
    gate_fail E4 "e4_attacker_gate_wait" "attacker gate did not complete (rc=${rc:-255})"
    return 1
  fi

  gate_ok E4
  return 0
}

# =============================================================================
# Gate sequence — independent gates, strictly one after another on the one GPU
# =============================================================================
for gate in "${GATES[@]}"; do
  if [[ "${GATE_STATUS[$gate]}" != "pending" ]]; then
    log "skipping $gate (status=${GATE_STATUS[$gate]}): ${GATE_REASON[$gate]}"
    continue
  fi
  log "--- gate $gate START ---"
  case "$gate" in
    E1) gate_e1 ;;
    E2) gate_e2 ;;
    E3) gate_e3 ;;
    E4) gate_e4 ;;
  esac
  log "--- gate $gate END status=${GATE_STATUS[$gate]} ---"
done

log "E1+E2 predictions and metrics recorded under $RUN_DIR (raw; no rescore, no measurement_state flip)"

# =============================================================================
# Registered rescore/audit step (only if the registration names one on disk)
# =============================================================================
if [[ -n "$RESCORE_SCRIPT" ]]; then
  run_login_step "registered_rescore" "post" "$REGISTRATION#7-E2-rescore" \
    "$(jq -nc --arg s "$RESCORE_SCRIPT" '{script:$s}')" \
    "$PY $RESCORE_SCRIPT" \
    || log "[post/registered_rescore] rc=$LAST_STEP_RC"
else
  record_step "registered_rescore" "post" "$REGISTRATION#7-E2-rescore" \
    "none — section 7 names no rescore script and none exists on disk" \
    "$(utc)" "$(utc)" 'null' "not_run_registration_defers" "$LOG" \
    "$(jq -nc --arg g "$DATA/groups_v2.jsonl" '{groups_file:$g, modified:false}')"
  log "no registered rescore script on disk; q_real/q_blind and measurement_state left untouched"
fi

# =============================================================================
# Terminal status — reflects whether EVERY gate this run ATTEMPTED completed,
# and separately whether that attempt covered the whole registered chain.
#
# Three terminal statuses, because two different questions are being answered
# and collapsing them would make the runner lie in one direction or the other:
#   complete           every registered gate was attempted here and ran.
#   selected_complete  every gate SELECTED here ran, but GATES_ONLY excluded
#                      others; this run makes no claim about those.
#   incomplete         some gate this run attempted is blocked or failed.
# A not_selected gate is excluded from the denominator: it was never attempted
# here, so counting it as a shortfall would report a failure this run did not
# observe.  It is equally never folded into "complete" — only a run that
# attempted all ${#GATES[@]} gates may use that word.
# =============================================================================
N_OK=0
N_SELECTED=0
for gate in "${GATES[@]}"; do
  log "gate $gate: status=${GATE_STATUS[$gate]}${GATE_REASON[$gate]:+ reason=${GATE_REASON[$gate]}}"
  [[ "${GATE_STATUS[$gate]}" == "not_selected" ]] || N_SELECTED=$((N_SELECTED + 1))
  [[ "${GATE_STATUS[$gate]}" == "ok" ]] && N_OK=$((N_OK + 1))
done

if [[ $N_OK -ne $N_SELECTED ]]; then
  CHAIN_STATUS=incomplete
  EXIT_CODE=1
  log "$N_OK of the $N_SELECTED gates this run attempted ran; the rest are blocked or failed (see gates in provenance)"
elif [[ $N_SELECTED -eq ${#GATES[@]} ]]; then
  CHAIN_STATUS=complete
  EXIT_CODE=0
  log "all ${#GATES[@]} registered gates ran; raw outputs recorded under $RUN_DIR"
else
  CHAIN_STATUS=selected_complete
  EXIT_CODE=0
  log "all $N_SELECTED gates selected for this run [$GATES_SELECTED] ran; raw outputs recorded under $RUN_DIR"
  log "this run did not attempt $(( ${#GATES[@]} - N_SELECTED )) other registered gate(s) and makes no claim about them; the registered chain is NOT complete on the strength of this run alone"
fi

release_claim
write_provenance
log "provenance: $PROVENANCE"
log "=== end (no results interpreted by this runner) ==="
cleanup_lock
exit "$EXIT_CODE"
