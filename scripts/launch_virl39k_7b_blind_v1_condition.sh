#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export VIRL_MODEL_PATH="${VIRL_MODEL_PATH:-/dev/shm/blind-gains/models/Qwen2.5-VL-7B-Instruct}"
export VIRL_MODEL_LOCATION="node-local"
export VIRL_MODEL_REVISION="Qwen/Qwen2.5-VL-7B-Instruct@cc594898137f460bfe9f0759e9844b3ce807cfb5"
export VIRL_CAPTION_RUN="experiments/runs/virl39k_sample4096_qwen25vl7b_captionstore384_retry_20260710T163500Z"
export VIRL_CAPTION_EXPECTED_SHARDS=1
export VIRL_RUN_PREFIX="blind_solvability_virl39k_7b_v1"
export VIRL_JOB_TYPE="m8_virl39k_7b_blind_solvability_v1"

exec "${ROOT}/scripts/launch_virl39k_blind_v1_condition.sh" "$@"
