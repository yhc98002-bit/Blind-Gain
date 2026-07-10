#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VIRTUALENV_BIN="${VIRTUALENV_BIN:-virtualenv}"
PYPI_MIRROR="${PYPI_MIRROR:-https://pypi.tuna.tsinghua.edu.cn/simple}"
ENV_DIR="${ROOT}/.venv-ocr"

cd "${ROOT}"
if [[ ! -x "${ENV_DIR}/bin/pip" ]]; then
  rm -rf "${ENV_DIR}"
  "${VIRTUALENV_BIN}" --python "${PYTHON_BIN}" "${ENV_DIR}"
fi
"${ENV_DIR}/bin/python" -m pip install --upgrade pip
"${ENV_DIR}/bin/python" -m pip install \
  --index-url "${PYPI_MIRROR}" \
  --requirement configs/env/ocr_requirements.txt
"${ENV_DIR}/bin/python" -m pip check
"${ENV_DIR}/bin/python" - <<'PY'
import cv2
import numpy
import onnxruntime
from rapidocr_onnxruntime import RapidOCR

engine = RapidOCR()
assert engine is not None
print(
    {
        "cv2": cv2.__version__,
        "numpy": numpy.__version__,
        "onnxruntime": onnxruntime.__version__,
    }
)
PY
