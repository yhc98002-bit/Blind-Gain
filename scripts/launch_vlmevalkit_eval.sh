#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 4 || $# -gt 6 ]]; then
  echo "Usage: $0 NODE GPU_LIST CONFIG RUN_TAG [JUDGE] [JUDGE_BASE_URL]" >&2
  exit 2
fi

NODE="$1"
GPUS="$2"
CONFIG="$3"
RUN_TAG="$4"
JUDGE="${5:-exact_matching}"
JUDGE_BASE_URL="${6:-}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! "${GPUS}" =~ ^[0-7](,[0-7])*$ ]]; then
  echo "GPU_LIST must be a comma-separated list of GPU indices 0-7" >&2
  exit 2
fi
if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "RUN_TAG must contain only lowercase letters, numbers, underscores, and hyphens" >&2
  exit 2
fi
if [[ ! "${JUDGE}" =~ ^[A-Za-z0-9_.:/-]+$ ]]; then
  echo "JUDGE contains unsupported characters" >&2
  exit 2
fi
if [[ ! -f "${ROOT}/${CONFIG}" ]]; then
  echo "Missing config: ${CONFIG}" >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="vlmevalkit_${RUN_TAG}_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
LOG="${RUN_DIR}/logs/${NODE}.log"
PID_FILE="${RUN_DIR}/pids/${NODE}.pid"
MANIFEST="${RUN_DIR}/run_manifest.json"
WORK_DIR="${RUN_DIR}/work"
VALIDATION="${RUN_DIR}/validation.json"
MODEL_NAMES="$(jq -r '.model | keys | join(",")' "${ROOT}/${CONFIG}")"
DATASET_NAMES="$(jq -r '.data | keys | join(",")' "${ROOT}/${CONFIG}")"
if [[ -z "${MODEL_NAMES}" || -z "${DATASET_NAMES}" ]]; then
  echo "Config must define at least one model and dataset" >&2
  exit 2
fi

DATASET_FILES=()
IFS=',' read -ra DATASETS <<< "${DATASET_NAMES}"
for DATASET in "${DATASETS[@]}"; do
  CANDIDATE="${ROOT}/data/vlmevalkit/${DATASET}.tsv"
  [[ -f "${CANDIDATE}" ]] && DATASET_FILES+=("${CANDIDATE}")
done
if [[ ${#DATASET_FILES[@]} -gt 0 ]]; then
  DATA_MANIFEST="$(printf '%s\n' "${DATASET_FILES[@]#${ROOT}/}" | paste -sd, -)"
  DATA_HASH="$(sha256sum "${DATASET_FILES[@]}" | sort -k2 | sha256sum | awk '{print $1}')"
else
  DATA_MANIFEST="VLMEvalKit remote dataset registry at commit 6a02ab92471a8c544ff0769da5968a29fd75971f"
  DATA_HASH=""
fi

JUDGE_ARGS="--judge ${JUDGE}"
if [[ -n "${JUDGE_BASE_URL}" ]]; then
  JUDGE_ARGS="${JUDGE_ARGS} --judge-base-url ${JUDGE_BASE_URL} --judge-key local-only"
fi
COMMAND="PYTHONPATH=artifacts/repos/VLMEvalKit LMUData=${ROOT}/data/vlmevalkit TRANSFORMERS_OFFLINE=1 HF_HOME=${ROOT}/artifacts/hf_home VLLM_WORKER_MULTIPROC_METHOD=spawn CUDA_VISIBLE_DEVICES=${GPUS} artifacts/envs/vlmevalkit/bin/python artifacts/repos/VLMEvalKit/run.py --config ${CONFIG} --work-dir ${WORK_DIR} --mode all ${JUDGE_ARGS} && .venv/bin/python scripts/validate_vlmeval_run.py --config ${CONFIG} --work-dir ${WORK_DIR} --output ${VALIDATION}"

cd "${ROOT}"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids" "${WORK_DIR}"
CONFIG_HASH="$(sha256sum "${CONFIG}" | awk '{print $1}')"
COMMAND_HASH="$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg node "${NODE}" \
  --arg gpu_allocation "${GPUS}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_path "${CONFIG}" \
  --arg config_hash "${CONFIG_HASH}" \
  --arg command_hash "${COMMAND_HASH}" \
  --arg data_manifest "${DATA_MANIFEST}" \
  --arg data_manifest_hash "${DATA_HASH}" \
  --arg model_names "${MODEL_NAMES}" \
  --arg dataset_names "${DATASET_NAMES}" \
  --arg judge "${JUDGE}" \
  --arg judge_base_url "${JUDGE_BASE_URL}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg work_dir "${WORK_DIR}" \
  --arg validation "${VALIDATION}" \
  '{
    run_id: $run_id,
    job_type: "p1_2_vlmevalkit_evaluation",
    node: $node,
    gpu_allocation: $gpu_allocation,
    git_hash: $git_hash,
    config_path: $config_path,
    config_hash: $config_hash,
    command_hash: $command_hash,
    data_manifest: $data_manifest,
    data_manifest_hash: (if $data_manifest_hash == "" then null else $data_manifest_hash end),
    model_revision: $model_names,
    datasets: ($dataset_names | split(",")),
    judge: $judge,
    judge_base_url: (if $judge_base_url == "" then null else $judge_base_url end),
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$work_dir, $validation]
  }' > "${MANIFEST}"

ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${RUN_DIR}/logs' '${RUN_DIR}/pids' '${WORK_DIR}' && (nohup '${ROOT}/.venv/bin/python' '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}' > /dev/null 2>&1 < /dev/null & echo \$! > '${PID_FILE}')"
echo "${RUN_DIR}"
echo "pid_file=${PID_FILE} log=${LOG}"
