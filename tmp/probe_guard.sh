#!/usr/bin/env bash
# read-only dry-proof of the GPU-scope colocation guard. Starts nothing.
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "${ROOT}"
probe() {
  local node="$1" gpus="$2" expect="$3"
  echo "=================== PROBE node=${node} gpus=${gpus} expect=${expect}"
  set +e
  python3 "${ROOT}/scripts/m7_gpu_occupancy_guard.py" --node "${node}" --gpus "${gpus}"
  local rc=$?
  set -e
  echo "---> exit=${rc} (0=allow, 75=refuse) expected=${expect}"
  if [[ "${rc}" == "${expect}" ]]; then echo "---> PROBE MATCHES EXPECTATION"; else echo "---> PROBE MISMATCH"; fi
}
probe an12 4,5,6,7 0
probe an12 2,3,4,5 75
probe an12 0,1,2,3 75
probe an29 0,1,2,3 0
probe an29 4,5 75
probe nosuchnode99 4,5,6,7 75
echo "=================== PROBES DONE"
