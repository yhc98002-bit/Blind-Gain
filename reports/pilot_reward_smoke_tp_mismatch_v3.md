# Pilot Reward Smoke Placement Mismatch V3

Status:
- `fail`. The historical five-step smoke remains superseded and L3 remains `blocked`.
- A replacement smoke must pass audit schema `blind-gains.pilot-reward-smoke-audit.v6` before L3 can be reconsidered.

Evidence:
- Historical machine re-audit: `reports/pilot_reward_smoke_historical_reaudit_v6.json`, SHA256 `05964b490fe523762e39cfea90acba39b3ac365866389628aa1d0b7a5c1cc8ae`, `status=fail`.
- Reward arithmetic, row partitions, and training-step checks still pass; placement/provenance fails independently.
- V6 retains the TP/config failures from V5 and additionally rejects absent immutable EasyR1 revision, worktree-patch, and logger snapshots.
- The current launcher snapshots `effective_config.yaml`, `easyr1_worktree.patch`, and `easyr1_logger.py` inside the run directory and records each hash.
- The current patched EasyR1 logger SHA256 is `a96854c3a84e94c9397413c73e0dd69854871bf28f22c4523a920b6b197e8912`; the full EasyR1 worktree-diff SHA256 is `2d96ccfdd3b15b747525661d7576a6c6b080f9465395f721c0fd846d4400f4f8`.
- The resume-safe logger patch is applied against EasyR1 revision `dd71bbd252694f5f850213eec15795b6b88d9fea` and a live sentinel fixture confirms explicit resume initialization preserves existing logs.
- Focused reward, placement, cleanup, and logger tests: 38 passed.

Problems:
- The historical run cannot retroactively acquire immutable stack snapshots.
- The replacement run still awaits a four-GPU window; no reduced-width substitute is accepted.

Decision:
- Preserve V3/V5 audits and V1/V2 mismatch reports as versioned historical evidence.
- Require TP1, four derived rollout replicas, run-local config and EasyR1 snapshots, runtime-log TP confirmation, and the isolated smoke checkpoint namespace in V6.
- Require a passing V6 audit before checksum-deleting the unavoidable step-5 checkpoint.
- Do not advance L12 or L13 from the historical smoke.

Next actions:
- Launch the replacement smoke on `an29` GPUs `1,5,6,7` after the active 72B caption job exits and its ephemeral weights are deleted.
