# Seed-3 Remaining-Arms an29 Queue V1

Status:
- Implementation complete, tested, committed, and launched as `experiments/runs/pilot_seed3_remaining_an29_queue_login_20260722T160247Z`.
- The queue adopts the exact running seed-3 A1 and A2 records. It may launch only A2b followed by A3, and only on `an29` GPUs 0-3.
- This is operational scheduling. It opens no performance values and makes no scientific gate decision.

Evidence:
- Scheduler: `scripts/run_pilot_seed3_queue_v2.py`.
- Dedicated launcher: `scripts/launch_pilot_seed3_remaining_an29.sh`.
- Fixtures: `tests/test_pilot_seed3_queue_v2.py`.
- Verification: 35 tests pass across multi-adoption, launch authorization, checkpoint watchers, and resume-watcher contracts.
- Adopted A1: `experiments/runs/mech_a1_real_seed3_an29_20260722T050330Z` plus `experiments/runs/pilot_checkpoint_watch_mech_a1_real_seed3_login_20260722T050427Z`.
- Adopted A2: `experiments/runs/mech_a2_gray_seed3_an12_20260722T145916Z` plus `experiments/runs/pilot_checkpoint_watch_mech_a2_gray_seed3_login_20260722T150017Z`.
- Independent M5 reservation: `experiments/runs/m5_after_seed3_a2_lifecycle_login_20260722T154457Z`, fixed to `an12:0-3`.
- Launch commit: `95aa293`.
- Initial machine state: A1/A2 adopted, `launch_nodes=[an29]`, `reserved_training_nodes=[an12,an29]`, A2b/A3 pending, and `performance_values_opened=false`.
- No A2b or A3 training directory existed after launch. The independent M5 lifecycle contract hash remained unchanged.

Problems:
- Retiring the superseded v5 outer scheduler removed the unsafe an12 race but also removed automatic launch coverage for A2b/A3.
- A transiently empty GPU probe is not sufficient release evidence. A trainer may be finalizing its checkpoint, or a stale manifest may need diagnosis.

Decision:
- Extend the existing queue format to adopt multiple exact training/watcher records while preserving the old single-adoption CLI.
- Require each arm's training and watcher manifests to be complete, exit zero, and artifact-verified before marking the arm released. Step-100 merged-index, raw-relocation, and tracker evidence remain mandatory.
- Treat every node with an arm in `running` or `checkpoint_finalizing` state as reserved, even if `nvidia-smi` reports free GPUs.
- Restrict the new queue's launch-node set to exactly `an29`. It cannot launch on an12 and therefore cannot race M5.
- Preserve registered arm order: after A1 release, launch A2b; after A2b release, launch A3. The existing arm launcher supplies the exact config, TP1 four-replica placement, authorization check, host-memory preflight, and attached watcher.

Adversarial fixtures:
- A final checkpoint file set does not release an arm while its watcher still reports `running`.
- Duplicate adopted arms and any node outside the allowed set are rejected.
- A running/finalizing record reserves its node despite a free-GPU observation.
- Multi-adoption preserves `launch_nodes=[an29]` in machine state.
- The dedicated launcher is syntax-checked and contains the exact two-adoption/an29-only command.

Next actions:
- Keep the CPU-only queue waiting while A1/A2 continue; its initial adoption, reservation, and no-child checks pass.
- When A1 plus its watcher finish, verify two stable an29 capacity polls and the exact A2b launch record.
- Keep the M5 lifecycle and this queue independent; investigate rather than override any fail-closed condition.
