# Mini-A5 Readiness V4

Status:
- `blocked`. Training corpus, exact rewards, corrected grouping, matched main
  configs, step-0 reward statistics, and the answer-preserving catch set are
  frozen and independently audited.
- The two registered one-step GPU plumbing smokes and the post-smoke main-arm
  registration marker remain required before a 120-step arm may launch.
- No PI gate decision is made.

Evidence:
- Training corpus: 3,000 pairs / 6,000 rows; Parquet SHA256
  `0b0f0965987d1c340c3ebd78da742c9d99b319b61524b5cb42960519fd9c9b28`.
- Step-0 audit: `reports/mini_a5_step0_reward_audit_v1.json`, SHA256
  `debc84d4ae0c22f44f43345fb3510033aea6b8bfee09ed71f6f768bbbe97107f`.
  CP hit-rate/variance is 0.146875/0.125303; member is
  0.252604/0.188795. The named-trajectory CP stratum is sparse and retained
  without data-dependent replacement or weighting.
- Catch set: `data/mini_a5_catch_v1/pairs.jsonl`, 300 pairs, SHA256
  `fbd83d52fa01103bfb839fa2572eb9164c532f8c3a3431da6ca8f6033d6a9728`.
- Catch audit: `reports/mini_a5_catch_audit_v1.json`, SHA256
  `37b9662c1f873c6b6cb7ee04a87a954dadef54ea974933c0e50e5ab8c60c2317`.
  All 18 checks pass: 100 pairs per held-out template, 600 images, 600 exact
  masks, target-region pixel invariance, preserved answers, and zero
  template/pair/image-hash overlap with training, R19, R20, or chart-v08.
- Side assignment was random and near-balanced: 147 unswapped / 153 swapped.
- Combined advantage/config audit:
  `reports/mini_a5_advantage_equivalence_v2.json`; all 31 checks pass. It binds
  the current EasyR1 overlay, step-0 audit, catch audit, exact 120-step budget,
  and the adversarial retired-shared-`2G` fixture.
- The isolated overlay now emits an opt-in structured runtime event for the
  joint advantage path. The shared EasyR1 checkout remains untouched.
- Both one-step smoke configs materialize through EasyR1 `PPOConfig` as
  one-node/eight-GPU/TP1 runs and differ only in the four registered arm
  fields. The fixed first batch contains exactly eight adjacent A/B pairs.

Problems:
- No real EasyR1 optimizer step has yet used the Mini-A5 overlay.
- `docs/registered_mini_a5_smoke_v1.md` still requires its immutable
  commit-binding marker before either smoke can launch.
- Main-arm launch remains separately fail-closed after smoke completion.

Decision:
- Freeze the 300-pair catch set; do not regenerate or replace examples using
  model output.
- Register and run CP/member one-step smokes sequentially on the first
  priority-compliant fully available node.
- Only after an independent smoke audit may a new marker authorize the two
  matched 120-step runs.

Next actions:
- Commit the smoke registration, create its commit-binding marker, and queue
  it behind active seed-2/M5/M11 work.
- Implement the independent smoke auditor and checkpoint-retention inventory
  while the queue waits.
