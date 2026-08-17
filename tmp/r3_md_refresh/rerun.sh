#!/usr/bin/env bash
# Two-seed R3 readout (registered estimator, docs/registered_m7_amendment_v1.md:52).
# Fired once both seed-2 evals (a2_gray, a3_caption) reach status complete.
# Seed-1 run dirs verbatim from reports/m7_r3_readout_v1.json provenance.runs.
set -euo pipefail
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
exec .venv/bin/python scripts/build_m7_r3_readout.py \
  --step0 a1_real=experiments/runs/m7_step0_heldout_base_real_an29_20260730T154447Z \
  --step0 a2_gray=experiments/runs/m7_step0_heldout_base_gray_an29_20260730T154458Z \
  --step0 a2b_noimage=experiments/runs/m7_step0_heldout_base_none_an29_20260730T154501Z \
  --step0 a3_caption=experiments/runs/m7_step0_heldout_base_caption_an29_20260730T154503Z \
  --step100 a1_real=experiments/runs/m7_step100_heldout_a1_real_an29_20260731T161352Z \
  --step100 a2_gray=experiments/runs/m7_step100_heldout_a2_gray_gray_an12_20260803T151508Z \
  --step100 a2b_noimage=experiments/runs/m7_step100_heldout_a2b_none_an29_20260801T014325Z \
  --step100 a3_caption=experiments/runs/m7_step100_heldout_a3_caption_caption_an12_20260803T151440Z \
  --step100-seed2 a1_real=experiments/runs/m7_step100_heldout_seed2_a1_real_seed2_real_an29_20260809T144439Z \
  --step100-seed2 a2b_noimage=experiments/runs/m7_step100_heldout_seed2_a2b_noimage_seed2_none_an29_20260811T041120Z \
  --step100-seed2 a2_gray=experiments/runs/m7_step100_heldout_seed2_a2_gray_seed2_gray_an12_20260816T082503Z \
  --step100-seed2 a3_caption=experiments/runs/m7_step100_heldout_seed2_a3_caption_seed2_caption_an29_20260816T082631Z \
  --artifact-dir tmp/r3_md_refresh/artifacts \
  --json-output tmp/r3_md_refresh/out.json \
  --markdown-output tmp/r3_md_refresh/out.md
