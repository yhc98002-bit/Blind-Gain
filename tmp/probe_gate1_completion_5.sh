#!/bin/bash
export PATH=$HOME/.local/bin:$PATH
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
echo "=== run_blind_solvability.py arg/manifest loading (head 150) ==="
head -150 scripts/run_blind_solvability.py
echo "=== G0 reports ==="
ls reports/ | grep -i -E '^g0|gate0'
echo "=== G0.1 delta-q definition ==="
for f in reports/g0_1*.json reports/g0*.md; do [ -f "$f" ] && echo "--- $f ---" && grep -l . "$f" >/dev/null && head -40 "$f"; done 2>/dev/null | head -100
echo "=== grep delta_q in reports for definition ==="
grep -rn -i -E '"delta_?q|delta_?q_definition|blind_condition' reports/g0*.json 2>/dev/null | head -20
echo "=== geo3k blind run manifest timing/count ==="
jq '{run_id, condition, split, start_time_utc, end_time_utc, item_count: (.item_count // .n_items // .items // null), status}' experiments/runs/blind_solvability_geo3k_none_an12_20260710T074918Z/run_manifest.json 2>/dev/null
wc -l experiments/runs/blind_solvability_geo3k_none_an12_20260710T074918Z/per_item.jsonl 2>/dev/null
head -1 experiments/runs/blind_solvability_geo3k_none_an12_20260710T074918Z/per_item.jsonl 2>/dev/null | jq 'keys'
echo "=== eval manifest sha256 full values ==="
jq '.evaluation_manifests' data/mini_a5_train_v1/decontamination.json
echo "=== launch_mini_a5_main.sh arm handling (head 60) ==="
head -60 scripts/launch_mini_a5_main.sh
echo "=== monitoring val format ==="
head -1 data/mini_a5_plumbing_val_v1.jsonl | jq 'keys'
wc -l data/mini_a5_plumbing_val_v1.jsonl
