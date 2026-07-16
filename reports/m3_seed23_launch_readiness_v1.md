# M3 Seed 2-3 Launch Readiness V1

Status:
- Registration and immutable configs are prepared; no seed-2 or seed-3 optimizer step has run.
- This report does not mark M3 complete and makes no PI scientific gate decision.

Evidence:
- Registration: `docs/registered_pilot_seed23_v1.md`.
- Eight follow-up configs are hash-pinned in the registration.
- Mechanical config audit permits exactly three changes from seed 1: `data.seed`, `trainer.experiment_name`, and `trainer.save_checkpoint_path`.
- The fixed intervention seed remains `20260710` in all eight configs.
- Adversarial tests reject an unregistered seed and a hidden reward change.

Problems:
- Seed 2 needs one stable four-GPU single-node placement that does not colocate a second EasyR1 trainer on the same host.
- M5 has concurrent first priority under R5; foreign processes are not preempted.

Decision:
- Queue seed-2 arms in fixed order A1, A2, A2b, A3. Run at most one pilot trainer per node.
- Keep seed 3 registered but do not schedule it ahead of M11 and M6 readiness work.

Next actions:
- Commit the registration, configs, authorization check, launcher, and queue before launching seed 2.
- Bind every run manifest to the selected config and registration hashes.
