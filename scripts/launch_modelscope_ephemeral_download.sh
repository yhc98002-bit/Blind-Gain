#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 7 || $# -gt 8 ]]; then
  echo "Usage: $0 NODE MODEL_ID REVISION LOCAL_DIR LICENSE REDISTRIBUTION EXPECTED_BYTES [RUN_TAG]" >&2
  exit 2
fi

NODE="$1"
MODEL_ID="$2"
REVISION="$3"
LOCAL_DIR="$4"
LICENSE="$5"
REDISTRIBUTION="$6"
EXPECTED_BYTES="$7"
RUN_TAG="${8:-$(printf '%s' "${MODEL_ID}" | tr '/.' '--' | tr '[:upper:]' '[:lower:]')}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE_PROXY_PORT="${BLIND_GAINS_REMOTE_PROXY_PORT:-17890}"

if [[ ! "${NODE}" =~ ^(an12|an29)$ ]]; then
  echo "NODE must be an12 or an29" >&2
  exit 2
fi
if [[ ! "${MODEL_ID}" =~ ^[A-Za-z0-9._/-]+$ || ! "${REVISION}" =~ ^[A-Za-z0-9._/-]+$ ]]; then
  echo "MODEL_ID and REVISION contain unsupported characters" >&2
  exit 2
fi
if [[ ! "${LOCAL_DIR}" =~ ^/dev/shm/blind-gains/[A-Za-z0-9._/-]+$ || "${LOCAL_DIR}" == *".."* ]]; then
  echo "Ephemeral model path must be under /dev/shm/blind-gains" >&2
  exit 2
fi
if [[ ! "${LICENSE}" =~ ^[A-Za-z0-9[:space:]._,:/()+-]+$ || ! "${REDISTRIBUTION}" =~ ^[A-Za-z0-9[:space:]._,:/()+-]+$ ]]; then
  echo "LICENSE or REDISTRIBUTION contains unsupported shell characters" >&2
  exit 2
fi
if [[ ! "${EXPECTED_BYTES}" =~ ^[1-9][0-9]*$ ]]; then
  echo "EXPECTED_BYTES must be positive" >&2
  exit 2
fi
if [[ ! "${REMOTE_PROXY_PORT}" =~ ^[1-9][0-9]*$ ]]; then
  echo "BLIND_GAINS_REMOTE_PROXY_PORT must be a valid integer" >&2
  exit 2
fi
if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "RUN_TAG must contain lowercase letters, numbers, underscores, or hyphens" >&2
  exit 2
fi

cd "${ROOT}"
if [[ ! -x .venv/bin/ms ]]; then
  echo "ModelScope CLI is unavailable in the registered environment" >&2
  exit 2
fi
if ssh "${NODE}" "test -e '${LOCAL_DIR}'"; then
  echo "Refusing to overwrite existing ephemeral model path: ${NODE}:${LOCAL_DIR}" >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="modelscope_ephemeral_${RUN_TAG}_${NODE}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
CHECKOUT_MANIFEST="${RUN_DIR}/model_checkout.json"
LOG="${RUN_DIR}/logs/${NODE}.log"
WRAPPER_LOG="${RUN_DIR}/logs/login_ssh.log"
PID_FILE="${RUN_DIR}/pids/login_ssh.pid"
COMMAND="env http_proxy=http://127.0.0.1:${REMOTE_PROXY_PORT} https_proxy=http://127.0.0.1:${REMOTE_PROXY_PORT} HTTP_PROXY=http://127.0.0.1:${REMOTE_PROXY_PORT} HTTPS_PROXY=http://127.0.0.1:${REMOTE_PROXY_PORT} .venv/bin/python scripts/download_modelscope_model.py --model-id ${MODEL_ID} --revision ${REVISION} --local-dir ${LOCAL_DIR} --license '${LICENSE}' --redistribution '${REDISTRIBUTION}' --storage-tier T --expected-bytes ${EXPECTED_BYTES} --allow-memory-filesystem --checkout-manifest ${CHECKOUT_MANIFEST} --notes 'L9 strong question-blind captioner; ephemeral weights; delete after caption stores commit'"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg node "${NODE}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg model_id "${MODEL_ID}" \
  --arg revision "${REVISION}" \
  --arg local_dir "${LOCAL_DIR}" \
  --arg license "${LICENSE}" \
  --arg redistribution "${REDISTRIBUTION}" \
  --arg command "${COMMAND}" \
  --arg checkout_manifest "${CHECKOUT_MANIFEST}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --argjson expected_bytes "${EXPECTED_BYTES}" \
  --argjson reverse_proxy_port "${REMOTE_PROXY_PORT}" \
  '{
    run_id: $run_id,
    job_type: "modelscope_ephemeral_model_download",
    node: $node,
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "CPU/network-only ModelScope download directly into node-local /dev/shm for a future single-node TP4 serving job; no GPU is allocated.",
    placement_policy_version: "pi-2026-07-11",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: null,
    data_manifest_hash: null,
    source: "ModelScope via international-proxy fallback after direct-route failure",
    source_url: ("https://modelscope.cn/models/" + $model_id),
    model_revision: $revision,
    license: $license,
    redistribution: $redistribution,
    local_path: $local_dir,
    storage_tier: "dev-shm-ephemeral",
    expected_download_bytes: $expected_bytes,
    reverse_proxy_port: $reverse_proxy_port,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$local_dir, $checkout_manifest],
    deviations: ["Direct ModelScope route failed during the 2026-07-11 probe; this run uses the logged international-proxy fallback through an SSH reverse tunnel."]
  }' > "${MANIFEST}"

nohup "${ROOT}/.venv/bin/python" scripts/run_reverse_proxy_manifest_job.py \
  --node "${NODE}" \
  --remote-proxy-port "${REMOTE_PROXY_PORT}" \
  --manifest "${ROOT}/${MANIFEST}" \
  --log "${ROOT}/${LOG}" \
  --wrapper-log "${ROOT}/${WRAPPER_LOG}" \
  > /dev/null 2>&1 < /dev/null &
echo $! > "${PID_FILE}"
printf '%s\n' "${RUN_DIR}"
