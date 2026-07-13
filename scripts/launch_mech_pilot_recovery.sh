#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 5 || $# -gt 6 ]]; then
  echo "usage: $0 <a1_real|a2_gray|a2b_noimage|a3_caption> <an12|an29> <gpu0,gpu1,gpu2,gpu3> <retry-tag> <failed-run-dir> [reason-code]" >&2
  exit 2
fi
ARM="$1"
NODE="$2"
GPUS="$3"
RETRY_TAG="$4"
FAILED_RUN="$5"
RECOVERY_REASON="${6:-checkpoint_guard_recursive_du_timeout_before_first_save}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
if [[ ! "${RETRY_TAG}" =~ ^retry[1-9][0-9]*$ ]]; then
  echo "retry tag must match retryN" >&2
  exit 2
fi
if [[ ! "${RECOVERY_REASON}" =~ ^[a-z0-9_]+$ ]]; then
  echo "recovery reason must be a lowercase machine reason code" >&2
  exit 2
fi
if [[ ! -s "${FAILED_RUN}/run_manifest.json" ]]; then
  echo "failed recovery source has no run manifest" >&2
  exit 2
fi
if [[ "$(jq -r '.status' "${FAILED_RUN}/run_manifest.json")" != "fail" ]]; then
  echo "pilot recovery source is not a failed run" >&2
  exit 2
fi
if [[ "$(jq -r '.arm' "${FAILED_RUN}/run_manifest.json")" != "${ARM}" ]]; then
  echo "pilot recovery arm does not match failed run" >&2
  exit 2
fi
if find "$(jq -r '.checkpoint_path' "${FAILED_RUN}/run_manifest.json")" \
  -maxdepth 1 -type d -name 'global_step_*' -print -quit 2>/dev/null | grep -q .; then
  echo "pilot recovery requires explicit resume handling when a raw checkpoint exists" >&2
  exit 2
fi

export BLIND_GAINS_PILOT_RUN_SUFFIX="${RETRY_TAG}"
export BLIND_GAINS_PILOT_RECOVERY_OF="${FAILED_RUN}"
export BLIND_GAINS_PILOT_RECOVERY_REASON="${RECOVERY_REASON}"
exec scripts/launch_mech_pilot_arm.sh "${ARM}" "${NODE}" "${GPUS}"
