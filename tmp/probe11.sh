#!/bin/bash
R=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd $R
echo "=== arm1 checkpoint tree total (5 ckpts now) ==="
du -sh checkpoints/m7/m7_virl_a1_real_seed1
echo
echo "=== arm1 global_step_100 breakdown ==="
du -sh checkpoints/m7/m7_virl_a1_real_seed1/global_step_100
find checkpoints/m7/m7_virl_a1_real_seed1/global_step_100 -maxdepth 2 -type d | while read d; do echo "$(du -sh $d | cut -f1)  $d"; done
echo
echo "=== the HF-weights-only subtree (what save_model_only writes) ==="
H=checkpoints/m7/m7_virl_a1_real_seed1/global_step_100/actor/huggingface
du -sb $H | awk '{printf "bytes=%s  GB_decimal=%.2f  GiB=%.2f\n",$1,$1/1e9,$1/1073741824}'
ls -la $H
echo
echo "=== per-checkpoint sizes, bytes ==="
for s in 20 40 60 80 100; do
  d=checkpoints/m7/m7_virl_a1_real_seed1/global_step_$s
  du -sb $d | awk -v s=$s '{printf "step %s: bytes=%s GiB=%.2f\n",s,$1,$1/1073741824}'
done
