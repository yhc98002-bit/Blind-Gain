#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_DIR="${ROOT}/.venv-m11"
REQUIREMENTS="${ROOT}/configs/env/m11_runtime_requirements.txt"
FREEZE="${ROOT}/reports/m11_runtime_freeze_v1.txt"
AUDIT="${ROOT}/reports/m11_runtime_audit_v1.json"
CACHE_DIR="/tmp/blind-gains-m11-pip-cache"
PROXY="http://127.0.0.1:7890"

cd "${ROOT}"
for path in "${ENV_DIR}" "${FREEZE}" "${AUDIT}"; do
  if [[ -e "${path}" ]]; then
    echo "refusing to overwrite M11 runtime artifact: ${path}" >&2
    exit 73
  fi
done
mkdir -p "${CACHE_DIR}"
python3 -m venv "${ENV_DIR}"

export HTTP_PROXY="${PROXY}"
export HTTPS_PROXY="${PROXY}"
export ALL_PROXY="${PROXY}"
export http_proxy="${PROXY}"
export https_proxy="${PROXY}"
export all_proxy="${PROXY}"
export PIP_CACHE_DIR="${CACHE_DIR}"
export PIP_DEFAULT_TIMEOUT=180

"${ENV_DIR}/bin/python" -m pip install \
  --index-url https://download.pytorch.org/whl/cu118 \
  --extra-index-url https://pypi.org/simple \
  'torch==2.6.0+cu118' 'torchvision==0.21.0+cu118'
"${ENV_DIR}/bin/python" -m pip install \
  --index-url https://pypi.org/simple \
  --requirement "${REQUIREMENTS}"
"${ENV_DIR}/bin/python" -m pip check

FREEZE_PARTIAL="${FREEZE}.partial"
"${ENV_DIR}/bin/python" -m pip freeze --all > "${FREEZE_PARTIAL}"
mv "${FREEZE_PARTIAL}" "${FREEZE}"
PYTHONPATH=. "${ENV_DIR}/bin/python" scripts/verify_m11_runtime.py \
  --requirements "${REQUIREMENTS}" \
  --freeze "${FREEZE}" \
  --output "${AUDIT}"
