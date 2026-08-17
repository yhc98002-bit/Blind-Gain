#!/usr/bin/env python3
"""Bring the M7 launcher to parity with the launchers that actually train.

A three-dimension audit against launch_mech_pilot_arm.sh, launch_mini_a5_main.sh
and launch_m5_anchor_longhorizon.sh found three BLOCKING divergences, all firing
at the same startup boundary (val_before_train, after ~10-15 min of model load
and prompt filtering), plus a set of risky ones:

  BLOCKING
  1. EASYR1_ATTN_IMPLEMENTATION unset -> EasyR1 defaults to flash_attention_2,
     which is not installed. (Observed crash.)
  2. PYTHONPATH omits ${ROOT} -> the reward actor cannot import src.*, so
     pilot_reward.py raises ModuleNotFoundError. Verified empirically.
  3. BLIND_GAINS_REWARD_SHADOW_LOG unset while all eight M7 configs set
     require_shadow_log: true -> pilot_reward raises RuntimeError.

  RISKY, fixed here
  4. No RAY_TMPDIR/TMPDIR/TMP/TEMP -> Ray spills onto the node's 32 GB root
     device. Filling that device is exactly what produced the earlier
     ncclSystemError incident on an29.
  5. Storage guard entirely unwired, so EasyR1's patched checkpoint guard is a
     no-op across a multi-day 8-arm run.
  6. No PYTORCH_CUDA_ALLOC_CONF.
  7. No flock/setsid/stdin redirection -> double-launch and orphan risk.
  8. No startup liveness probe: the script exited 0 while the trainer was dying.
  9. GPU-count unvalidated: config sets n_gpus_per_node: 4 but any list passed.

Not changed here (recorded, needs a manifest reshape): M7 invokes verl directly
rather than through run_manifest_job.py, so run_manifest.json is never finalised
on exit -- which is why it read "running" 43 minutes after the trainer died.
Crash detection is handled by external watching until that is reworked.
"""
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
p = ROOT / "scripts/launch_m7_virl_arm.sh"
t = p.read_text()

if "BLIND_GAINS_REWARD_SHADOW_LOG" in t:
    print("already patched")
    raise SystemExit(0)

# --- 1. GPU count must match the config's n_gpus_per_node ---------------------
old_gpu = '''[[ "${GPU_IDS}" =~ ^[0-7](,[0-7])*$ ]] || { echo "invalid gpu ids" >&2; exit 2; }'''
new_gpu = '''[[ "${GPU_IDS}" =~ ^[0-7](,[0-7])*$ ]] || { echo "invalid gpu ids" >&2; exit 2; }
# the config fixes n_gpus_per_node; a mismatched list silently mis-shards
GPU_COUNT="$(printf '%s' "${GPU_IDS}" | tr ',' '\\n' | sort -u | grep -c .)"
CFG_GPUS="$(grep -E '^[[:space:]]+n_gpus_per_node:' "${CONFIG}" | awk '{print $2}')"
[[ "${GPU_COUNT}" == "${CFG_GPUS}" ]] || {
  echo "gpu count ${GPU_COUNT} != config n_gpus_per_node ${CFG_GPUS}" >&2; exit 2; }'''
assert t.count(old_gpu) == 1, "gpu anchor"
t = t.replace(old_gpu, new_gpu, 1)

# --- 2. run-dir side paths ----------------------------------------------------
old_eff = '''cp "${CONFIG}" "${EFFECTIVE}"'''
new_eff = '''install -m 0444 "${CONFIG}" "${EFFECTIVE}"
SHADOW="${ROOT}/${RUN_DIR}/reward_shadow.jsonl"
STORAGE_LOG="${ROOT}/${RUN_DIR}/storage_guard.jsonl"
RAY_DIGEST="$(printf '%s' "${USER}:${NODE}:${RUN_ID}" | sha256sum | awk '{print substr($1, 1, 12)}')"
RAY_TMP_DIR="/dev/shm/bg-ray-${RAY_DIGEST}"
JOB_TMP_DIR="${RAY_TMP_DIR}/tmp"
LOCK="/dev/shm/blind_gains_${NODE}_${LABEL}.lock"'''
assert t.count(old_eff) == 1, f"effective anchor {t.count(old_eff)}"
t = t.replace(old_eff, new_eff, 1)

# --- 3. the environment the working launchers use -----------------------------
old_cmd = ('''COMMAND="cd ${ROOT} && CUDA_VISIBLE_DEVICES=${GPU_IDS} PYTHONHASHSEED=${SEED} '''
           '''TRANSFORMERS_OFFLINE=1 HF_HOME=${ROOT}/artifacts/hf_home '''
           '''PYTHONPATH=${ROOT}/artifacts/repos/EasyR1 .venv/bin/python -u -m verl.trainer.main '''
           '''config=${ROOT}/${EFFECTIVE}"''')
new_cmd = '''ENV_VARS="PYTHONUNBUFFERED=1 PYTHONFAULTHANDLER=1 HYDRA_FULL_ERROR=1 \\
PYTHONHASHSEED=0 PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True' \\
TMPDIR='${JOB_TMP_DIR}' TMP='${JOB_TMP_DIR}' TEMP='${JOB_TMP_DIR}' \\
RAY_TMPDIR='${RAY_TMP_DIR}' RAY_DEDUP_LOGS=0 \\
CUDA_VISIBLE_DEVICES='${GPU_IDS}' EASYR1_ATTN_IMPLEMENTATION=sdpa \\
BLIND_GAINS_REWARD_SHADOW_LOG='${SHADOW}' \\
BLIND_GAINS_STORAGE_GUARD_ENABLED=1 BLIND_GAINS_CHECKPOINT_TIER=S \\
BLIND_GAINS_CHECKPOINT_REQUIRED_BYTES=55000000000 \\
BLIND_GAINS_SHARED_QUOTA_ROOT='/XYFS02/HDD_POOL/paratera_xy/pxy1289' \\
BLIND_GAINS_SHARED_USAGE_SNAPSHOT='${ROOT}/reports/storage_usage_snapshot.json' \\
BLIND_GAINS_SHARED_USAGE_SNAPSHOT_MAX_AGE_SECONDS=21600 \\
BLIND_GAINS_STORAGE_GUARD_LOG='${STORAGE_LOG}' \\
BLIND_GAINS_STORAGE_GUARD_RETRY_SECONDS=300 BLIND_GAINS_STORAGE_GUARD_MAX_ATTEMPTS=0 \\
HF_HOME='${ROOT}/artifacts/hf_home' HF_DATASETS_CACHE='${ROOT}/artifacts/hf_home/datasets' \\
TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 \\
PYTHONPATH='${ROOT}/artifacts/repos/EasyR1:${ROOT}'"'''
assert t.count(old_cmd) == 1, f"command anchor {t.count(old_cmd)}"
t = t.replace(old_cmd, new_cmd, 1)

# --- 4. remote launch: setsid + flock + stdin redirect + tmp dirs -------------
import re
m = re.search(r'^ssh "\$\{NODE\}" "cd \$\{ROOT\} && \(nohup bash -lc .*?\)"$', t, re.M | re.S)
if not m:
    raise SystemExit("ssh launch anchor not found; inspect the launcher manually")
old_ssh = m.group(0)

new_ssh = ('''ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${RUN_DIR}/logs' '${RUN_DIR}/pids' '''
           ''''${RAY_TMP_DIR}' '${JOB_TMP_DIR}' && (nohup setsid flock -n --no-fork '${LOCK}' '''
           '''env ${ENV_VARS} '${ROOT}/.venv/bin/python' -u -m verl.trainer.main '''
           '''config='${ROOT}/${EFFECTIVE}' > '${ROOT}/${LOG}' 2>&1 < /dev/null '''
           '''& echo \\$! > '${ROOT}/${RUN_DIR}/pids/${NODE}.pid')"''')
t = t.replace(old_ssh, new_ssh, 1)

# --- 5. startup liveness probe ------------------------------------------------
old_sleep = "sleep 5\n"
new_sleep = '''sleep 25
REMOTE_PID="$(cat "${ROOT}/${RUN_DIR}/pids/${NODE}.pid" 2>/dev/null || true)"
if [[ -z "${REMOTE_PID}" ]] || ! ssh "${NODE}" "kill -0 '${REMOTE_PID}' 2>/dev/null"; then
  echo "M7 arm exited during startup; inspect ${LOG}" >&2
  exit 1
fi
'''
if t.count(old_sleep) == 1:
    t = t.replace(old_sleep, new_sleep, 1)
else:
    print(f"  note: sleep anchor count {t.count(old_sleep)}, liveness probe not inserted")

p.write_text(t)
print("patched scripts/launch_m7_virl_arm.sh")
