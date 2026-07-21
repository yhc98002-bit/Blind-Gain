#!/usr/bin/env bash
# shellcheck disable=SC2029
set -euo pipefail

if [[ $# -lt 7 || $# -gt 9 ]]; then
  echo "usage: $0 ARM NODE GPU TRAINING_RUN MARKER CHECKPOINT CAPTION_RUN|- [RESUME_FROM|-] [BATCH_SIZE]" >&2
  exit 2
fi

ARM="$1"
NODE="$2"
GPU="$3"
TRAINING_RUN="$4"
MARKER="$5"
CHECKPOINT="$6"
CAPTION_RUN="$7"
RESUME_FROM="${8:--}"
BATCH_SIZE="${9:-4}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_MANIFEST="data/geometry3k_caption_images_manifest.jsonl"
FORMAT_PROMPT="artifacts/repos/EasyR1/examples/format_prompt/r1v.jinja"
MAX_TOKENS=2048
SEED=20260710
GLOBAL_STEP="${BLIND_GAINS_PILOT_GLOBAL_STEP:-100}"
FOLLOWUP_SEED="${BLIND_GAINS_PILOT_FOLLOWUP_SEED:-}"
FOLLOWUP_ROW_SCHEMA_VERSION="blind-gains.pilot-followup-geo3k-checkpoint-eval.v1"

if [[ ! "${GLOBAL_STEP}" =~ ^(60|100)$ ]]; then
  echo "pilot Geometry3K global step must be 60 or 100" >&2
  exit 2
fi
if [[ -n "${FOLLOWUP_SEED}" ]]; then
  [[ "${FOLLOWUP_SEED}" =~ ^(2|3)$ ]] || { echo "follow-up pilot seed must be 2 or 3" >&2; exit 2; }
  TRAINING_JOB_TYPE="m3_mechanical_pilot_arm"
  EVALUATION_JOB_TYPE="m3_pilot_geo3k_checkpoint_eval"
  RUN_SCOPE="m3"
  ROW_SCHEMA_ARGS="--row-schema-version ${FOLLOWUP_ROW_SCHEMA_VERSION}"
else
  [[ "${GLOBAL_STEP}" == "100" ]] || { echo "seed-1 Geometry3K endpoint is pinned to step 100" >&2; exit 2; }
  TRAINING_JOB_TYPE="l13_mechanical_pilot_arm"
  EVALUATION_JOB_TYPE="m2_pilot_geo3k_step100_eval"
  RUN_SCOPE="m2"
  ROW_SCHEMA_ARGS=""
fi

case "${ARM}" in
  a1_real) CONDITION="real" ;;
  a2_gray) CONDITION="gray" ;;
  a2b_noimage) CONDITION="none" ;;
  a3_caption) CONDITION="caption" ;;
  *) echo "unsupported pilot arm: ${ARM}" >&2; exit 2 ;;
esac
if [[ ! "${NODE}" =~ ^(an12|an29)$ || ! "${GPU}" =~ ^[0-7]$ ]]; then
  echo "invalid node or GPU" >&2
  exit 2
fi
if [[ ! "${BATCH_SIZE}" =~ ^[1-9][0-9]*$ ]]; then
  echo "batch size must be positive" >&2
  exit 2
fi

cd "${ROOT}"
for path in "${TRAINING_RUN}/run_manifest.json" "${MARKER}" "${CHECKPOINT}/model.safetensors.index.json" "${SOURCE_MANIFEST}" "${FORMAT_PROMPT}"; do
  if [[ ! -s "${path}" ]]; then
    echo "required input is absent or empty: ${path}" >&2
    exit 2
  fi
done
if ! rg -q '^M0 \| pass \|' reports/main_progress.md; then
  echo "M2 evaluation is blocked until M0 is recorded pass" >&2
  exit 3
fi
if ! git ls-files --error-unmatch reports/preregistration_pilot_v1.md >/dev/null 2>&1 || \
   ! git diff --quiet HEAD -- reports/preregistration_pilot_v1.md; then
  echo "registered preregistration must be tracked and byte-clean at HEAD" >&2
  exit 3
fi

TRAINING_MANIFEST="${TRAINING_RUN}/run_manifest.json"
if ! jq -e \
  --arg arm "${ARM}" \
  --arg condition "${CONDITION}" \
  --arg job_type "${TRAINING_JOB_TYPE}" \
  --argjson followup_seed "${FOLLOWUP_SEED:-null}" \
  '(.job_type == $job_type) and
   (.arm == $arm) and (.image_condition == $condition) and
   ($followup_seed == null or .seed == $followup_seed) and
   (.status == "complete") and (.exit_code == 0) and (.artifacts_exist == true)' \
  "${TRAINING_MANIFEST}" >/dev/null; then
  echo "training run is not a complete matching pilot arm" >&2
  exit 3
fi
EXPECTED_CHECKPOINT="$(jq -r '.checkpoint_path' "${TRAINING_MANIFEST}")/global_step_${GLOBAL_STEP}/actor/huggingface"
if [[ "$(realpath "${CHECKPOINT}")" != "$(realpath "${EXPECTED_CHECKPOINT}")" ]]; then
  echo "checkpoint is not the exact completed arm step-100 merge" >&2
  exit 3
fi
CHECKPOINT_REAL="$(realpath "${CHECKPOINT}")"
if ! jq -e \
  --arg checkpoint "${CHECKPOINT_REAL}" \
  --argjson global_step "${GLOBAL_STEP}" \
  '(.schema_version == "blind-gains.pilot-step-eval-marker.v1") and
   (.status == "complete") and (.global_step == $global_step) and
   (.checkpoint_path == $checkpoint) and
   (.checks | type == "object" and length > 0 and all(.[]; . == true))' \
  "${MARKER}" >/dev/null; then
  echo "registered step-100 R19 completion marker is invalid or mismatched" >&2
  exit 3
fi

CAPTION_ARGS=""
DATA_FILES=("${SOURCE_MANIFEST}" "${FORMAT_PROMPT}" "${TRAINING_MANIFEST}" "${MARKER}" "${CHECKPOINT}/model.safetensors.index.json")
if [[ "${CONDITION}" == "caption" ]]; then
  if [[ "${CAPTION_RUN}" == "-" || ! -s "${CAPTION_RUN}/run_manifest.json" ]]; then
    echo "caption arm requires its completed frozen caption store" >&2
    exit 2
  fi
  if ! jq -e '(.status == "complete") and (.job_type == "caption_image_store_generation") and (.expected_shards == 3)' "${CAPTION_RUN}/run_manifest.json" >/dev/null; then
    echo "caption store manifest is not the registered complete three-shard store" >&2
    exit 2
  fi
  mapfile -t CAPTION_FILES < <(find "${CAPTION_RUN}/shards" -maxdepth 1 -type f -name 'store_shard_*.jsonl' -size +0c | sort)
  if [[ "${#CAPTION_FILES[@]}" -ne 3 ]]; then
    echo "caption store does not contain exactly three non-empty shards" >&2
    exit 2
  fi
  printf -v CAPTION_ARGS ' %q' "${CAPTION_FILES[@]}"
  CAPTION_ARGS="--caption-shards${CAPTION_ARGS}"
  DATA_FILES+=("${CAPTION_RUN}/run_manifest.json" "${CAPTION_FILES[@]}")
elif [[ "${CAPTION_RUN}" != "-" ]]; then
  echo "caption store may only be supplied for A3" >&2
  exit 2
fi

RESUME_ARGS=""
if [[ "${RESUME_FROM}" != "-" ]]; then
  if [[ ! -s "${RESUME_FROM}" ]]; then
    echo "resume source is absent or empty: ${RESUME_FROM}" >&2
    exit 2
  fi
  printf -v RESUME_ARGS ' --resume-from %q' "${RESUME_FROM}"
  DATA_FILES+=("${RESUME_FROM}")
fi

ACTIVE_PIDS="$(ssh "${NODE}" "nvidia-smi -i ${GPU} --query-compute-apps=pid --format=csv,noheader,nounits" | sed '/^[[:space:]]*$/d')"
if [[ -n "${ACTIVE_PIDS}" ]]; then
  echo "requested GPU ${NODE}:${GPU} has active compute processes: ${ACTIVE_PIDS//$'\n'/,}" >&2
  exit 75
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
PILOT_SEED_LABEL="${FOLLOWUP_SEED:-1}"
RUN_ID="${RUN_SCOPE}_geo3k_${ARM}_seed${PILOT_SEED_LABEL}_step${GLOBAL_STEP}_${NODE}_gpu${GPU}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
RUN_MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/${NODE}_gpu${GPU}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}_gpu${GPU}.pid"
OUTPUT="${RUN_DIR}/per_item.jsonl"
CACHE_DIR="/dev/shm/blind-gains/${RUN_ID}/condition_cache"
CHECKPOINT_INDEX_SHA256="$(sha256sum "${CHECKPOINT}/model.safetensors.index.json" | awk '{print $1}')"
R19_MARKER_SHA256="$(sha256sum "${MARKER}" | awk '{print $1}')"
MARKER_CHECKPOINT_INDEX_SHA256="$(jq -r '.checkpoint_index_sha256 // empty' "${MARKER}")"
if [[ "${MARKER_CHECKPOINT_INDEX_SHA256}" != "${CHECKPOINT_INDEX_SHA256}" ]]; then
  echo "R19 marker does not bind the current merged checkpoint index" >&2
  exit 3
fi

# Relocation is operational bookkeeping, not an evaluation dependency. Prefer its
# stronger full-tree provenance when available, otherwise retain the R19-bound index.
RETENTION_MARKER="$(dirname "${CHECKPOINT_REAL}")/RAW_STATE_RELOCATED.json"
RETENTION_MARKER_SHA256=""
MERGED_CHECKPOINT_SHA256=""
CHECKPOINT_PROVENANCE_MODE="r19_marker_index"
RETENTION_STATUS="absent"
if [[ -s "${RETENTION_MARKER}" ]] && jq -e \
  --arg index_sha256 "${CHECKPOINT_INDEX_SHA256}" \
  '(.merged_checkpoint_sha256 | type == "string" and length == 64) and
   any(.merged_checkpoint_files[]; .file == "huggingface/model.safetensors.index.json" and .sha256 == $index_sha256)' \
  "${RETENTION_MARKER}" >/dev/null; then
  RETENTION_MARKER_SHA256="$(sha256sum "${RETENTION_MARKER}" | awk '{print $1}')"
  MERGED_CHECKPOINT_SHA256="$(jq -r '.merged_checkpoint_sha256' "${RETENTION_MARKER}")"
  CHECKPOINT_PROVENANCE_MODE="retention_marker"
  RETENTION_STATUS="verified"
  DATA_FILES+=("${RETENTION_MARKER}")
elif [[ -e "${RETENTION_MARKER}" ]]; then
  RETENTION_STATUS="invalid_ignored"
fi
SOURCE_MANIFEST_SHA256="$(sha256sum "${SOURCE_MANIFEST}" | awk '{print $1}')"
TRAINING_MANIFEST_SHA256="$(sha256sum "${TRAINING_MANIFEST}" | awk '{print $1}')"
PROMPT_CONTRACT_JSON="$(PYTHONPATH=.:artifacts/repos/EasyR1 .venv/bin/python -c 'import json; from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT; print(json.dumps(DEFAULT_PROMPT_CONTRACT.to_dict(), sort_keys=True))')"
PROMPT_CONTRACT_SHA256="$(PYTHONPATH=.:artifacts/repos/EasyR1 .venv/bin/python -c 'from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT; print(DEFAULT_PROMPT_CONTRACT.sha256)')"
PARSER_VERSION="$(PYTHONPATH=.:artifacts/repos/EasyR1 .venv/bin/python -c 'from src.rewards.answer_reward import PARSER_VERSION; print(PARSER_VERSION)')"
REWARD_VERSION="$(PYTHONPATH=.:artifacts/repos/EasyR1 .venv/bin/python -c 'from src.rewards.pilot_reward import PILOT_REWARD_VERSION; print(PILOT_REWARD_VERSION)')"
DATA_HASH="$(sha256sum "${DATA_FILES[@]}" | sort -k2 | sha256sum | awk '{print $1}')"
COMMAND="TRANSFORMERS_OFFLINE=1 HF_HOME=${ROOT}/artifacts/hf_home CUDA_VISIBLE_DEVICES=${GPU} VLLM_WORKER_MULTIPROC_METHOD=spawn PYTHONHASHSEED=0 PYTHONPATH=${ROOT}:${ROOT}/artifacts/repos/EasyR1 .venv/bin/python scripts/run_pilot_geo3k_step100_eval.py --arm ${ARM} --condition ${CONDITION} --model-path ${CHECKPOINT_REAL} --manifest ${SOURCE_MANIFEST} --format-prompt ${FORMAT_PROMPT} --output ${OUTPUT} --cache-dir ${CACHE_DIR} --run-manifest ${RUN_MANIFEST} --source-training-manifest ${TRAINING_MANIFEST} --checkpoint-index-sha256 ${CHECKPOINT_INDEX_SHA256} ${CAPTION_ARGS}${RESUME_ARGS} --batch-size ${BATCH_SIZE} --max-model-len 8192 --max-tokens ${MAX_TOKENS} --seed ${SEED} --global-step ${GLOBAL_STEP} ${ROW_SCHEMA_ARGS}"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg job_type "${EVALUATION_JOB_TYPE}" \
  --arg arm "${ARM}" \
  --arg condition "${CONDITION}" \
  --arg node "${NODE}" \
  --arg gpu "${GPU}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_hash "${DATA_HASH}" \
  --arg source_manifest "${SOURCE_MANIFEST}" \
  --arg source_manifest_sha256 "${SOURCE_MANIFEST_SHA256}" \
  --arg training_run "${TRAINING_RUN}" \
  --arg training_manifest_sha256 "${TRAINING_MANIFEST_SHA256}" \
  --arg marker "${MARKER}" \
  --arg marker_sha256 "${R19_MARKER_SHA256}" \
  --arg checkpoint "${CHECKPOINT_REAL}" \
  --arg checkpoint_index_sha256 "${CHECKPOINT_INDEX_SHA256}" \
  --arg retention_marker "${RETENTION_MARKER}" \
  --arg retention_marker_sha256 "${RETENTION_MARKER_SHA256}" \
  --arg merged_checkpoint_sha256 "${MERGED_CHECKPOINT_SHA256}" \
  --arg checkpoint_provenance_mode "${CHECKPOINT_PROVENANCE_MODE}" \
  --arg retention_status "${RETENTION_STATUS}" \
  --arg caption_run "${CAPTION_RUN}" \
  --arg resume_from "${RESUME_FROM}" \
  --arg parser_version "${PARSER_VERSION}" \
  --arg reward_version "${REWARD_VERSION}" \
  --argjson prompt_contract "${PROMPT_CONTRACT_JSON}" \
  --arg prompt_contract_sha256 "${PROMPT_CONTRACT_SHA256}" \
  --arg command "${COMMAND}" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg output "${OUTPUT}" \
  --arg log "${LOG}" \
  --argjson batch_size "${BATCH_SIZE}" \
  --argjson max_tokens "${MAX_TOKENS}" \
  --argjson seed "${SEED}" \
  --argjson pilot_seed "${PILOT_SEED_LABEL}" \
  --argjson global_step "${GLOBAL_STEP}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: $job_type,
    arm: $arm,
    pilot_seed: $pilot_seed,
    global_step: $global_step,
    condition: $condition,
    node: $node,
    gpu_allocation: [$gpu],
    gpu_ids: [($gpu | tonumber)],
    tensor_parallel_width: 1,
    replica_count: 1,
    placement_justification: "Independent locked greedy evaluation on one A800; TP1 is required for the 3B model and does not interfere with the disjoint-GPU A2 training job.",
    placement_policy_version: "pi-2026-07-11",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $source_manifest,
    data_manifest_hash: $data_hash,
    source_manifest_sha256: $source_manifest_sha256,
    expected_row_count: 601,
    source_training_run: $training_run,
    source_training_manifest_sha256: $training_manifest_sha256,
    r19_completion_marker: $marker,
    r19_completion_marker_sha256: $marker_sha256,
    model_revision: $checkpoint,
    checkpoint_index_sha256: $checkpoint_index_sha256,
    checkpoint_provenance_mode: $checkpoint_provenance_mode,
    retention_status: $retention_status,
    retention_marker: (if $retention_marker_sha256 == "" then null else $retention_marker end),
    retention_marker_sha256: (if $retention_marker_sha256 == "" then null else $retention_marker_sha256 end),
    merged_checkpoint_sha256: (if $merged_checkpoint_sha256 == "" then null else $merged_checkpoint_sha256 end),
    caption_source_run: (if $caption_run == "-" then null else $caption_run end),
    resume_from: (if $resume_from == "-" then null else $resume_from end),
    parser_version: $parser_version,
    pilot_reward_version: $reward_version,
    prompt_contract: $prompt_contract,
    prompt_contract_sha256: $prompt_contract_sha256,
    scoring_mode: "pilot-reward-v1+canonical-v2",
    decoding: {temperature: 0, top_p: 1, n: 1, max_tokens: $max_tokens, seed: $seed},
    batch_size: $batch_size,
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    status: "running",
    stdout_stderr_log: $log,
    expected_artifacts: [$output],
    deviations: [],
    scientific_gate_decision: null
  }' > "${RUN_MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && (nohup '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${RUN_MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${ROOT}/${PID_FILE}')"
printf '%s\n' "${RUN_DIR}"
