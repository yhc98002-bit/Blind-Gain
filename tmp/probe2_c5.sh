#!/usr/bin/env bash
set -uo pipefail
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
echo "=== any geometry3k/geo3k runs mentioning 7b ==="
ls -d experiments/runs/* | grep -i -E "geo" | grep -i "7b"
echo "exit=$?"
echo "=== all geo3k-ish eval runs (tail 30) ==="
ls -d experiments/runs/* | grep -i -E "geo3k|geometry3k" | tail -30
echo "=== flagship readiness report ==="
cat reports/flagship_7b_readiness_v1.md
echo "=== caption_store_contract_geo3k_7b.json ==="
head -c 2000 reports/caption_store_contract_geo3k_7b.json
echo
echo "=== d3 condition matrix registration (head 80) ==="
sed -n '1,80p' docs/registered_d3_condition_matrix_v1.md
