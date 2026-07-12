# Four-Arm Pilot Readiness V3

Status:
- `not ready to launch`. The four matched configs and preregistration inputs exist, but L3 and L12 remain blocked.
- L7 is now complete with audited five-condition outputs; this removes the stale L7 blocker stated in V2.
- No pilot-arm optimizer step has been taken.

Evidence:
- Configs: `configs/train/mech_a1_real_3b_geo3k.yaml`, `configs/train/mech_a2_gray_3b_geo3k.yaml`, `configs/train/mech_a2b_noimage_3b_geo3k.yaml`, and `configs/train/mech_a3_caption_3b_geo3k.yaml`.
- The configs are structurally identical after removing only registered arm identity: `data.image_condition`, `trainer.experiment_name`, and `trainer.save_checkpoint_path`.
- Shared contract: seed 1, 100 steps, G=5, rollout batch 512, actor global batch 128, frozen vision tower, KL coefficient 0.01, greedy validation every 10 steps, checkpoint save every 20 steps, and four GPUs on one node.
- Qwen2.5-VL-3B rollout serving is TP1; one synchronous EasyR1 job remains colocated with four rollout replicas.
- L7 report/audit: `reports/blind_solvability_geo3k_v2.md` and `reports/blind_solvability_geo3k_v2_audited.json`, all 13 checks true.
- Draft preregistration: `reports/preregistration_pilot_v1_DRAFT_20260712T0608Z.md`; the final L12 path remains absent.
- Stack: `reports/training_stack_decision_v2.md`; every run must snapshot the current EasyR1 diff and logger.
- Full repository test suite: 435 passed.

Throughput and cadence:
- The only surviving continuous anchor segment covers steps 81–100. Its 20 training steps average 1,537.36 seconds and have median 1,513.93 seconds per step, including validation/save overhead on cadence steps.
- Mean processed tokens in that segment are 1,948,828 per step.
- Provisional estimate: about 42.7 hours per 100-step arm, approximately 171 arm-hours and 683 four-GPU hours for all four arms before evaluation/merge overhead.
- With two arms running concurrently on separate nodes, the lower-bound training wall time is about 85 hours; actual placement may be staggered around L9/L10 and foreign jobs.
- Registered checkpoint cadence `K=20`; registered Geometry3K greedy validation cadence remains 10 steps.
- These are wall-clock/token estimates. No FLOP-equality claim is made.

Problems:
- L3: the historical smoke used TP2 while claiming TP1. The v6 auditor rejects it; a replacement five-step TP1 smoke is pending.
- L12: human R19 contact-sheet review and both PI signatures are pending.
- The L13 launcher/checkpoint watcher must still bind the final preregistration hash, refuse a first optimizer step unless ledger dependencies pass, and implement shared-save to login-archive retention.
- The anchor's structured metric file was truncated on resume, so throughput calibration uses only the audited surviving 81–100 segment; this limitation is documented in `reports/anchor_metric_continuity_audit_v1.md`.
- One seed estimates pilot direction only and cannot quantify run-to-run RL variance.

Decision:
- Retain `K=20` for checkpoint saves and 10-step greedy validation.
- Keep all behavior-changing fields matched across arms except the registered image condition and immutable run/checkpoint identity.
- Report actual tokens, optimizer steps, and wall-clock by arm; do not claim matched FLOPs.
- Do not launch L13 from this readiness report.

Next actions:
- Complete the replacement L3 TP1 smoke and publish a passing v6 audit/reward spec.
- Complete the human R19 audit and obtain both PI signatures on the final L12 document.
- Implement and adversarially test the L13 preregistration-hash launcher and retention watcher before scheduling an arm.
