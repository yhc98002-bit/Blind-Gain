# Four-Arm Pilot Launch Plumbing V2

Status:
- Implementation complete and test-audited; no pilot optimizer step was launched.
- Runtime authorization remains blocked by L3 and L12. This report is not a PI gate verdict.
- V2 preserves V1 and adds the checkpoint-bound evaluation-marker producer required to release step 60 from shared storage.

Evidence:
- Base launch/retention implementation: `reports/pilot_launch_plumbing_v1.md` at Git commit `388f032`.
- Marker producer: `scripts/finalize_pilot_step_evaluation.py`, SHA256 `e8f3cf5ba7fd3c8a900a4e1327ce96de49074d9c02317d26d16c86742622d9e6`, Git commit `ea71e5d`.
- Marker/watcher focused suite: `6 passed`; broader launch/guard suite remains `21 passed`.
- Production blocked probe: `reports/pilot_launch_blocked_probe_v1.md`; no run directory, checkpoint namespace, SSH, or GPU contact occurred.

Step-60 release contract:
- The marker producer accepts only registered steps 60 or 100.
- Evaluation must be complete, real-image R19, greedy (`temperature=0`, `top_p=1`, `n=1`), 32 output tokens, and use prompt-contract SHA256 `7ac39f53a2a824490fc5ee22671a888d2d79d55e1d8351919006d7d71c7a8f3f`.
- The evaluation model path must resolve to the exact merged checkpoint and its manifest must name the same global step.
- The aggregate must be complete, point to that exact evaluation run, and cover 1,200 pairs.
- The emitted marker hashes the checkpoint index, evaluation manifest, aggregate manifest, and aggregate metrics. Any later checkpoint-index change invalidates the watcher check.
- The watcher relocates the step-60 merged checkpoint only after this marker validates; raw-state relocation can proceed earlier under latest-raw retention.

Problems:
- A dedicated pilot checkpoint R19 scoring launcher is still prepared only through the generic sharded evaluator; it must stamp the fields above before marker finalization.
- L3 and L12 remain real blockers, so the authorized training/evaluation path cannot be exercised in production yet.

Decision:
- Keep L13 blocked and retain the marker contract without bypass flags.
- Treat a missing or malformed marker as a reason to retain step 60 on shared storage, never as permission to sweep it.

Next actions:
- Close L3 if its replacement audit passes.
- Merge L12 only after the human R19 review and both PI approvals.
- At an authorized run’s step 60, launch the fixed R19 evaluator, aggregate all 1,200 pairs, then create the marker before the watcher sweep.
