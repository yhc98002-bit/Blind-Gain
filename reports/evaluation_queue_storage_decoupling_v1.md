# Evaluation Queue Storage Decoupling V1

Status:
- Implemented under PI ruling R3.
- Pilot step-100 R19 evaluation readiness now depends on the exact completed
  training run and a structurally complete merged checkpoint. Archive
  relocation status is recorded only as operational context.

Evidence:
- Implementation: `scripts/run_pilot_step100_eval_queue.py`, SHA256
  `ab44a3fc7d22de568b949c02735481d7631c53fc339f2d12f1afbd6165628962`.
- Adversarial fixture: `tests/test_pilot_step100_eval_queue.py`, SHA256
  `4ca54c92f1046059f8af6773bd153ed863aa9e49fe00f7d5d42b6bb586acc3ca`.
- Focused queue suites: 17 tests passed.
- The new checkpoint check requires a valid nonempty safetensors weight map and
  every referenced shard to be present and nonempty.

Problems:
- Historical A2 queues remain immutable failures. They are not rewritten or
  reused; recovery uses new run identities.

Decision:
- A failed or running archive relocation no longer blocks a complete merged
  checkpoint. A missing/partial merge remains fail-closed as
  `waiting_checkpoint`.
- The old implementation fails the new adversarial fixture because it returns
  `retention_terminal_failed` despite a complete checkpoint.

Next actions:
- Launch the fresh A2 R19 queue only after the step-100 safetensors index and all
  referenced shards pass this readiness check.
