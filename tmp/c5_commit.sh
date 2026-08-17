#!/usr/bin/env bash
set -euo pipefail
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
# new files must enter the index before --only can reference them; add ONLY
# the C5 file set, never -A (other agents share this tree and index)
git add \
  scripts/build_c5_configs.py \
  scripts/launch_c5_7b_arm.sh \
  tests/test_c5_gpu_claim_guard.py \
  configs/train/c5_a1_real_seed1_7b.yaml \
  configs/train/c5_a2_gray_seed1_7b.yaml \
  reports/c5_arm_configs_v1.json \
  docs/registered_c5_7b_access_pair_v1.md
git commit --only \
  scripts/build_c5_configs.py \
  scripts/launch_c5_7b_arm.sh \
  scripts/m7_gpu_occupancy_guard.py \
  tests/test_c5_gpu_claim_guard.py \
  configs/train/c5_a1_real_seed1_7b.yaml \
  configs/train/c5_a2_gray_seed1_7b.yaml \
  reports/c5_arm_configs_v1.json \
  docs/registered_c5_7b_access_pair_v1.md \
  reports/main_progress.md \
  -m "C5 (R4): author and register the 7B access pair; close the launcher TOCTOU window

- docs/registered_c5_7b_access_pair_v1.md: two arms x one seed (A1 real,
  A2 gray by the fired precommitted M8 fork rule quoted from Extension 4);
  pure scale manipulation of the geo3k pilot recipe; Extension 4's ViRL39K
  flagship explicitly DEFERRED, not discharged. 7B model pinned by computed
  on-disk hashes (no revision marker on disk). Registered mechanics
  deviations: gpu_memory_utilization 0.6->0.45, save_model_only true both
  arms. Readout: 6-cell access matrix vs the (still unevaluated) 7B base.
- scripts/build_c5_configs.py + generated configs + reports/c5_arm_configs_v1.json:
  parity asserted programmatically; byte diff vs the 3B template is exactly
  the declared deviation set.
- scripts/launch_c5_7b_arm.sh: manifest-finalizing launch through
  run_manifest_job.py, registration/hash/model-identity/GPU-count gates,
  guard pass -> per-GPU reservation claims on the node -> guard re-check.
- scripts/m7_gpu_occupancy_guard.py: third occupancy source = reservation
  claim files (/dev/shm/blind-gains/gpu_claims); fresh (age < 30 min) or
  pid-alive claims read as occupied; fail-closed on unreadable claims;
  --ignore-claim-run-id for a launcher re-checking its own claims. Closes
  the vLLM-init TOCTOU that killed M7 arm 4's first attempt.
- tests/test_c5_gpu_claim_guard.py: adversarial fixture (I10) reproducing
  the arm-4 scenario; the old decision rule provably allows it, the new
  guard refuses; 17 tests incl. end-to-end fake-ssh runs of the real guard.
- reports/main_progress.md: corrected stale C5 row (A2b -> A2-gray, with the
  M8 fork rule citation).

NO training launched; all GPUs remain untouched. Launch ~2026-08-02 when M7
frees GPUs, through the registered launcher only.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
git log -1 --stat | head -30
