#!/bin/bash
export PATH=$HOME/.local/bin:$PATH
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
echo "=== load_geometry_rows ==="
grep -n -A 40 'def load_geometry_rows' src/eval/blind_solvability.py | head -60
echo "=== gate0 q definition ==="
jq '.inputs // .definitions // .provenance // empty' reports/gate0_stratification_v1.json 2>/dev/null | head -40
grep -o -E '"(p_sample|pass_at_k16|pass_at_g|q_blind[a-z_]*|q_real[a-z_]*|delta_q[a-z_]*)"' reports/gate0_stratification_v1.json | sort | uniq -c
echo "=== overlay patch pair/adjacency handling ==="
grep -n -E 'adjacen|pair_group|validate_pair|sampler|Sampler|shuffle' docs/easyr1_mini_a5_pair_grouping_patch.diff | head -30
echo "=== smoke config diff vs member main ==="
diff configs/train/mini_a5_member_plumbing_smoke_v1.yaml configs/train/mini_a5_same_data_3b_v1.yaml | head -40
echo "=== member/cp config diff (verify matched-difference) ==="
diff configs/train/mini_a5_same_data_3b_v1.yaml configs/train/mini_a5_cp_3b_v1.yaml
echo "=== sha256 of current key inputs ==="
sha256sum configs/train/mini_a5_same_data_3b_v1.yaml src/rewards/cp_grpo_reward.py src/train/cp_grouping.py data/mini_a5_train_v1/train.parquet data/mini_a5_train_v1/train.jsonl data/mini_a5_train_v1/pairs.jsonl data/mini_a5_train_v1/decontamination.json data/mini_a5_plumbing_val_v1.jsonl docs/easyr1_mini_a5_pair_grouping_patch.diff scripts/launch_mini_a5_main.sh reports/f8_mini_a5_endpoint_readout_v1.md reports/mini_a5_corpus_audit_v1.json 2>/dev/null
echo "=== g02 refinement json: q fields ==="
jq '.definitions // .q_definition // .inputs // empty' reports/g02_necessity_refinement_v1.json 2>/dev/null | head -30
grep -o -E '"[a-z_]*p_sample[a-z_]*"|"condition[a-z_]*"' reports/g02_necessity_refinement_v1.json | sort | uniq -c | head
