#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${ROOT}/artifacts/repos/EasyR1"
PATCH="${ROOT}/docs/easyr1_image_condition_patch.diff"
PINNED_REVISION="dd71bbd252694f5f850213eec15795b6b88d9fea"

if [[ ! -d "${TARGET}/.git" ]]; then
  echo "EasyR1 checkout not found at ${TARGET}" >&2
  exit 1
fi
if [[ "$(git -C "${TARGET}" rev-parse HEAD)" != "${PINNED_REVISION}" ]]; then
  echo "EasyR1 revision does not match ${PINNED_REVISION}" >&2
  exit 1
fi
if grep -q 'IMAGE_CONDITIONS = ' "${TARGET}/verl/utils/dataset.py"; then
  echo "EasyR1 image-condition patch already applied"
  exit 0
fi

git -C "${TARGET}" apply --check "${PATCH}"
git -C "${TARGET}" apply "${PATCH}"
grep -q 'image_condition=config.image_condition' "${TARGET}/verl/trainer/data_loader.py"
python3 -m py_compile \
  "${TARGET}/verl/utils/dataset.py" \
  "${TARGET}/verl/trainer/config.py" \
  "${TARGET}/verl/trainer/data_loader.py"
echo "Applied EasyR1 image-condition patch"
