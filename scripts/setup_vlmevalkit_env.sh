#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="${ROOT}/artifacts/repos/VLMEvalKit"
ENV_DIR="${ROOT}/artifacts/envs/vlmevalkit"
BASE_SITE="${ROOT}/.venv/lib/python3.10/site-packages"
EXPECTED_COMMIT="6a02ab92471a8c544ff0769da5968a29fd75971f"
INDEX_URL="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"

ACTUAL_COMMIT="$(git -C "${REPO}" rev-parse HEAD)"
if [[ "${ACTUAL_COMMIT}" != "${EXPECTED_COMMIT}" ]]; then
  echo "VLMEvalKit commit mismatch: expected ${EXPECTED_COMMIT}, found ${ACTUAL_COMMIT}" >&2
  exit 1
fi

if [[ ! -x "${ENV_DIR}/bin/python" || ! -x "${ENV_DIR}/bin/pip" ]]; then
  rm -rf "${ENV_DIR}"
  if ! python3 -m venv "${ENV_DIR}"; then
    rm -rf "${ENV_DIR}"
    virtualenv --python python3 "${ENV_DIR}"
  fi
fi

SITE_DIR="$("${ENV_DIR}/bin/python" -c 'import site; print(site.getsitepackages()[0])')"
printf '%s\n' "${BASE_SITE}" > "${SITE_DIR}/blindgain_base_env.pth"

"${ENV_DIR}/bin/python" -m pip install \
  --index-url "${INDEX_URL}" \
  --constraint "${ROOT}/configs/env/vlmevalkit_constraints.txt" \
  --editable "${REPO}"

"${ENV_DIR}/bin/python" -m pip install \
  --index-url "${INDEX_URL}" \
  --constraint "${ROOT}/configs/env/vlmevalkit_constraints.txt" \
  --requirement "${ROOT}/configs/env/vlmevalkit_extra_requirements.txt"

"${ENV_DIR}/bin/python" -m pip freeze --all > "${ENV_DIR}/requirements.freeze.txt"
PYTHONPATH="${REPO}" "${ENV_DIR}/bin/python" -c \
  'import numpy, torch, transformers, vlmeval; print(numpy.__version__, torch.__version__, transformers.__version__, vlmeval.__file__)'
