#!/bin/bash
export PATH=$HOME/.local/bin:$PATH
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
echo "=== git status/branch ==="
git branch --show-current
git log --oneline -3
git status --short | head -30
echo "=== mini_a5 scripts ==="
ls scripts/ | grep -i -E 'mini_a5|gate1|necessity|blind_solv' 
echo "=== build config scripts ==="
ls scripts/ | grep -i -E 'build.*config|config.*build'
echo "=== corpus audit ==="
jq . reports/mini_a5_corpus_audit_v1.json 2>/dev/null | head -80
echo "=== decontamination.json keys ==="
jq 'keys' data/mini_a5_train_v1/decontamination.json
echo "=== train.jsonl row count and first-row keys ==="
wc -l data/mini_a5_train_v1/train.jsonl data/mini_a5_train_v1/pairs.jsonl
head -1 data/mini_a5_train_v1/train.jsonl | jq 'keys'
echo "=== first row sample (truncated fields) ==="
head -1 data/mini_a5_train_v1/train.jsonl | jq 'with_entries(if (.value|type)=="string" and (.value|length)>200 then .value=(.value[:200]+"...") else . end)'
echo "=== pairs.jsonl first row ==="
head -1 data/mini_a5_train_v1/pairs.jsonl | jq 'with_entries(if (.value|type)=="string" and (.value|length)>200 then .value=(.value[:200]+"...") else . end)'
