# Pilot Reward Specification

Status:
- Complete. The custom pilot reward passed the exact five-step plumbing smoke and shadow audit.
- Machine status JSON: `reports/pilot_reward_smoke_audit_v2.json`.
- The native anchor reward path remains separate; this reward is bound only by pilot-arm configs.

Evidence:
- Smoke run: `pilot_reward_smoke_an29_20260711T114247Z` on `an29` GPUs `1,5,6,7`.
- Git/config/data hashes: `5b141c0ba7527b4c03745e6b79d3ccdc1890174d` / `41dc4c7281329207a6949eb9f92b8a21631fbf81bdc2de73f6d0f3469713b6f9` / `f3d88dd1e52ccef833f266880e487eef252193f774c1076f7dfbccd180b450e6`.
- Exact training shadow rows: `12800` = 5 steps x 512 rollout prompts x group size 5.
- Exact final-validation shadow rows: `601`, matching the frozen Geometry3K test answers in sequence.
- Training-partition reward counts: `{'0.0': 4407, '0.5': 7611, '1.0': 782}`.
- Training-partition disagreement reason counts: `{'canonical_correct_mathruler_incorrect': 159, 'mathruler_correct_canonical_incorrect': 82, 'none': 12559}`.
- Validation-partition reward counts: `{'0.0': 39, '0.5': 430, '1.0': 132}`.
- All shadow values are finite; every training-reward identity recomputes exactly; parser/reward versions are canonical-v2/pilot-reward-v1.
- Image-grid regression evidence: `reports/easyr1_image_grid_audit_v1.md` (0/1,288 mismatches after the payload fix).

Reward contract:
1. Extract the final answer span with canonical-v2.
2. Grade that extracted span with mathruler.
3. Compute `contract_valid` independently from exact `<answer>...</answer>` compliance.
4. Set accuracy weight to 0.5 and format weight to 0.5, matching the reference recipe split.
5. Precedence rule: if mathruler and canonical numeric-equivalence disagree, mathruler's verdict is the reward and the disagreement is logged with a reason code.
6. Log `training_reward`, `native_r1v_shadow_reward`, `canonical_eval_reward`, and `reward_disagreement_reason` per rollout.

Problems:
- The first full-path smoke exposed double-resized visual-grid drift before optimizer step 1. That run remains preserved in `reports/pilot_reward_smoke_failure_20260711.md`; the repaired run is the evidence above.
- EasyR1 always performs a final validation pass and calls the same reward function. The failed v1 audit expected only training rows; v2 partitions the append-only shadow log using the exact 601-row test-answer sequence.
- A five-step smoke certifies reward plumbing and nondegeneracy, not training stability or scientific efficacy.

Decision:
- Pin `pilot-reward-v1`, canonical-v2, mathruler precedence, and the 0.5/0.5 split for L7 and all four pilot arms.
- Keep the anchor config bound to EasyR1 native `r1v.py`; do not retroactively rescore or modify anchor optimization.

Next actions:
- Run the five-condition L7 audit under this exact reward and fill preregistration quantities only from its audited outputs.
