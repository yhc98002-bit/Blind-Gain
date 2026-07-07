#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-$(pwd)}"
PYTHON="${PYTHON:-python3}"
PIP_INDEX="${PIP_INDEX:-https://pypi.tuna.tsinghua.edu.cn/simple}"
TORCH_INDEX="${TORCH_INDEX:-https://download.pytorch.org/whl/cu121}"
TORCH_VERSION="${TORCH_VERSION:-2.5.1}"
TORCHVISION_VERSION="${TORCHVISION_VERSION:-0.20.1}"
VENV="${VENV:-$ROOT/.venv}"

cd "$ROOT"

if [[ -d "$VENV" && ( ! -x "$VENV/bin/python" || ! -f "$VENV/bin/activate" ) ]]; then
  rm -rf "$VENV"
fi

if [[ ! -x "$VENV/bin/python" || ! -f "$VENV/bin/activate" ]]; then
  "$PYTHON" -m venv "$VENV" || true
  if [[ ! -x "$VENV/bin/python" || ! -f "$VENV/bin/activate" ]]; then
    rm -rf "$VENV"
    "$PYTHON" -m pip install --user -U virtualenv -i "$PIP_INDEX"
    "$PYTHON" -m virtualenv "$VENV"
  fi
fi

source "$VENV/bin/activate"

python -m pip install -U pip setuptools wheel -i "$PIP_INDEX"
python -m pip install "torch==$TORCH_VERSION" "torchvision==$TORCHVISION_VERSION" --index-url "$TORCH_INDEX"
python -m pip install -U \
  numpy pillow matplotlib opencv-python-headless pandas scipy scikit-learn \
  pytest pyyaml tqdm requests rich jsonlines jinja2 beautifulsoup4 lxml \
  datasets transformers accelerate peft deepspeed modelscope \
  -i "$PIP_INDEX" --upgrade-strategy only-if-needed

python scripts/check_env.py
