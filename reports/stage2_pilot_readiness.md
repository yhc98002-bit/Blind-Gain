# Stage 2 Pilot Readiness

Status:
- The three-arm mechanical pilot implementation and matched configs are prepared.
- The pilot is not cleared to launch because its P1.1 anchor dependency is still running.

Evidence:
- EasyR1 revision: `dd71bbd252694f5f850213eec15795b6b88d9fea`.
- Reproducible patch: `docs/easyr1_image_condition_patch.diff`.
- Patch installer: `scripts/apply_easyr1_image_condition_patch.sh`.
- Adversarial tests: `tests/test_easyr1_image_condition_patch.py`; all four pass.
- Matched-config test: `tests/test_mech_pilot_configs.py`; passes.
- Parser agreement audit: `reports/parser_agreement_audit.md`; P0.2 is complete with 320 recovered-checkpoint generations audited.
- Configs: `configs/train/mech_a1_real_3b_geo3k.yaml`, `configs/train/mech_a2_gray_3b_geo3k.yaml`, and `configs/train/mech_a2b_noimage_3b_geo3k.yaml`.
- All arms use seed 1, 100 steps, rollout batch 512, group size 5, actor global batch 128, full Geometry3K test validation, greedy validation every 10 steps, checkpoints every 20 steps, and `freeze_vision_tower: true`.
- Configs are byte-equivalent after parsing and removing only `data.image_condition`, `trainer.experiment_name`, and `trainer.save_checkpoint_path`.

Problems:
- P1.1 anchor `experiments/runs/anchor_a0_recipe_3b_geo3k_20260709T224852Z` has not completed.

Decision:
- Keep P2.1 prepared-only. Do not launch a long arm before the anchor supplies throughput and checkpoint evidence.
- Gray conditioning occurs after pixel-size normalization and the same conditioned PIL object reaches both the model processor and rollout `multi_modal_data`.
- No-image conditioning removes `<image>` from the rendered prompt, removes the image field, and emits no multimodal payload.

Next actions:
- Finalize and audit P1.1.
- Run one batch-level smoke for each arm on the compute-node environment.
- Launch the three immutable runs only after P1.1 completes and the anchor audit is incorporated.
