#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_DIR="${ROOT}/.venv-m11"
REQUIREMENTS="${ROOT}/configs/env/m11_runtime_requirements_v2.txt"
FREEZE_V1="${ROOT}/reports/m11_runtime_freeze_v1.txt"
AUDIT_V1="${ROOT}/reports/m11_runtime_audit_v1.json"
FREEZE_V2="${ROOT}/reports/m11_runtime_freeze_v2.txt"
AUDIT_V2="${ROOT}/reports/m11_runtime_audit_v2.json"
MODEL_NODE="${BLIND_GAINS_M11_MODEL_NODE:-an29}"
MODEL_PATH="${BLIND_GAINS_M11_INTERNVL_PATH:-/dev/shm/blind-gains/models/InternVL3-9B}"
CACHE_DIR="/tmp/blind-gains-m11-pip-cache-v2"
PROXY="http://127.0.0.1:7890"

cd "${ROOT}"
for path in "${FREEZE_V2}" "${AUDIT_V2}"; do
  if [[ -e "${path}" ]]; then
    echo "refusing to overwrite M11 v2 runtime artifact: ${path}" >&2
    exit 73
  fi
done
if [[ ! -x "${ENV_DIR}/bin/python" ]]; then
  echo "M11 v1 environment is absent: ${ENV_DIR}" >&2
  exit 2
fi
if [[ ! -s "${AUDIT_V1}" || ! -s "${FREEZE_V1}" ]] || ! jq -e \
  '(.status == "pass") and (.schema_version == "blind-gains.m11-runtime-audit.v1")' \
  "${AUDIT_V1}" >/dev/null; then
  echo "M11 v1 runtime evidence is absent or non-pass" >&2
  exit 2
fi
if [[ "$(jq -r '.freeze_sha256' "${AUDIT_V1}")" != "$(sha256sum "${FREEZE_V1}" | awk '{print $1}')" ]]; then
  echo "M11 v1 freeze hash mismatch" >&2
  exit 2
fi
if ! ssh "${MODEL_NODE}" "test -s '${MODEL_PATH}/modeling_internvl_chat.py'"; then
  echo "InternVL dynamic model source is absent on ${MODEL_NODE}: ${MODEL_PATH}" >&2
  exit 2
fi

mkdir -p "${CACHE_DIR}"
export HTTP_PROXY="${PROXY}"
export HTTPS_PROXY="${PROXY}"
export ALL_PROXY="${PROXY}"
export http_proxy="${PROXY}"
export https_proxy="${PROXY}"
export all_proxy="${PROXY}"
export PIP_CACHE_DIR="${CACHE_DIR}"
export PIP_DEFAULT_TIMEOUT=180

"${ENV_DIR}/bin/python" -m pip install \
  --index-url https://pypi.org/simple \
  --upgrade-strategy only-if-needed \
  --requirement "${REQUIREMENTS}"
"${ENV_DIR}/bin/python" -m pip check
"${ENV_DIR}/bin/python" -m pip freeze --all > "${FREEZE_V2}.partial"
mv "${FREEZE_V2}.partial" "${FREEZE_V2}"

ssh "${MODEL_NODE}" "cd '${ROOT}' && env CUDA_VISIBLE_DEVICES='' TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 PYTHONPATH=. '${ENV_DIR}/bin/python' scripts/verify_m11_runtime_v2.py --requirements '${REQUIREMENTS}' --freeze '${FREEZE_V2}' --model-path '${MODEL_PATH}' --output '${AUDIT_V2}'"
jq -e '(.status == "pass") and (.checks | type == "object" and all(. == true))' \
  "${AUDIT_V2}" >/dev/null
