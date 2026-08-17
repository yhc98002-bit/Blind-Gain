#!/usr/bin/env bash
set -euo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
NODE="$(hostname)"
cd "$ROOT"
mkdir -p logs

claim() {
  local GPU="$1"
  local USED
  USED="$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "${GPU}")"
  if [[ "${USED}" -gt 1000 ]]; then
    echo "REFUSE gpu=${GPU} already holds ${USED} MiB -- not contending" >&2
    return 1
  fi
  echo "gpu=${GPU} free (${USED} MiB)"
  return 0
}

launch() {
  local GPU="$1"
  local SCALE="$2"
  claim "${GPU}" || return 1
  setsid nohup "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_e1c_blind_queue.py" \
    --node "${NODE}" --gpu "${GPU}" \
    --queue-log "${ROOT}/logs/e1c_blind_queue_${NODE}_gpu${GPU}.log" \
    --cell "e1c_mmvp${SCALE}=configs/eval/layer1_blind_mmvp_${SCALE}.json" \
    --cell "e1c_hallusion${SCALE}=configs/eval/layer1_blind_hallusion_${SCALE}.json" \
    --cell "e1c_mmmu${SCALE}=configs/eval/layer1_blind_mmmu_${SCALE}.json" \
    --cell "e1c_blink${SCALE}=configs/eval/layer1_blind_blink_${SCALE}.json" \
    --cell "e1c_mathverse${SCALE}=configs/eval/layer1_blind_mathverse_${SCALE}.json" \
    > "${ROOT}/logs/e1c_blind_queue_${NODE}_gpu${GPU}.boot" 2>&1 < /dev/null &
  echo "LAUNCHED node=${NODE} gpu=${GPU} scale=${SCALE} pid=$!"
}

launch 6 3b
launch 7 7b
sleep 3
echo "--- queue logs ---"
tail -n 3 "${ROOT}"/logs/e1c_blind_queue_"${NODE}"_gpu{6,7}.log 2>/dev/null || true
