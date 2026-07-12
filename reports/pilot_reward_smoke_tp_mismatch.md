# Pilot Reward Smoke Placement Mismatch

Status:
- `fail`. The completed five-step reward smoke remains valid evidence that reward fields populated, but it is not valid evidence for the PI-set TP1 placement or for the current exact pilot configuration.
- L3 is returned to `blocked` until a replacement five-step TP1 smoke completes and receives a new versioned audit.

Evidence:
- Historical run: `experiments/runs/pilot_reward_smoke_an29_20260711T165700Z` on `an29` GPUs `1,5,6,7`.
- Frozen run git revision: `476c97ae7c3f9136e362c76c7186b0bb27fa9e2b`.
- Historical base-config SHA256 recorded by the run: `fd745ad80acc0f075f8ad451cb3baca31d07cbdbe10cf6f94a1b8679b83e8ffa`.
- At that git revision, `configs/train/mech_a1_real_3b_geo3k.yaml:77` sets `worker.rollout.tensor_parallel_size: 2`.
- The immutable stdout/stderr log at line 207 prints `"tensor_parallel_size": 2`.
- The run manifest incorrectly records `tensor_parallel_width: 1`, `replica_count: 1`, and a TP1 placement justification.
- Manifest SHA256: `9b6002b231654a37016d684dd8bc62c94237cfa09c1dc16c29d177bdef13c78e`.
- Log SHA256: `420f178ce4850f067a2ca33ce0e366a89bf2676ca5e766322e723fcd63bec107`.
- Historical audit SHA256: `ca08935b406a37a6c8603ba0e023797ced60e6dbe3032b675cfe6ce59593a1d0`.

Problems:
- The launcher hardcoded placement metadata instead of deriving it from the run config.
- TP2 across four GPUs implies two rollout replicas, not the manifest's claimed TP1/one-replica placement.
- The current pilot configs were subsequently changed to TP1, so the old smoke is not an exact-current-config plumbing run.
- This accounting error does not alter the preserved reward-shadow rows or their reward arithmetic, but it invalidates the placement claim and the L3 completion claim.

Decision:
- Preserve `reports/pilot_reward_spec_v2.md` and `reports/pilot_reward_smoke_audit_v3.json` as historical, superseded evidence; do not overwrite or rewrite their numbers.
- Derive tensor-parallel width and rollout replica count from an immutable per-run config snapshot before launch, refusing any width other than TP1.
- Record four TP1 rollout replicas for the four-GPU synchronous EasyR1 job while keeping training and rollout colocated on one node.
- Route the replacement smoke's unconditional final checkpoint to a run-specific `checkpoints/smoke/<run_id>` namespace and checksum-delete it after successful audit.
- Do not advance L12 or L13 on the basis of the historical smoke.

Next actions:
- Run the adversarial TP2 rejection fixture and launcher tests.
- Launch one replacement five-step smoke on four free GPUs after the active L9 job releases its allocation.
- Publish a versioned reward specification and smoke audit only after the replacement run and checkpoint cleanup complete.
