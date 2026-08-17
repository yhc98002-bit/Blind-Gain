#!/bin/bash
export PATH=$HOME/.local/bin:$PATH
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
echo "=== F8 readout md (head 120) ==="
head -120 reports/f8_mini_a5_endpoint_readout_v1.md
echo "=== R19 paired comparison primary numbers ==="
jq '{schema_version, primary: (.primary // .tasks // .per_task // empty)}' reports/mini_a5_f8_r19_paired_comparison_v1.json 2>/dev/null | head -60
