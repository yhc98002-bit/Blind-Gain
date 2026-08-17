#!/usr/bin/env bash
# ST3-7B arm launcher. Fails closed on every registered precondition before a
# single optimizer step: registration at HEAD, config/corpus/reward clean vs
# HEAD, corpus hash matches its build report, GPU occupancy guard + TOCTOU
# reservation claims, host-RAM headroom (the 2026-08-03 cascade that killed a
# 7B arm), storage floor sized for resumable 7B checkpoints.
#
# Usage: launch_st3_7b_arm.sh {std|igpo} NODE GPU_LIST
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
PY="$ROOT/.venv/bin/python"

[[ $# -eq 3 ]] || { echo "usage: $0 {std|igpo} <an12|an29> <gpu csv>" >&2; exit 2; }
ARM="$1"; NODE="$2"; GPU_LIST="$3"
[[ "$ARM" =~ ^(std|igpo)$ ]] || { echo "arm must be std or igpo" >&2; exit 2; }
[[ "$NODE" =~ ^(an12|an29)$ ]] || { echo "node must be an12 or an29" >&2; exit 2; }
IFS=',' read -r -a GPU_IDS <<< "$GPU_LIST"
GPU_COUNT=${#GPU_IDS[@]}

LABEL="st3_${ARM}_seed1_7b"
CONFIG="configs/train/${LABEL}.yaml"
CORPUS_REPORT="reports/st3_train_corpus_v1.json"
REGISTRATION="docs/registered_stage3_7b_v1.md"
[[ -f "$CONFIG" ]] || { echo "missing config $CONFIG" >&2; exit 2; }

# --- registered preconditions -------------------------------------------------
grep -q "RATIFIED\|Launch amendment 1" "$REGISTRATION" || {
  echo "registration is not ratified / carries no launch amendment" >&2; exit 3; }
CRITICAL=("$REGISTRATION" "$CONFIG" "$CORPUS_REPORT" "scripts/launch_st3_7b_arm.sh"
          "scripts/build_st3_train_corpus.py" "src/rewards/pilot_reward.py"
          "scripts/m7_gpu_occupancy_guard.py" "scripts/run_manifest_job.py")
for path in "${CRITICAL[@]}"; do
  git ls-files --error-unmatch "$path" >/dev/null 2>&1 || {
    echo "not git-tracked: $path" >&2; exit 3; }
  git diff --quiet HEAD -- "$path" || {
    echo "uncommitted drift vs HEAD: $path" >&2; exit 3; }
done

# corpus identity: the trainer must read exactly the corpus the report declares
CFG_TRAIN=$(grep -E "^  train_files:" "$CONFIG" | awk '{print $2}')
REPORT_DIR=$(jq -r '.out_dir' "$CORPUS_REPORT")
JSONL_SHA=$(jq -r '.train_jsonl_sha256' "$CORPUS_REPORT")
ACTUAL_SHA=$(sha256sum "${REPORT_DIR}/train.jsonl" | awk '{print $1}')
[[ "$JSONL_SHA" == "$ACTUAL_SHA" ]] || {
  echo "corpus sha mismatch: report $JSONL_SHA vs disk $ACTUAL_SHA" >&2; exit 3; }
[[ -f "$CFG_TRAIN" ]] || { echo "config train_files missing on disk: $CFG_TRAIN" >&2; exit 3; }

CFG_GPUS=$(grep -E "^  n_gpus_per_node:" "$CONFIG" | awk '{print $2}')
[[ "$GPU_COUNT" == "$CFG_GPUS" ]] || {
  echo "gpu count $GPU_COUNT != config n_gpus_per_node $CFG_GPUS" >&2; exit 2; }
CKPT=$(grep -E "^  save_checkpoint_path:" "$CONFIG" | awk '{print $2}')
[[ ! -e "$CKPT" ]] || { echo "refusing to overwrite checkpoints: $CKPT" >&2; exit 73; }

# --- placement safety ---------------------------------------------------------
# One ramping trainer per node: a 7B host-offload arm colocated with another
# trainer took down both on 2026-08-03 (registered_c5_7b_access_pair_v1.md).
# The pattern is assembled remotely with printf so that neither this script's
# ssh command line nor the remote shell's own command line contains the literal
# string — pgrep -f matches full command lines and would otherwise count itself
# (it did, on the first launch attempt).
LIVE=$(ssh -o BatchMode=yes -o ConnectTimeout=25 "$NODE" \
        'p=$(printf "%s.%s" verl.trainer mai)n; pgrep -fc "$p" || true' \
        2>/dev/null | tr -d '[:space:]')
[[ "${LIVE:-0}" == "0" ]] || {
  echo "another trainer is live on $NODE (count=$LIVE); 7B arms run alone" >&2; exit 73; }
AVAIL=$(ssh -o BatchMode=yes -o ConnectTimeout=25 "$NODE" \
        "free -g | awk '/^Mem:/{print \$7}'" 2>/dev/null | tr -d '[:space:]')
[[ "${AVAIL:-0}" -ge 600 ]] || {
  echo "host RAM available ${AVAIL}GiB < 600GiB floor on $NODE" >&2; exit 76; }
FREE_BYTES=$(df -B1 --output=avail "$ROOT" | tail -1 | tr -d '[:space:]')
[[ "$FREE_BYTES" -ge 400000000000 ]] || {
  echo "storage floor: ${FREE_BYTES}B < 400GB (resumable 7B checkpoints)" >&2; exit 76; }

"$PY" scripts/m7_gpu_occupancy_guard.py --node "$NODE" --gpus "$GPU_LIST" || exit 75

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="${LABEL}_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
mkdir -p "$RUN_DIR/logs" "$RUN_DIR/pids"
EFFECTIVE="$RUN_DIR/effective_config.yaml"
install -m 0444 "$CONFIG" "$EFFECTIVE"

CLAIMS=/dev/shm/blind-gains/gpu_claims
for gpu in "${GPU_IDS[@]}"; do
  jq -nc --argjson gpu "$gpu" --arg run_id "$RUN_ID" --argjson pid null \
    --arg dir "$RUN_DIR" --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '{gpu:$gpu, run_id:$run_id, pid:$pid, eval_run_dir:$dir, written_utc:$ts,
      written_by:"scripts/launch_st3_7b_arm.sh"}' | \
    ssh -o BatchMode=yes -o ConnectTimeout=25 "$NODE" \
      "mkdir -p '$CLAIMS' && cat > '$CLAIMS/${NODE}_gpu${gpu}.claim'" || exit 3
done
"$PY" scripts/m7_gpu_occupancy_guard.py --node "$NODE" --gpus "$GPU_LIST" \
  --ignore-claim-run-id "$RUN_ID" || exit 75

RAY_TMP="/dev/shm/bg-ray-$(printf '%s' "$RUN_ID" | sha256sum | cut -c1-12)"
COMMAND="env CUDA_VISIBLE_DEVICES='${GPU_LIST}' EASYR1_ATTN_IMPLEMENTATION=sdpa \
BLIND_GAINS_STORAGE_GUARD_ENABLED=1 BLIND_GAINS_CHECKPOINT_TIER=S \
BLIND_GAINS_CHECKPOINT_REQUIRED_BYTES=330000000000 \
PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True' \
RAY_TMPDIR='${RAY_TMP}' TMPDIR='${RAY_TMP}' \
TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 \
PYTHONPATH='${ROOT}/artifacts/repos/EasyR1:${ROOT}' \
${PY} -u -m verl.trainer.main config=${ROOT}/${EFFECTIVE}"

jq -n --arg run_id "$RUN_ID" --arg node "$NODE" --arg arm "$ARM" \
  --argjson gpu_ids "$(printf '%s\n' "${GPU_IDS[@]}" | jq -sc 'map(tonumber)')" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_sha "$(sha256sum "$CONFIG" | awk '{print $1}')" \
  --arg corpus_sha "$JSONL_SHA" --arg corpus "$CFG_TRAIN" \
  --arg command "$COMMAND" --arg ckpt "$CKPT" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{schema_version:"blind-gains.run-manifest.v1", run_id:$run_id,
    job_type:"st3_7b_training", status:"running", node:$node, arm:$arm,
    gpu_ids:$gpu_ids, replica_count:($gpu_ids|length), tensor_parallel_width:1,
    model_key:"Qwen2.5-VL-7B-Instruct", git_hash:$git_hash,
    config_sha256:$config_sha, train_corpus:$corpus,
    train_corpus_sha256:$corpus_sha, checkpoint_path:$ckpt, command:$command,
    placement_justification:"one ramping trainer per node; an12 runs LH2, so ST3 arms are sequential on an29 at 8 GPUs",
    registration:"docs/registered_stage3_7b_v1.md §2 + Launch amendment 1",
    start_time_utc:$started, end_time_utc:null, exit_code:null, deviations:[]}' \
  > "$RUN_DIR/run_manifest.json"

ssh -o BatchMode=yes -o ConnectTimeout=25 "$NODE" \
  "cd '$ROOT' && mkdir -p '${RAY_TMP}' && (nohup setsid ${PY} scripts/run_manifest_job.py '${ROOT}/${RUN_DIR}/run_manifest.json' '${ROOT}/${RUN_DIR}/logs/${NODE}.log' > /dev/null 2>&1 < /dev/null & echo \$! > '${ROOT}/${RUN_DIR}/pids/${NODE}.pid')" \
  || { echo "dispatch failed" >&2; exit 1; }
sleep 25
PID=$(cat "$RUN_DIR/pids/${NODE}.pid" 2>/dev/null)
ssh -o BatchMode=yes -o ConnectTimeout=25 "$NODE" "kill -0 ${PID}" 2>/dev/null \
  || { echo "trainer died within 25s; see $RUN_DIR/logs/${NODE}.log" >&2; exit 1; }
echo "$RUN_DIR"
