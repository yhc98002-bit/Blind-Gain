#!/usr/bin/env bash
set -uo pipefail
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
M=artifacts/models/Qwen/Qwen2.5-VL-7B-Instruct
echo "=== 7B model dir listing ==="
ls -la "$M"
echo "=== revision markers? ==="
ls -la "$M"/.??* 2>/dev/null || echo "no dotfiles"
find "$M" -maxdepth 2 -name "*.json" | sort
echo "=== index sha256 + total_size ==="
sha256sum "$M/model.safetensors.index.json"
grep -o '"total_size": [0-9]*' "$M/model.safetensors.index.json"
echo "=== per-shard sizes and sha256 of config.json ==="
stat -c '%n %s' "$M"/*.safetensors
sha256sum "$M/config.json" "$M/generation_config.json" "$M/tokenizer_config.json" 2>/dev/null
echo "=== architecture ==="
grep -o '"architectures": \[[^]]*\]' "$M/config.json" || head -5 "$M/config.json"
echo "=== 7B base geo3k evals in experiments/runs? ==="
ls -d experiments/runs/*7b* 2>/dev/null | head -40
echo "=== geo3k+7b reports ==="
ls reports/ | grep -i 7b | head -30
echo "=== pilot corpus files ==="
sha256sum data/geo3k_pilot_filtered.jsonl data/geo3k_pilot_filtered_ids.json 2>/dev/null
echo "=== caption store shards referenced by pilot config ==="
ls -la experiments/runs/geometry3k_qwen25vl3b_captionstore384_20260710T005300Z/shards/ 2>/dev/null | head
echo "=== reward fn ==="
ls -la src/rewards/pilot_reward.py
echo "=== git status/branch ==="
git rev-parse --abbrev-ref HEAD; git rev-parse HEAD; git status --porcelain | head -20
