#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="${ROOT}/artifacts/repos/EasyR1"
TARGET="${1:-${ROOT}/artifacts/repos/EasyR1-mini-a5}"
PINNED_REVISION="dd71bbd252694f5f850213eec15795b6b88d9fea"
PATCHES=(
  "docs/easyr1_image_condition_patch.diff"
  "docs/easyr1_caption_condition_patch.diff"
  "docs/easyr1_multimodal_grid_patch.diff"
  "docs/easyr1_caption_pil_hash_patch.diff"
  "docs/easyr1_storage_guard_patch.diff"
  "docs/easyr1_resume_safe_logger_patch.diff"
  "docs/easyr1_sdpa_patch.diff"
  "docs/easyr1_mini_a5_pair_grouping_patch.diff"
)

if [[ ! -d "${SOURCE}/.git" ]]; then
  echo "EasyR1 source checkout is absent: ${SOURCE}" >&2
  exit 1
fi
if [[ "$(git -C "${SOURCE}" rev-parse HEAD)" != "${PINNED_REVISION}" ]]; then
  echo "EasyR1 source revision is not pinned to ${PINNED_REVISION}" >&2
  exit 1
fi
if [[ -e "${TARGET}" ]]; then
  echo "refusing to replace existing mini-A5 worktree target: ${TARGET}" >&2
  exit 1
fi

cleanup_failed_worktree() {
  status=$?
  if [[ ${status} -ne 0 && -e "${TARGET}" ]]; then
    git -C "${SOURCE}" worktree remove --force "${TARGET}" >/dev/null 2>&1 || true
  fi
  exit "${status}"
}
trap cleanup_failed_worktree EXIT

git -C "${SOURCE}" worktree add --detach "${TARGET}" "${PINNED_REVISION}"
for patch in "${PATCHES[@]}"; do
  git -C "${TARGET}" apply --check "${ROOT}/${patch}"
  git -C "${TARGET}" apply "${ROOT}/${patch}"
done

PYTHONPATH="${ROOT}:${TARGET}" "${ROOT}/.venv/bin/python" -m py_compile \
  "${TARGET}/verl/trainer/config.py" \
  "${TARGET}/verl/trainer/data_loader.py" \
  "${TARGET}/verl/trainer/ray_trainer.py" \
  "${TARGET}/verl/utils/dataset.py" \
  "${TARGET}/verl/workers/reward/function.py"

grep -q 'pair_group_mode: str = "none"' "${TARGET}/verl/trainer/config.py"
grep -q 'compute_pair_level_grpo_advantage' "${TARGET}/verl/trainer/ray_trainer.py"
grep -q 'pair_rollout_index' "${TARGET}/verl/workers/reward/function.py"

trap - EXIT
printf '%s\n' "${TARGET}"
