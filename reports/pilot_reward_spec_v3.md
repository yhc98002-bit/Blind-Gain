# Pilot Reward Specification

Status:
- Complete. The custom pilot reward passed the exact five-step plumbing smoke and shadow audit.
- Machine status JSON: `reports/pilot_reward_smoke_audit_v4.json`.
- The native anchor reward path remains separate; this reward is bound only by pilot-arm configs.

Evidence:
- Smoke run: `pilot_reward_smoke_an29_20260712T075418Z` on `an29` GPUs `1,5,6,7`.
- Git/config/data hashes: `e5dde9d7bafd472720d6c1bb8afd727da28f7c29` / `05471729b1d8b6925513c3654b06fa8d3ed88e65c9bf3d3aa0f68c1f39321ec9` / `f3d88dd1e52ccef833f266880e487eef252193f774c1076f7dfbccd180b450e6`.
- Placement: TP`1` with `4` rollout replicas; runtime log values `[1]`.
- EasyR1 revision: `dd71bbd252694f5f850213eec15795b6b88d9fea`; worktree patch SHA256 `2d96ccfdd3b15b747525661d7576a6c6b080f9465395f721c0fd846d4400f4f8`; logger SHA256 `a96854c3a84e94c9397413c73e0dd69854871bf28f22c4523a920b6b197e8912`.
- Native weight evidence: `artifacts/repos/EasyR1/examples/reward_function/r1v.py`, SHA256 `694c4197e8dd5088732b702dc4796f80a10319a9abfc125d2bc3c024aa097c5b`, at EasyR1 revision `dd71bbd252694f5f850213eec15795b6b88d9fea`.
- Exact native lines 45 and 49:
```python
def compute_score(reward_input: dict[str, Any], format_weight: float = 0.5) -> dict[str, float]:
        "overall": (1 - format_weight) * accuracy_score + format_weight * format_score,
```
- The resolved launched-anchor config `checkpoints/anchor_a0_recipe_3b_geo3k/anchor_a0_recipe_3b_geo3k_20260709T224852Z/experiment_config.json` (SHA256 `fdbc29d475c23afce00f9cfa8ffd3a7a894e72a7be5027245ba9c161c61bbcaa`) records `worker.reward.reward_function_kwargs={}`, so the native default is not overridden.
- Therefore native r1v uses accuracy weight `1 - 0.5 = 0.5` and format weight `0.5`. The pilot's registered 0.5/0.5 split matches native; no PI weight disposition is required.
- Exact training shadow rows: `12800` = 5 steps x 512 rollout prompts x group size 5.
- Exact final-validation shadow rows: `601`, matching the frozen Geometry3K test answers in sequence.
- Training-partition reward counts: `{'0.0': 4402, '0.5': 7627, '1.0': 771}`.
- Training-partition disagreement reason counts: `{'canonical_correct_mathruler_incorrect': 173, 'mathruler_correct_canonical_incorrect': 72, 'none': 12555}`.
- Validation-partition reward counts: `{'0.0': 52, '0.5': 426, '1.0': 123}`.
- All shadow values are finite; every training-reward identity recomputes exactly; parser/reward versions are canonical-v2/pilot-reward-v1.
- Every row pins symbolic-grader guard `posix-itimer-v1` with a 5.0-second timeout; native shadows are valid on all rows.
- Symbolic timeout counts: `{}`.
- Image-grid regression evidence: `reports/easyr1_image_grid_audit_v1.md` (0/1,288 mismatches after the payload fix).

Reward contract:
1. Extract the final answer span with canonical-v2.
2. Grade that extracted span with mathruler.
3. Compute `contract_valid` independently from exact `<answer>...</answer>` compliance.
4. Set accuracy weight to 0.5 and format weight to 0.5, exactly matching the quoted native r1v default and composition.
5. Precedence rule: if mathruler and canonical numeric-equivalence disagree, mathruler's verdict is the reward and the disagreement is logged with a reason code.
6. Log `training_reward`, `native_r1v_shadow_reward`, `canonical_eval_reward`, and `reward_disagreement_reason` per rollout.
7. Bound both MathRuler grading and the native-r1v shadow with POSIX `ITIMER_REAL` at 5.0 seconds; a native-shadow failure is logged and cannot change the optimized reward.

Problems:
- The first full-path smoke exposed double-resized visual-grid drift before optimizer step 1. That run remains preserved in `reports/pilot_reward_smoke_failure_20260711.md`; the repaired run is the evidence above.
- EasyR1 always performs a final validation pass and calls the same reward function. The failed v1 audit expected only training rows; v2 partitions the append-only shadow log using the exact 601-row test-answer sequence.
- An unbounded symbolic grader later stalled L7 no-image scoring. The guarded replacement smoke recorded zero guard mismatches and zero invalid native shadows; finite-call reward semantics remain unchanged.
- The historical five-step smoke used TP2 while its manifest claimed TP1. It remains preserved and rejected by `reports/pilot_reward_smoke_historical_reaudit_v6.json`; only the replacement run is completion evidence.
- A five-step smoke certifies reward plumbing and nondegeneracy, not training stability or scientific efficacy.

Decision:
- Pin `pilot-reward-v1`, canonical-v2, mathruler precedence, and the 0.5/0.5 split for L7 and all four pilot arms.
- Keep the anchor config bound to EasyR1 native `r1v.py`; do not retroactively rescore or modify anchor optimization.

Next actions:
- Keep L13 blocked until the draft preregistration receives the separate human R19 audit and both PI signatures.
