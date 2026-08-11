#!/usr/bin/env bash
# Replay the published seed-1 R3 invocation to scratch paths and diff against
# reports/m7_r3_readout_v1.json. Read-only with respect to every published
# artifact: the script refuses to overwrite outputs or an existing artifact dir.
set -euo pipefail
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain

OUT=experiments/scratch_twoseed/replay
rm -rf "$OUT"
mkdir -p "$OUT"

.venv/bin/python scripts/build_m7_r3_readout.py \
  --step0 a1_real=experiments/runs/m7_step0_heldout_base_real_an29_20260730T154447Z \
  --step0 a2_gray=experiments/runs/m7_step0_heldout_base_gray_an29_20260730T154458Z \
  --step0 a2b_noimage=experiments/runs/m7_step0_heldout_base_none_an29_20260730T154501Z \
  --step0 a3_caption=experiments/runs/m7_step0_heldout_base_caption_an29_20260730T154503Z \
  --step100 a1_real=experiments/runs/m7_step100_heldout_a1_real_an29_20260731T161352Z \
  --step100 a2_gray=experiments/runs/m7_step100_heldout_a2_gray_gray_an12_20260803T151508Z \
  --step100 a2b_noimage=experiments/runs/m7_step100_heldout_a2b_none_an29_20260801T014325Z \
  --step100 a3_caption=experiments/runs/m7_step100_heldout_a3_caption_caption_an12_20260803T151440Z \
  --json-output "$OUT/replay.json" \
  --markdown-output "$OUT/replay.md" \
  --artifact-dir "$OUT/replay_artifacts"

echo "REPLAY_DONE"
