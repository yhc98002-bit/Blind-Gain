#!/bin/bash
export PATH=$HOME/.local/bin:$PATH
R=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd $R
echo "=== m5c eval progress (gates an29 GPUs 4-5) ==="
for d in experiments/runs/m5c_sampled_m5c-taskb-step400_an29_gpu4_20260730T122620Z experiments/runs/m5c_sampled_m5c-taskb-step100-repro_an29_gpu5_20260730T122701Z; do
  echo "--- $d"
  if [ -f $d/per_item.jsonl ]; then echo "per_item lines: $(wc -l < $d/per_item.jsonl)"; ls -la $d/per_item.jsonl; else echo "no per_item.jsonl yet"; ls -la $d 2>&1 | head; fi
  for l in $d/logs/*; do [ -f "$l" ] && { echo "log $l:"; tail -4 "$l"; }; done
done
echo
echo "=== total items expected (test split filtered) ==="
python3 -c "
import json
ids=json.load(open('data/geo3k_pilot_filtered_ids.json'))
print('filtered_ids type/len:', type(ids).__name__, len(ids) if hasattr(ids,'__len__') else '?')
" 2>&1
wc -l data/geometry3k_caption_images_manifest.jsonl 2>&1
echo
echo "=== ARM4 checkpoint path existence ==="
python3 -c "import yaml;print(yaml.safe_load(open('configs/train/m7_virl_a3_caption_seed1_3b.yaml'))['trainer']['save_checkpoint_path'])" 2>&1
echo
echo "=== disk free at repo root ==="
df -h $R | tail -2
df --output=avail -B1 $R | tail -1
echo
echo "=== storage snapshot age ==="
ls -la reports/storage_usage_snapshot.json; date -u
echo
echo "=== git cleanliness of CRITICAL files ==="
git diff --stat HEAD -- docs/registered_m7_amendment_v1.md docs/registered_m7_heldout_split_v2.md docs/registered_extensions_v1.md docs/registered_m7_single_image_v2.md docs/registered_m7_seed_scope_v1.md configs/train/m7_virl_a3_caption_seed1_3b.yaml scripts/launch_m7_virl_arm.sh scripts/build_m7_heldout_split_v2.py scripts/build_m7_configs.py scripts/m7_gpu_occupancy_guard.py
echo "(empty above = byte-clean)"
