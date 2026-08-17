#!/bin/bash
set -euo pipefail
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
git commit --only \
  docs/registered_mini_a5_gate1_completion_v1.md \
  configs/train/mini_a5_std_3b_v1.yaml \
  configs/train/mini_a5_necessity_3b_v1.yaml \
  -m "Gate-1 completion: register arms 1 (standard) and 3 (necessity); author both configs

Registration docs/registered_mini_a5_gate1_completion_v1.md filed before any
optimizer step (I9). Configs mirror the member arm byte-for-byte except
train_files/experiment_name/save_checkpoint_path. Arm-1 corpus and the arm-3
delta-q measurement pass are registered prework (T1-T7); no training launched.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
git log --oneline -1
