#!/bin/bash
export PATH=$HOME/.local/bin:$PATH
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
echo "=== F8 reports ==="
ls reports/ | grep -i -E 'f8|endpoint_readout|mini_a5' 
echo "=== F8 readout summary ==="
for f in reports/mini_a5_endpoint_readout_v1.json reports/f8_readout_v1.json; do
  [ -f "$f" ] && echo "--- $f ---" && jq 'if type=="object" then with_entries(if (.value|type)=="array" and (.value|length)>5 then .value=(.value[:3]) else . end) else . end' "$f" | head -60
done
echo "=== ledger F8 / gate1 lines ==="
grep -n -i -E 'f8|gate.?1|mini.a5' reports/main_progress.md | tail -40
echo "=== step0 reward audit structure ==="
jq 'keys' reports/mini_a5_step0_reward_audit_v1.json 2>/dev/null
jq '.per_item // .items // empty | length' reports/mini_a5_step0_reward_audit_v1.json 2>/dev/null
echo "=== blind solvability runs ==="
ls experiments/runs/ | grep -i -E 'blind_solv' | head -30
echo "=== blind solvability over mini_a5? ==="
ls experiments/runs/ | grep -i -E 'mini_a5' | head -20
echo "=== git log for mini_a5 configs ==="
git log --oneline --follow -- configs/train/mini_a5_cp_3b_v1.yaml | head -5
git log --oneline --follow -- configs/train/mini_a5_same_data_3b_v1.yaml | head -5
echo "=== search for a mini_a5 config build script ==="
grep -rl 'mini_a5_cp_3b_v1' scripts/ src/ tools/ 2>/dev/null | head
echo "=== cp_grpo_reward functions ==="
grep -n 'def ' src/rewards/cp_grpo_reward.py | head -20
echo "=== necessity / delta_q infra in src ==="
grep -rn -i -E 'delta_?q|necessity' src/ --include='*.py' -l | head -20
echo "=== generator ==="
ls src/fliptrack/ | grep -i -E 'mini_a5|build'
