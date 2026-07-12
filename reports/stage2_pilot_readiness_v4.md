# Four-Arm Pilot Readiness V4

Status:
- `not ready to launch`. Launch/retention plumbing is now implemented, but L3 and L12 remain blocked.
- No pilot-arm optimizer step has been taken, and this report does not declare a PI gate.
- V3 remains unchanged; V4 adds the completed launch-plumbing audit and engineering-anchor endpoint evaluation.

Evidence:
- Four matched configs: `configs/train/mech_a1_real_3b_geo3k.yaml`, `mech_a2_gray_3b_geo3k.yaml`, `mech_a2b_noimage_3b_geo3k.yaml`, and `mech_a3_caption_3b_geo3k.yaml`.
- Launch implementation and checks: `reports/pilot_launch_plumbing_v1.md`.
- L7 report/audit: `reports/blind_solvability_geo3k_v2.md` and `reports/blind_solvability_geo3k_v2_audited.json`; all 13 audit checks pass.
- Draft preregistration: `reports/preregistration_pilot_v1_DRAFT_20260712T0608Z.md`; final `reports/preregistration_pilot_v1.md` remains absent.
- Engineering-anchor endpoint: `reports/grpo_anchor_step100_prepost_v1.md`; test greedy pilot accuracy `0.1498 -> 0.4359`, paired delta `+0.2862` with 95% item-bootstrap CI `[+0.2446, +0.3278]`.
- Full repository suite before launch-plumbing changes: `447 passed`; focused new launch/guard suite: `21 passed`.

Registered mechanics:
- Four arms, seed 1, 100 steps, G=5, rollout batch 512, actor global batch 128, frozen vision tower, KL coefficient 0.01, greedy Geometry3K-test validation every 10 steps, and saves every 20 steps.
- Each arm runs on one node with four selected GPUs, TP1 serving, and no cross-node rollout/training disaggregation.
- Actual optimizer steps, tokens, and wall time will be reported per arm; no matched-FLOP claim is authorized.
- Save and retention behavior is hash-guarded as specified in `reports/pilot_launch_plumbing_v1.md`.

Throughput and cadence:
- Retain registered checkpoint cadence `K=20` and greedy validation cadence 10.
- The surviving anchor steps 81-100 imply approximately 42.7 hours per 100-step arm, around 171 arm-hours total and 683 four-GPU hours before evaluation/merge overhead.
- With two concurrent single-node arms, the lower-bound training wall time remains about 85 hours; placement may be staggered around foreign jobs and storage-save windows.

Problems:
- L3: the corrected TP1 replacement smoke is still active; historical TP2 evidence remains rejected.
- L12: the frozen R19 human contact-sheet audit and both PI signatures are still absent.
- The anchor endpoint is an engineering calibration only. Its native metric file lacks steps 1-80 and cannot substitute for pilot preregistration or run-to-run replication.
- Step-60 FlipTrack scoring must publish the checkpoint-bound completion marker before the watcher can sweep that merged checkpoint.

Decision:
- Keep all four arm launches fail-closed.
- Use `scripts/launch_mech_pilot_arm.sh` only after the final L12 file is merged and the per-arm authorization JSON says `authorized`.
- Preserve `K=20`, validation cadence 10, and matched configs; do not tune after inspecting pilot metrics.

Next actions:
- Complete and audit L3.
- Complete the human/PI L12 gate.
- After authorization, place each arm opportunistically on four free GPUs of one node and start its checkpoint watcher immediately after training startup.
