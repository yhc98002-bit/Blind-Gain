#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${ROOT}/artifacts/repos/EasyR1"
PATCH="${ROOT}/docs/easyr1_resume_safe_logger_patch.diff"
PINNED_REVISION="dd71bbd252694f5f850213eec15795b6b88d9fea"
LOGGER="${TARGET}/verl/utils/logger/logger.py"
MARKER="Preserving existing EasyR1 file logger artifact during resume"

if [[ ! -d "${TARGET}/.git" ]]; then
  echo "EasyR1 checkout not found at ${TARGET}" >&2
  exit 1
fi
if [[ "$(git -C "${TARGET}" rev-parse HEAD)" != "${PINNED_REVISION}" ]]; then
  echo "EasyR1 revision does not match ${PINNED_REVISION}" >&2
  exit 1
fi
if grep -q "${MARKER}" "${LOGGER}"; then
  echo "EasyR1 resume-safe logger patch already applied"
  exit 0
fi

git -C "${TARGET}" apply --check "${PATCH}"
git -C "${TARGET}" apply "${PATCH}"
python3 -m py_compile "${LOGGER}"
echo "Applied EasyR1 resume-safe file logger patch"
