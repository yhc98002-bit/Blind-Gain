#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 4 || $# -gt 6 ]]; then
  echo "Usage: $0 MODEL_ID LOCAL_DIR LICENSE REDISTRIBUTION [REVISION] [RUN_TAG]" >&2
  exit 2
fi

MODEL_ID="$1"
LOCAL_DIR="$2"
LICENSE="$3"
REDISTRIBUTION="$4"
REVISION="${5:-master}"
RUN_TAG="${6:-$(printf '%s' "${MODEL_ID}" | tr '/.' '--' | tr '[:upper:]' '[:lower:]')}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXPECTED_BYTES="${BLIND_GAINS_DOWNLOAD_EXPECTED_BYTES:?set BLIND_GAINS_DOWNLOAD_EXPECTED_BYTES to the model's conservative byte budget}"
DOWNLOAD_TIER="${BLIND_GAINS_DOWNLOAD_TIER:-S}"

if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "RUN_TAG must contain only lowercase letters, numbers, underscores, and hyphens" >&2
  exit 2
fi
if [[ -e "${ROOT}/${LOCAL_DIR}" ]]; then
  echo "Refusing to overwrite existing model directory: ${LOCAL_DIR}" >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="modelscope_model_${RUN_TAG}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
PID_FILE="${RUN_DIR}/pids/login.pid"
COMMAND="env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY .venv/bin/python scripts/download_modelscope_model.py --model-id ${MODEL_ID} --revision ${REVISION} --local-dir ${LOCAL_DIR} --license ${LICENSE} --redistribution ${REDISTRIBUTION} --storage-tier ${DOWNLOAD_TIER} --expected-bytes ${EXPECTED_BYTES} --notes 'P1.10 text embedding cosine'"

cd "${ROOT}"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg model_id "${MODEL_ID}" \
  --arg revision "${REVISION}" \
  --arg local_dir "${LOCAL_DIR}" \
  --arg storage_tier "${DOWNLOAD_TIER}" \
  --argjson expected_bytes "${EXPECTED_BYTES}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{
    run_id: $run_id,
    job_type: "modelscope_model_download",
    node: "login",
    gpu_allocation: [],
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: null,
    data_manifest_hash: null,
    source: "ModelScope direct domestic route",
    source_url: ("https://modelscope.cn/models/" + $model_id),
    model_revision: $revision,
    local_path: $local_dir,
    storage_tier: $storage_tier,
    expected_download_bytes: $expected_bytes,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$local_dir]
  }' > "${MANIFEST}"

nohup "${ROOT}/.venv/bin/python" scripts/run_manifest_job.py "${MANIFEST}" "${LOG}" > /dev/null 2>&1 < /dev/null &
echo $! > "${PID_FILE}"
printf '%s\n' "${RUN_DIR}"
