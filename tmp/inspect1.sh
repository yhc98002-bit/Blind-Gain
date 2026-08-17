#!/usr/bin/env bash
export PATH=$HOME/.local/bin:$PATH
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
echo "=== HEAD ==="
git rev-parse HEAD
echo "=== m7 configs present ==="
ls -la configs/train/ | grep m7 || echo NONE
echo "=== git tracked m7 configs ==="
git ls-files configs/train | grep m7 || echo NONE
echo "=== manifest exists ==="
ls -la reports/m7_arm_configs_v1.json 2>&1
echo "=== manifest config entries ==="
jq -r '.configs[] | "\(.config) \(.config_sha256[0:16]) steps=\(.max_steps) gpus=\(.n_gpus_per_node)"' reports/m7_arm_configs_v1.json 2>&1
echo "=== checkpoints/m7 ==="
ls -la checkpoints/m7 2>&1
echo "=== seed_scope doc tracked+clean? ==="
git ls-files --error-unmatch docs/registered_m7_seed_scope_v1.md && echo TRACKED
git diff --quiet HEAD -- docs/registered_m7_seed_scope_v1.md && echo CLEAN || echo DIRTY
echo "=== critical files diff vs HEAD ==="
for F in docs/registered_m7_amendment_v1.md docs/registered_m7_heldout_split_v2.md docs/registered_extensions_v1.md docs/registered_m7_single_image_v2.md scripts/launch_m7_virl_arm.sh scripts/build_m7_heldout_split_v2.py scripts/build_m7_configs.py; do
  if git diff --quiet HEAD -- "$F"; then echo "CLEAN $F"; else echo "DIRTY $F"; fi
done
echo "=== recent m7 run dirs ==="
ls -1dt experiments/runs/*m7* 2>/dev/null | head -10
