#!/bin/bash
# Real-data invocation of the R3 readout in --partial (step-0 only) mode
# against the four live m7_step0_heldout_base_* runs. CPU only.
set -u
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
exec .venv/bin/python scripts/build_m7_r3_readout.py \
  --partial \
  --step0 a1_real=experiments/runs/m7_step0_heldout_base_real_an29_20260730T154447Z \
  --step0 a2_gray=experiments/runs/m7_step0_heldout_base_gray_an29_20260730T154458Z \
  --step0 a2b_noimage=experiments/runs/m7_step0_heldout_base_none_an29_20260730T154501Z \
  --step0 a3_caption=experiments/runs/m7_step0_heldout_base_caption_an29_20260730T154503Z \
  --json-output reports/m7_r3_readout_v1_partial.json \
  --markdown-output reports/m7_r3_readout_v1_partial.md
