#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 5 ]]; then
  echo "usage: $0 <failed-lifecycle-run> <a1-step60-geo-run> <a2-step60-geo-run> <a2b-step60-geo-run> <a3-step60-geo-run>" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
LAUNCH_LOCK="/tmp/blindgain_pilot_seed2_recovery_lifecycle.lock"
exec 9>"${LAUNCH_LOCK}"
flock -n 9 || {
  echo "another seed-2 recovery lifecycle launcher is active" >&2
  exit 73
}
FAILED_RUN="$(realpath -m "$1")"
NEW_RUNS=("$(realpath -m "$2")" "$(realpath -m "$3")" "$(realpath -m "$4")" "$(realpath -m "$5")")
ARMS=(a1_real a2_gray a2b_noimage a3_caption)
case "${FAILED_RUN}" in
  "${ROOT}"/experiments/runs/*) ;;
  *) echo "failed lifecycle must be under experiments/runs" >&2; exit 2 ;;
esac
FAILED_MANIFEST="${FAILED_RUN}/run_manifest.json"
ORIGINAL_CHILDREN="${FAILED_RUN}/children.json"
[[ -s "${FAILED_MANIFEST}" && -s "${ORIGINAL_CHILDREN}" ]] || {
  echo "failed lifecycle inputs are absent" >&2
  exit 2
}
jq -e '
  (.job_type == "pilot_followup_evaluation_lifecycle") and
  (.pilot_seed == 2) and (.status == "fail") and
  (.performance_values_opened == false)
' "${FAILED_MANIFEST}" >/dev/null || {
  echo "source lifecycle is not the sealed failed seed-2 lifecycle" >&2
  exit 2
}

CRITICAL=(
  scripts/launch_pilot_seed2_recovery_lifecycle.sh
  scripts/watch_pilot_followup_eval_lifecycle.py
)
for file in "${CRITICAL[@]}"; do
  git ls-files --error-unmatch "${file}" >/dev/null 2>&1 || {
    echo "untracked lifecycle-critical file: ${file}" >&2
    exit 3
  }
done
git diff --quiet HEAD -- "${CRITICAL[@]}" || {
  echo "lifecycle-critical code differs from HEAD" >&2
  exit 3
}

for index in "${!NEW_RUNS[@]}"; do
  run="${NEW_RUNS[$index]}"
  arm="${ARMS[$index]}"
  case "${run}" in
    "${ROOT}"/experiments/runs/*) ;;
    *) echo "replacement queue must be under experiments/runs" >&2; exit 2 ;;
  esac
  manifest="${run}/run_manifest.json"
  [[ -s "${manifest}" ]] || { echo "replacement queue manifest absent" >&2; exit 2; }
  jq -e --arg arm "${arm}" '
    (.job_type == "pilot_followup_geo3k_evaluation_queue") and
    (.pilot_seed == 2) and (.global_step == 60) and (.arm == $arm) and
    (.performance_values_opened == false) and
    (.status == "running" or .status == "complete")
  ' "${manifest}" >/dev/null || {
    echo "replacement queue identity mismatch for ${arm}" >&2
    exit 2
  }
done

while IFS= read -r manifest; do
  [[ "$(jq -r '.job_type // ""' "${manifest}" 2>/dev/null)" == "pilot_followup_evaluation_recovery_lifecycle" ]] || continue
  [[ "$(jq -r '.status // ""' "${manifest}" 2>/dev/null)" == "running" ]] || continue
  echo "an active seed-2 recovery lifecycle already exists: $(dirname "${manifest}")" >&2
  exit 73
done < <(find experiments/runs -mindepth 2 -maxdepth 2 -name run_manifest.json -print)

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="pilot_seed2_recovery_eval_lifecycle_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
CHILDREN="${RUN_DIR}/children.json"
OUTPUT="${RUN_DIR}/lifecycle_complete.json"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"

jq \
  --arg a1 "${NEW_RUNS[0]#"${ROOT}/"}" \
  --arg a2 "${NEW_RUNS[1]#"${ROOT}/"}" \
  --arg a2b "${NEW_RUNS[2]#"${ROOT}/"}" \
  --arg a3 "${NEW_RUNS[3]#"${ROOT}/"}" '
    (.endpoints[] | select(.global_step == 60 and .arm == "a1_real").geo3k_queue_run) = $a1 |
    (.endpoints[] | select(.global_step == 60 and .arm == "a2_gray").geo3k_queue_run) = $a2 |
    (.endpoints[] | select(.global_step == 60 and .arm == "a2b_noimage").geo3k_queue_run) = $a2b |
    (.endpoints[] | select(.global_step == 60 and .arm == "a3_caption").geo3k_queue_run) = $a3
  ' "${ORIGINAL_CHILDREN}" > "${CHILDREN}"
PYTHONPATH=. .venv/bin/python -c \
  'import json,sys; from pathlib import Path; from scripts.watch_pilot_followup_eval_lifecycle import validate_children; validate_children(json.loads(Path(sys.argv[1]).read_text()), Path.cwd())' \
  "${CHILDREN}"

COMMAND="PYTHONPATH=. .venv/bin/python scripts/watch_pilot_followup_eval_lifecycle.py --children '${CHILDREN}' --output '${OUTPUT}' --poll-seconds 60"
CONFIG_HASH="$({ sha256sum "${CRITICAL[@]}"; } | sort -k2 | sha256sum | awk '{print $1}')"
DATA_HASH="$(sha256sum "${CHILDREN}" | awk '{print $1}')"
jq -n \
  --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${CONFIG_HASH}" --arg data_hash "${DATA_HASH}" \
  --arg children "${CHILDREN}" --arg command "${COMMAND}" --arg log "${LOG}" \
  --arg output "${OUTPUT}" --arg source "${FAILED_RUN#"${ROOT}/"}" \
  --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" '
  {
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "pilot_followup_evaluation_recovery_lifecycle",
    pilot_seed: 2,
    node: "login",
    gpu_ids: [],
    gpu_allocation: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "CPU-only sealed coordinator reuses successful immutable endpoints and replaces only four failed step-60 Geometry3K queues.",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $children,
    data_manifest_hash: $data_hash,
    source_failed_lifecycle: $source,
    seed: 0,
    command: $command,
    start_time_utc: $start,
    end_time_utc: null,
    status: "running",
    stdout_stderr_log: $log,
    expected_artifacts: [$children, $output],
    performance_values_opened: false,
    scientific_gate_decision: null,
    deviations: [{
      code: "replace_only_step60_geo3k_after_relocation_race",
      scientific_config_change: false
    }]
  }' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" \
  > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo "$!" > "${RUN_DIR}/pids/login.pid"
sleep 2
kill -0 "$(cat "${RUN_DIR}/pids/login.pid")" 2>/dev/null || {
  echo "seed-2 recovery lifecycle exited during startup" >&2
  exit 1
}
printf '%s\n' "${RUN_DIR}"
