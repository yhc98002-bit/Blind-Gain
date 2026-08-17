#!/bin/bash
R=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd $R
echo "=== base model used by M7 arms ==="
grep -nE "model_path|model:" configs/train/m7_virl_a3_caption_seed1_3b.yaml | head
echo
echo "=== a REAL HF weights export of the same family (used by the m5c evals) ==="
for H in checkpoints/m5_anchor_longhorizon_400_resume150/global_step_400/actor/huggingface \
         checkpoints/anchor_a0_recipe_3b_geo3k/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_100/actor/huggingface; do
  if [ -d "$H" ]; then
    echo "--- $H"
    du -sb $H | awk '{printf "  total bytes=%s  GB_decimal=%.2f  GiB=%.2f\n",$1,$1/1e9,$1/1073741824}'
    ls -la $H | grep -iE "safetensors|bin" | head
  else echo "--- $H : ABSENT"; fi
done
echo
echo "=== any run in the project with save_model_only true and checkpoints on disk? ==="
grep -rln "save_model_only: true" configs/train/ 2>/dev/null | head
echo
echo "=== arms 2/3 step-1 completion check ==="
date -u +%H:%M:%SZ
for d in m7_virl_a2_gray_seed1_an12_20260730T121803Z m7_virl_a2b_noimage_seed1_an29_20260730T121834Z; do
  echo "--- $d"
  ls -la checkpoints/m7/$(echo $d | sed -E 's/_an[0-9]+_[0-9]{8}T[0-9]{6}Z//')/experiment_log.jsonl 2>/dev/null
  wc -l checkpoints/m7/$(echo $d | sed -E 's/_an[0-9]+_[0-9]{8}T[0-9]{6}Z//')/experiment_log.jsonl 2>/dev/null
  tail -c 600 experiments/runs/$d/logs/*.log | tr '\r' '\n' | grep -oE "Running step [0-9]+:[^|]*\|[^|]*\| [0-9.]+/100 \[[0-9:]+" | tail -2
done
