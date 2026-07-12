# Blind Gains Prelaunch Execution Update - 2026-07-12 10:22 UTC

Status:
- The mechanical L3 reward-plumbing task is complete and recorded `pass`; this is not a PI scientific or compute-gate declaration.
- No four-arm pilot optimizer step has run. L12 remains blocked on the human R19 contact-sheet audit and signatures from both PIs, so L13 remains fail-closed.
- L10 is active on an12 GPUs0-4. Step-100 Geometry3K blind-condition evaluation is active on an12 GPUs6-7 and an29 GPUs1/5.
- Branch `agent/gate2-recovery` is synchronized to GitHub at commit `c84623b4770dc21e1f40369339c3ed67041169e3`.

Evidence:

## Task ledger

| Task | State | Current evidence or blocker |
| --- | --- | --- |
| L0 | pass | Shared-save to login-archive dry cycle and storage guards passed; `reports/storage_preflight.md` |
| L1 | pass | canonical-v2 fixtures pass; agreement remains 0.915625 and below the 0.95 PI-review threshold |
| L2 | pass | extractor-valid/contract-valid split and strict-gain identity audited |
| L3 | pass | Five-step TP1/4-replica smoke, exact 13,401-row v6 audit, and hash-before-delete cleanup complete |
| L4 | pass | Frozen 3B caption store has 100% filtered-corpus coverage; caption batches carry no image payload |
| L5 | pass | Precision filter frozen at 1,288/2,101 training rows; ID SHA256 `8631d015ee8593669b46cc707b9fe1fb3690391520bccf416b64bbb2306ff7d1` |
| L6 | pass | Consistency auditor and non-gating GPU-hours reporting complete |
| L7 | pass | Five-condition Geometry3K v2 base audit complete; 1,889 rows per condition and zero rescore mismatches |
| L8 | pass | R20 one-shot 1,200-pair run complete; document passes, geometry/chart remain R19-selected |
| L9 | pass | 72B caption stress complete; 146,833,336,607 ephemeral weight bytes hash-deleted |
| L10 | blocked | MathVerse/MMMU complete; five ViRL39K 4,096-item conditions are still running |
| L11 | pass | One-shot document calibration complete; 7B real saturation recorded without iteration |
| L12 | blocked | Draft exists; human R19 audit and both PI signatures are absent |
| L13 | blocked | Launch plumbing passes, but final merged L12 does not exist; no optimizer step authorized |

## L3 closure

- Run: `experiments/runs/pilot_reward_smoke_an29_20260712T075418Z`.
- Placement: an29 GPUs `1,5,6,7`, one node, TP1, four rollout replicas; runtime tensor-parallel values were exactly `[1]`.
- Training contract: 5 optimizer steps, 12,800 training shadow rows plus 601 final-validation rows in the exact registered answer order.
- Reward values: 4,454 rows at 0.0, 8,053 at 0.5, and 894 at 1.0; all finite and nondegenerate.
- Disagreements: 187 canonical-correct/mathruler-incorrect and 74 mathruler-correct/canonical-incorrect; the registered mathruler precedence was applied and logged.
- All training-reward identities recompute exactly; native shadows are valid on all rows; no symbolic timeouts, traceback, NaN, or image-grid mismatch occurred.
- Audit: `reports/pilot_reward_smoke_audit_v4.json`, SHA256 `125c11f06a62e6777bb48ad251236ac4193a5120725c9a1483278943d80cf931`.
- Specification: `reports/pilot_reward_spec_v3.md`, SHA256 `12f1b1b22f6a3599defce8f6b5ca4c926e6cba29bc82512178e43993be4833c2`.
- The pre-save guard projected 80,071,206,912 bytes of quota headroom after a conservative 55 GB save allowance, above the 20 GiB floor.
- The retention-expired checkpoint contained 28 files / 40,970,272,505 bytes. It was hash-listed, reverified, and deleted at `2026-07-12T10:10:48Z`; the path is absent.
- Cleanup run: `experiments/runs/pilot_reward_smoke_checkpoint_cleanup_login_20260712T100831Z`.
- Objective audit: `reports/prelaunch_objective_audit_20260712T101316Z`, all six checks true, SHA256 `ae42ee46d7c5a655094070b098aa62c7160c062839866ce890497eb0c592189a`.

## Engineering anchor results

- Geometry3K test, base to step 100: pilot-reward greedy accuracy 0.1498 to 0.4359, paired delta +0.2862, 95% item-bootstrap CI [+0.2446, +0.3278].
- R19 real-image pair accuracy, base to step 100: 0.5617 to 0.5633, paired delta +0.0017, 95% CI [-0.0183, +0.0209].
- At step 100, gray and noise pair accuracy are both 0.0000/1,200 with Collapse Rate 1.0000; real-image pair accuracy is 0.5633 with Collapse Rate 0.0833.
- The real-minus-gray and real-minus-noise paired deltas are both +0.5633, 95% CI [+0.5358, +0.5917].
- These are one-run engineering calibration endpoints on an R19-selected instrument. They show test-time pixel dependence, not that GRPO increased visual dependence.
- Report: `reports/anchor_step100_fliptrack_r19_blind_ablation_v2.md`; machine JSON SHA256 `bee3411413882d8d8acdff5dd23ebc9fe057d4079c0753564d6b1e70105ee32a`.

## Active scientific jobs

Snapshot at `2026-07-12T10:21:45Z`:

| Node/GPU | Job | Progress | Placement |
| --- | --- | ---: | --- |
| an12/0 | ViRL39K real | 1,974 / 4,096 | TP1, one replica |
| an12/1 | ViRL39K gray | 2,004 / 4,096 | TP1, one replica |
| an12/2 | ViRL39K noise | 2,012 / 4,096 | TP1, one replica |
| an12/3 | ViRL39K none | 1,746 / 4,096 | TP1, one replica |
| an12/4 | ViRL39K caption | 1,754 / 4,096 | TP1, one replica |
| an12/6 | Step-100 Geometry3K gray | 32 / 1,889 | TP1, one replica |
| an12/7 | Step-100 Geometry3K noise | 52 / 1,889 | TP1, one replica |
| an29/1 | Step-100 Geometry3K none | startup/model load | TP1, one replica |
| an29/5 | Step-100 Geometry3K caption | startup/model load | TP1, one replica; frozen 3B store |

- an12 GPU5 and an29 GPUs0/2/3/4 host neighboring researcher processes. They are treated as normal and were not modified.
- Every listed Blind Gains job is single-node and records node, GPU IDs, TP width, replica count, seed, hashes, command, and artifact paths in its immutable run directory.

## Code and verification

- Full repository suite: `467 passed` after launcher hardening.
- FlipTrack image outputs now fail closed on existing final/partial files and publish predictions/metrics by atomic rename.
- Image-evaluation manifests now pin seed, noise seed, and model revision.
- Noncontiguous GPUs map to shards by replica ordinal instead of physical GPU number.
- Pilot smoke saves now inherit the shared quota guard used by full pilot arms.
- Commits pushed in this continuation: `91d1efa`, `767196e`, `7188ecd`, `c84623b`.

Problems:
- Human R19 contact-sheet audit is still absent. This blocks final L12 regardless of machine results.
- Both PI signatures are still absent. The draft preregistration cannot be promoted by the implementing agent.
- L1 parser agreement remains below 0.95 and is explicitly retained for PI review rather than hidden.
- ViRL39K and the four step-100 blind evaluations are long-running; their partial rows are not consumed as results.
- Item-bootstrap intervals do not measure run-to-run RL variance.
- The working tree still contains unrelated user state (`CLAUDE.md` deletion, untracked `AGENTS.md`, prior storage snapshots, and the prior progress report); none was reverted or committed.

Decision:
- Treat L3 as mechanically complete and use the pinned pilot reward for evaluations and future authorized pilot arms.
- Keep L12/L13 fail-closed. No pilot metric inspection or optimizer step occurs before final preregistration merge.
- Use free GPUs for exact-contract checkpoint evaluation rather than synthetic utilization.
- Preserve V1 reports and publish V2/V3 artifacts alongside them; no result file or checkpoint was overwritten.

Next actions:
- Monitor and finalize the five ViRL39K conditions, then produce the L10 report and distinct audited JSON.
- Complete and compare all five step-100 Geometry3K conditions under the exact pilot contract.
- Request the human R19 contact-sheet decisions and both PI signatures through the researcher.
- After those human inputs, generate final `reports/preregistration_pilot_v1.md`, rerun objective consistency checks, and only then permit L13 launch authorization to succeed.
