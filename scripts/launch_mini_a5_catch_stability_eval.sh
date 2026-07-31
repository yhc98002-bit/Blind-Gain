#!/usr/bin/env bash
# Driver: Mini-A5 catch-trial stability evaluation (registered secondary 2).
#
# Binding registration: docs/registered_mini_a5_catch_stability_v1.md
# (instrument committed at fc57cb8, merged before this launch — I9 holds).
#
# This driver:
#   1. verifies every pinned input hash (registration section 2) on disk,
#   2. rebuilds the derived manifest via the registered adapter if absent and
#      verifies it against the tracked checksum record,
#   3. passes scripts/m7_gpu_occupancy_guard.py for the two target GPUs,
#      writes reservation claim files under /dev/shm/blind-gains/gpu_claims on
#      the node BEFORE launching, then re-runs the guard with its own claims
#      excluded (TOCTOU close, same protocol as scripts/launch_c5_7b_arm.sh),
#   4. launches ONE FlipTrack shard eval per arm (1 GPU each, single node) via
#      scripts/launch_fliptrack_eval_shards.sh on the UNBOUND path — the
#      launcher has no m6_mini_a5_registered_main binding branch, so
#      checkpoint provenance is carried out-of-band by a post-run
#      reports/ record, exactly per reports/f8_eval_plan_v1.json
#      blocking-limitations mitigation and registration section 2.4,
#   5. stamps the worker pid into each claim file so the claim stays valid
#      (pid-alive rule) for the full eval instead of expiring at 30 min.
#
# Generation regime (registration section 2.4, verbatim from the F8 cells):
# greedy, seed 0, max-new-tokens 32, image-mode real, answer-tags-v1 contract.
set -euo pipefail

ROOT="/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"
cd "${ROOT}"
export PATH="${HOME}/.local/bin:${PATH}"

NODE="an29"
GPU_CP="5"
GPU_MEMBER="7"
TS="${MINI_A5_CATCH_TS:-$(date -u +%Y%m%dT%H%M%SZ)}"
RUN_CP="experiments/runs/mini_a5_catch_cp_step120_real_${NODE}_${TS}"
RUN_MEMBER="experiments/runs/mini_a5_catch_member_step120_real_${NODE}_${TS}"
STATE_DIR="experiments/runs/mini_a5_catch_driver_state_${TS}"
MANIFEST="data/derived/mini_a5_catch_eval_manifest_v1.jsonl"
CKPT_CP="${ROOT}/checkpoints/mini_a5/mini_a5_cp_seed1/global_step_120/actor/huggingface"
CKPT_MEMBER="${ROOT}/checkpoints/mini_a5/mini_a5_same_data_seed1/global_step_120/actor/huggingface"
CLAIM_RUN_ID="mini_a5_catch_stability_v1_${TS}"
CLAIMS_NODE_DIR="/dev/shm/blind-gains/gpu_claims"

# Pinned hashes — registration docs/registered_mini_a5_catch_stability_v1.md section 2.
SHA_PAIRS="fbd83d52fa01103bfb839fa2572eb9164c532f8c3a3431da6ca8f6033d6a9728"
SHA_DECON="19ed9a833665aead2aee1f4494279a26055c4f531fed68d3e3340af8a1a16bda"
SHA_AUDIT="37b9662c1f873c6b6cb7ee04a87a954dadef54ea974933c0e50e5ab8c60c2317"
SHA_ADAPTER="b7b964f3c17f650d2355e36ab532e2893de8fb49aa51bb427a352e2fc995e93e"
SHA_MANIFEST="c4bb508f930ec47c9f3a2a4bc905693394f63bf6b4ebbd0f1332eef85afcbe4a"
SHA_PROVENANCE="47f35dce7f76e3b43902951f7a0f24cdd147d9d3e576f6fb019fcfffddaa8ad8"
SHA_SCORER="d15eaa5d878cb757aa8dbae17d446c98cd6675cdc10fbd1a23bac1d7af1d8e91"
SHA_CP_INDEX="4bb3b752a9895596f57798116b660406110198669dcfefbc213594d540baed21"
SHA_MEMBER_INDEX="b4270b12dda440fdfdb345c4c074decd1dbbe8d40c751b67392ce6d96bd037f6"

mkdir -p "${STATE_DIR}"
exec > >(tee -a "${STATE_DIR}/driver.log") 2>&1
echo "[driver] ts=${TS} node=${NODE} gpu_cp=${GPU_CP} gpu_member=${GPU_MEMBER}"
echo "[driver] run_cp=${RUN_CP}"
echo "[driver] run_member=${RUN_MEMBER}"

verify_sha() {
  local expect="$1" path="$2" got
  got="$(sha256sum "${path}" | awk '{print $1}')"
  if [[ "${got}" != "${expect}" ]]; then
    echo "[driver] HASH MISMATCH ${path}: got ${got} expected ${expect}" >&2
    exit 65
  fi
  echo "[driver] verified ${got}  ${path}"
}

# --- 1. pinned inputs ---
verify_sha "${SHA_PAIRS}" data/mini_a5_catch_v1/pairs.jsonl
verify_sha "${SHA_DECON}" data/mini_a5_catch_v1/decontamination.json
verify_sha "${SHA_AUDIT}" reports/mini_a5_catch_audit_v1.json
verify_sha "${SHA_ADAPTER}" scripts/build_mini_a5_catch_eval_manifest.py
verify_sha "${SHA_SCORER}" src/eval/catch_stability.py
verify_sha "${SHA_CP_INDEX}" "${CKPT_CP}/model.safetensors.index.json"
verify_sha "${SHA_MEMBER_INDEX}" "${CKPT_MEMBER}/model.safetensors.index.json"

# --- 2. derived manifest: rebuild if absent, then verify (launch preflight
# --- required by registration section 2.2) ---
if [[ ! -f "${MANIFEST}" ]]; then
  echo "[driver] derived manifest absent; rebuilding via registered adapter"
  PYTHONPATH=. .venv/bin/python scripts/build_mini_a5_catch_eval_manifest.py
fi
verify_sha "${SHA_MANIFEST}" "${MANIFEST}"
verify_sha "${SHA_PROVENANCE}" "${MANIFEST}.provenance.json"
TRACKED_SHA="$(jq -r '.output_sha256' experiments/manifests/mini_a5_catch_eval_manifest_v1.json)"
if [[ "${TRACKED_SHA}" != "${SHA_MANIFEST}" ]]; then
  echo "[driver] tracked checksum record disagrees with registration: ${TRACKED_SHA}" >&2
  exit 65
fi
echo "[driver] tracked record experiments/manifests/mini_a5_catch_eval_manifest_v1.json agrees"
ROWS="$(wc -l < "${MANIFEST}")"
if [[ "${ROWS}" != "300" ]]; then
  echo "[driver] manifest row count ${ROWS} != 300" >&2
  exit 65
fi

# --- 3. record git state at launch, verbatim (f8 plan recommended action) ---
git rev-parse HEAD > "${STATE_DIR}/git_head_at_launch.txt"
git status --porcelain > "${STATE_DIR}/git_status_at_launch.txt"
echo "[driver] git head at launch: $(cat "${STATE_DIR}/git_head_at_launch.txt")"

# --- 4. guard pass 1 (no self-claims yet) ---
if ! .venv/bin/python scripts/m7_gpu_occupancy_guard.py --node "${NODE}" --gpus "${GPU_CP},${GPU_MEMBER}"; then
  echo "[driver] guard refused GPUs ${GPU_CP},${GPU_MEMBER} on ${NODE}; not launching" >&2
  exit 75
fi

# --- claims BEFORE launch (TOCTOU close) ---
mkdir -p "${STATE_DIR}/gpu_claims"
CLAIMS_PLACED=0
LAUNCH_STATE="clean"
cleanup_claims() {
  if [[ "${CLAIMS_PLACED}" == 1 && "${LAUNCH_STATE}" == "clean" ]]; then
    ssh "${NODE}" "rm -f '${CLAIMS_NODE_DIR}/${NODE}_gpu${GPU_CP}.claim' '${CLAIMS_NODE_DIR}/${NODE}_gpu${GPU_MEMBER}.claim'" \
      || echo "[driver] WARNING: could not remove claims; they expire in 30 min" >&2
  elif [[ "${CLAIMS_PLACED}" == 1 ]]; then
    echo "[driver] leaving claims in place (launch state: ${LAUNCH_STATE})"
  fi
}
trap cleanup_claims EXIT

write_claim() {
  local gpu="$1" pid_json="$2" run_dir="$3"
  jq -n --arg run_id "${CLAIM_RUN_ID}" --arg node "${NODE}" \
    --argjson gpu "${gpu}" --argjson pid "${pid_json}" \
    --arg created "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg run_dir "${run_dir}" \
    '{schema_version:"blind-gains.gpu-claim.v1",run_id:$run_id,node:$node,
      gpu:$gpu,pid:$pid,created_utc:$created,
      purpose:"mini_a5_catch_stability_eval",
      registration:"docs/registered_mini_a5_catch_stability_v1.md",
      eval_run_dir:$run_dir}' \
    > "${STATE_DIR}/gpu_claims/${NODE}_gpu${gpu}.claim"
}
write_claim "${GPU_CP}" null "${RUN_CP}"
write_claim "${GPU_MEMBER}" null "${RUN_MEMBER}"
ssh "${NODE}" "mkdir -p '${CLAIMS_NODE_DIR}' && cp '${ROOT}/${STATE_DIR}/gpu_claims/'*.claim '${CLAIMS_NODE_DIR}/'"
CLAIMS_PLACED=1
echo "[driver] claims placed for GPUs ${GPU_CP},${GPU_MEMBER} run_id=${CLAIM_RUN_ID}"

# --- guard pass 2: self-claims excluded; catches a competitor that moved in ---
if ! .venv/bin/python scripts/m7_gpu_occupancy_guard.py --node "${NODE}" \
    --gpus "${GPU_CP},${GPU_MEMBER}" --ignore-claim-run-id "${CLAIM_RUN_ID}"; then
  echo "[driver] a competitor moved in during claim placement; aborting clean" >&2
  exit 75
fi

# --- 5. launch, unbound path (no PILOT/M5 binding env), seed 0 ---
unset BLIND_GAINS_PILOT_SOURCE_RUN BLIND_GAINS_PILOT_GLOBAL_STEP \
      BLIND_GAINS_M5_SOURCE_RUN BLIND_GAINS_M5_GLOBAL_STEP 2>/dev/null || true
export BLIND_GAINS_EVAL_SEED=0

LAUNCH_STATE="cp_launching"
bash scripts/launch_fliptrack_eval_shards.sh "${NODE}" 0 1 "${CKPT_CP}" "${MANIFEST}" "${RUN_CP}" 32 "${GPU_CP}" real
echo "[driver] cp arm launcher exit=0"
LAUNCH_STATE="member_launching"
bash scripts/launch_fliptrack_eval_shards.sh "${NODE}" 0 1 "${CKPT_MEMBER}" "${MANIFEST}" "${RUN_MEMBER}" 32 "${GPU_MEMBER}" real
echo "[driver] member arm launcher exit=0"
LAUNCH_STATE="launched"

# --- 6. stamp worker pids into the claims (pid-alive keeps them valid > 30 min) ---
stamp_claim() {
  local gpu="$1" run_dir="$2" pid_file pid
  pid_file="${run_dir}/pids/${NODE}_gpu${gpu}_shard0.pid"
  for _ in $(seq 1 30); do
    [[ -s "${pid_file}" ]] && break
    sleep 2
  done
  if [[ ! -s "${pid_file}" ]]; then
    echo "[driver] WARNING: pid file ${pid_file} absent; claim stays age-based" >&2
    return 0
  fi
  pid="$(tr -d '[:space:]' < "${pid_file}")"
  write_claim "${gpu}" "${pid}" "${run_dir}"
  ssh "${NODE}" "cp '${ROOT}/${STATE_DIR}/gpu_claims/${NODE}_gpu${gpu}.claim' '${CLAIMS_NODE_DIR}/'"
  echo "[driver] claim ${NODE}_gpu${gpu} stamped with pid ${pid}"
}
stamp_claim "${GPU_CP}" "${RUN_CP}"
stamp_claim "${GPU_MEMBER}" "${RUN_MEMBER}"

echo "[driver] launched. run_cp=${RUN_CP} run_member=${RUN_MEMBER} claim_run_id=${CLAIM_RUN_ID}"
