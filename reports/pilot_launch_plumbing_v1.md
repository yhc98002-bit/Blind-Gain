# Four-Arm Pilot Launch Plumbing V1

Status:
- Implementation complete and test-audited; no pilot optimizer step was launched.
- Runtime authorization remains `blocked` by L3 and L12. This report is not a PI gate verdict.

Evidence:
- Git commit: `388f032`.
- Arm launcher: `scripts/launch_mech_pilot_arm.sh`, SHA256 `165fe44f5b9ca3fac19f4e0197a9604533ab021283cb8624d0b914994f74b5b7`.
- Watcher launcher: `scripts/launch_pilot_checkpoint_watch.sh`, SHA256 `8987443ea41239b04294052d4db7ad3a0a8002b28736faf7eb4ede2921d11748`.
- Pilot watcher: `scripts/watch_pilot_checkpoints.py`, SHA256 `cd428173072e6cb53416c2a704992437d48e9f70c4321176fadcba51d6f5bd11`.
- Shared checkpoint machinery: `scripts/watch_anchor_checkpoints.py`, SHA256 `52cf241f26bb7329e59e47ae34ce0842b8bc243254dd9b407262057f9b4f698b`.
- Authorization checker: `scripts/check_pilot_launch_authorization.py`, SHA256 `944e07e34420812e89b9b5a5eed639fa4d8713fcf9a1d0d4b76279f834ee80ca`.
- Focused launch/authorization/config/checkpoint-guard suite: `21 passed`.
- Watcher and relocation suites: `26 passed`; watcher-only follow-up: `15 passed`.
- Repository suite before this implementation: `447 passed`; no failure was present.

Launch contract:
- Accepted arm keys are `a1_real`, `a2_gray`, `a2b_noimage`, and `a3_caption`.
- Every job is one synchronous EasyR1/GRPO process on exactly one of `an12` or `an29`, four selected GPUs, TP1, with four TP1 rollout replicas.
- `scripts/check_pilot_launch_authorization.py` is executed before run-directory creation, checkpoint creation, SSH, or GPU use.
- Authorization requires L3/L4/L5/L12 ledger pass, a final preregistration with exact human and two-PI approvals, a passing L3 v6 smoke audit, reward spec v3, pinned config/data hashes, and an absent selected checkpoint namespace.
- The launcher additionally requires `reports/preregistration_pilot_v1.md` to be tracked and byte-identical to `HEAD` and refuses dirty critical launch/config/reward/guard files.
- The immutable run directory snapshots the effective config, merged preregistration, EasyR1 worktree diff, resume-safe logger, and checkpoint-guard trainer implementation with hashes.
- A3 manifests additionally pin the 3B caption model, caption prompt hash, canonical caption-store hash, and caption-store file-bundle hash.

Storage and retention:
- Saves go to `checkpoints/pilot/<arm>` on shared storage.
- Every EasyR1 save invokes the quota-aware Tier-S guard with a 55,000,000,000-byte reservation and 20 GiB floor. A refusal waits 300 seconds and retries; there is no save semaphore.
- Checkpoints 20/40/60/80/100 are merged and hash-verified. Raw state is moved to login-node `/tmp`, with only the newest raw state retained after the next verified merge.
- Merged checkpoints 20/40/60/80 move to the login-node archive. Step 100 remains on shared storage.
- Step 60 is not swept until `step60_fliptrack_complete.json` binds a completed evaluation run/output hash to the exact merged checkpoint-index SHA256.

Problems:
- The current authorization artifact remains blocked because L3 replacement evidence and final L12 approval do not yet exist.
- The step-60 marker consumer is implemented; the future scoring job must still create that marker only after its registered FlipTrack output is complete and hashed.
- A launcher test proves fail-closed ordering, but no production launch dry run can cross authorization before L12 by design.

Decision:
- Keep L13 blocked. The implementation is ready for code review, not execution.
- Do not add an override flag for preregistration, approval, checkpoint namespace, or storage guard failures.

Next actions:
- Close L3 from the active corrected five-step smoke if and only if its v6 audit passes.
- Obtain the independent R19 human audit and both PI approvals, then merge the final L12 file.
- Re-run the authorization check for each arm immediately before placement and launch.
