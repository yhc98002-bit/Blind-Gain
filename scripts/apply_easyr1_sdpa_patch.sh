#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${ROOT}/artifacts/repos/EasyR1"
PATCH="${ROOT}/docs/easyr1_sdpa_patch.diff"

if [[ ! -d "${TARGET}/.git" ]]; then
  echo "EasyR1 checkout not found at ${TARGET}" >&2
  exit 1
fi

if grep -q 'EASYR1_ATTN_IMPLEMENTATION' "${TARGET}/verl/workers/fsdp_workers.py"; then
  echo "EasyR1 SDPA patch already applied"
  exit 0
fi

git -C "${TARGET}" apply "${PATCH}"
grep -q 'EASYR1_ATTN_IMPLEMENTATION' "${TARGET}/verl/workers/fsdp_workers.py"
python3 -m py_compile "${TARGET}/verl/workers/fsdp_workers.py"
echo "Applied EasyR1 SDPA patch"
