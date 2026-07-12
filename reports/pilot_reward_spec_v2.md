# Pilot Reward Specification

Status:
- Complete. The custom pilot reward passed the exact five-step plumbing smoke and shadow audit.
- Machine status JSON: `reports/pilot_reward_smoke_audit_v3.json`.
- The native anchor reward path remains separate; this reward is bound only by pilot-arm configs.

Evidence:
- Smoke run: `pilot_reward_smoke_an29_20260711T165700Z` on `an29` GPUs `1,5,6,7`.
- Git/config/data hashes: `476c97ae7c3f9136e362c76c7186b0bb27fa9e2b` / `66e75b45156d599f781eeffb6e7b1b8ad2baad7bb9b5f1a70332a9fbc6725058` / `f3d88dd1e52ccef833f266880e487eef252193f774c1076f7dfbccd180b450e6`.
- Exact training shadow rows: `12800` = 5 steps x 512 rollout prompts x group size 5.
- Exact final-validation shadow rows: `601`, matching the frozen Geometry3K test answers in sequence.
- Training-partition reward counts: `{'0.0': 4338, '0.5': 7723, '1.0': 739}`.
- Training-partition disagreement reason counts: `{'canonical_correct_mathruler_incorrect': 179, 'mathruler_correct_canonical_incorrect': 74, 'none': 12547}`.
- Validation-partition reward counts: `{'0.0': 39, '0.5': 440, '1.0': 122}`.
- All shadow values are finite; every training-reward identity recomputes exactly; parser/reward versions are canonical-v2/pilot-reward-v1.
- Every row pins symbolic-grader guard `posix-itimer-v1` with a 5.0-second timeout; native shadows are valid on all rows.
- Symbolic timeout counts: `{}`.
- Image-grid regression evidence: `reports/easyr1_image_grid_audit_v1.md` (0/1,288 mismatches after the payload fix).

Reward contract:
1. Extract the final answer span with canonical-v2.
2. Grade that extracted span with mathruler.
3. Compute `contract_valid` independently from exact `<answer>...</answer>` compliance.
4. Set accuracy weight to 0.5 and format weight to 0.5, matching the reference recipe split.
5. Precedence rule: if mathruler and canonical numeric-equivalence disagree, mathruler's verdict is the reward and the disagreement is logged with a reason code.
6. Log `training_reward`, `native_r1v_shadow_reward`, `canonical_eval_reward`, and `reward_disagreement_reason` per rollout.
7. Bound both MathRuler grading and the native-r1v shadow with POSIX `ITIMER_REAL` at 5.0 seconds; a native-shadow failure is logged and cannot change the optimized reward.

Problems:
- The first full-path smoke exposed double-resized visual-grid drift before optimizer step 1. That run remains preserved in `reports/pilot_reward_smoke_failure_20260711.md`; the repaired run is the evidence above.
- EasyR1 always performs a final validation pass and calls the same reward function. The failed v1 audit expected only training rows; v2 partitions the append-only shadow log using the exact 601-row test-answer sequence.
- An unbounded symbolic grader later stalled L7 no-image scoring. The guarded replacement smoke recorded zero guard mismatches and zero invalid native shadows; finite-call reward semantics remain unchanged.
- A five-step smoke certifies reward plumbing and nondegeneracy, not training stability or scientific efficacy.

Decision:
- Pin `pilot-reward-v1`, canonical-v2, mathruler precedence, and the 0.5/0.5 split for L7 and all four pilot arms.
- Keep the anchor config bound to EasyR1 native `r1v.py`; do not retroactively rescore or modify anchor optimization.

Next actions:
- Run the five-condition L7 audit under this exact reward and fill preregistration quantities only from its audited outputs.
