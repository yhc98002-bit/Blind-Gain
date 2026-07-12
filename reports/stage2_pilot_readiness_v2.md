# Four-Arm Pilot Readiness V2

Status:
- `prepared, not authorized`. Four matched 3B configs exist for A1 real, A2 gray, A2b no-image, and A3 fixed question-blind captions.
- L13 remains blocked by the unfinished L7 artifact, the R19 human contact-sheet audit, and merged two-PI L12 preregistration.
- No pilot-arm optimizer step has been taken.

Evidence:
- Configs: `configs/train/mech_a1_real_3b_geo3k.yaml`, `configs/train/mech_a2_gray_3b_geo3k.yaml`, `configs/train/mech_a2b_noimage_3b_geo3k.yaml`, and `configs/train/mech_a3_caption_3b_geo3k.yaml`.
- The parsed configs are identical after removing only `data.image_condition`, `trainer.experiment_name`, and `trainer.save_checkpoint_path`.
- Every arm uses seed 1, 100 steps, rollout group size 5, rollout batch 512, actor global batch 128, frozen vision tower, KL coefficient 0.01, greedy validation every 10 steps, and checkpoints every 20 steps.
- Every 3B rollout now uses TP1 under the PI placement rule; each synchronous EasyR1 arm remains wholly on one four-GPU node.
- Custom reward: canonical-v2 extraction, MathRuler precedence, 0.5 accuracy/0.5 format split, and `posix-itimer-v1` bounded at 5.0 seconds.
- Caption store: three fixed 3B question-blind shards with 100% filtered-corpus coverage, recorded in each config.
- Anchor engineering recovery is complete in `reports/anchor_step100_oom_recovery_v2.md`.
- Matched-config and image-condition fixtures: `tests/test_mech_pilot_configs.py` and `tests/test_easyr1_image_condition_patch.py`.

Problems:
- The prior configs used TP2 for a 3B model, contrary to the PI's 2026-07-11 placement rule. V2 changes all four arms to TP1 and tests the invariant.
- The launch/finalizer implementation still must bind the merged L12 hash and refuse any optimizer step before that artifact exists.
- One seed estimates pilot direction only and cannot quantify run-to-run RL variance.

Decision:
- Keep all behavior-changing fields matched across arms except the registered image condition and immutable run/checkpoint identity.
- Report matched optimizer budget plus actual tokens and wall-clock; make no FLOP-equality claim.
- Do not launch L13 from this readiness report.

Next actions:
- Complete and audit L7, fill the fixed preregistration fields, obtain the R19 human audit and two PI approvals, then merge L12.
- Implement the L13 launcher with a hard preregistration hash check and the shared-save/login-sweep retention path before scheduling any arm.
