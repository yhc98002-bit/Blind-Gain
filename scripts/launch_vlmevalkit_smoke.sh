#!/usr/bin/env bash
set -euo pipefail

NODE="${1:-an29}"
GPUS="${2:-1}"
CONFIG="${3:-configs/eval/vlmevalkit_p1_2_smoke.json}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

exec "${ROOT}/scripts/launch_vlmevalkit_eval.sh" "${NODE}" "${GPUS}" "${CONFIG}" smoke
