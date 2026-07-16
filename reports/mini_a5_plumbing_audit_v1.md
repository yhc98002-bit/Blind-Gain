# Mini-A5 Plumbing Audit V1

Status:
- `blocked`. The exact CP/member reward and pair-level advantage machinery are
  implemented and tested, but the immutable mass corpus, step-0 reward audit,
  launch configs, and GPU smoke have not yet landed. No M6 optimizer step is
  authorized by this report.

Evidence:
- Exact CP reward: `src/rewards/cp_grpo_reward.py`, SHA256
  `e8dea3e49c03c44a050881fba6e9bec5c8120977659f5a786f2bf4526b6213f0`.
  `overall = acc(a_i) * acc(b_i)` is broadcast to both members; the matched
  control uses member accuracy. Format and canonical-v2 values are shadows and
  do not shape either M6 reward.
- Pilot-precedence extraction helper: `src/rewards/pilot_reward.py`, SHA256
  `706de156da12ecbcfa2d52591b7477baf322fe488b98d3a52fac4ec2d628d97d`.
  Existing pilot scoring delegates to this helper without changing its result.
- Pair grouping and unique-pair GRPO normalization:
  `src/train/cp_grouping.py`, SHA256
  `8a00c722b52b9bec7e571638a9a987bc575f38b1d91db356e8711d2c9a57711b`.
- Isolated EasyR1 overlay:
  `docs/easyr1_mini_a5_pair_grouping_patch.diff`, SHA256
  `816ea43cf99b4afc5ba8a4d4a42805b2a928d7d4871e79d029d9acb0eca9a8f2`.
  `scripts/prepare_easyr1_mini_a5_worktree.sh` applies the seven pinned recovery
  patches plus this overlay to a detached worktree. An integration run produced
  the expected files while the live EasyR1 diff stayed byte-identical at
  `503f029de050f6374e912749a2ef51e532b5cd62ce5f9fc1de00aa45d51bbbcd`.
- Corpus generator: `src/fliptrack/build_mini_a5_train.py`, SHA256
  `8ee3d06361159d8aff808a3e5ef7a6433e21a4ef43e301b8a6094bb19b4b013b`.
  It defines three training-only template IDs, exact pixel-difference masks,
  randomized semantic side assignment, pair-adjacent pre-shuffled rows, atomic
  publication, Parquet conversion, and R19/R20/chart-v08 overlap checks.
- Focused validation: 38 reward/grouping/overlay/pilot tests passed, then 17
  corpus/grouping/overlay tests passed. Python compilation, ShellCheck,
  `git diff --check`, and a real detached-worktree patch application passed.

Adversarial fixtures:
- Inputs lacking explicit pair identity now fail instead of being paired by row
  position.
- Duplicate/missing A/B members and non-broadcast joint rewards fail.
- A naive normalization over 2G duplicated rewards is shown not to equal GRPO
  over G unique pair outcomes; the registered implementation matches the latter.
- Independent row shuffle and odd pair-grouped batch sizes are rejected.
- Injected training/evaluation template overlap and overwrite attempts fail.

Problems:
- The 3,000-pair corpus has not yet been generated from committed code.
- EasyR1 reward-manager/trainer integration has not had a GPU dry run.
- Advantage equivalence is unit-tested but still needs an immutable machine
  artifact tied to the eventual CP and same-data configs.
- Step-0 CP/member reward hit rates and variances, catch-trial inputs, final
  100-150 step choice, and matched token budget remain pending.

Decision:
- Keep the shared EasyR1 checkout unchanged while M3 is active. M6 will use the
  isolated worktree only.
- Generate and audit the immutable corpus next. Keep M6 fail-closed until the
  remaining registered prerequisites are present and merged before training.

Next actions:
- Commit this implementation, then generate 1,000 pairs per training-only
  template under a Tier-S storage guard with a run manifest.
- Publish the corpus/decontamination hashes, prepare matched CP/member configs,
  and run the advantage/reward plumbing smoke on the first suitable eight-GPU
  single-node window after higher-priority active jobs release capacity.
