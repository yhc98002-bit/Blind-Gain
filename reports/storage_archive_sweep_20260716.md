# Storage Archive Sweep, 2026-07-16

Status:
- Complete. Exactly one explicitly superseded Blind Gains archive was preserved
  on shared storage and removed from login scratch only after full-tree
  verification.
- No unrelated `/tmp` content was inspected beyond size/ownership metadata,
  moved, or deleted.

Evidence:
- Immutable run:
  `experiments/runs/storage_sweep_superseded_a3_login_20260716T150633Z`;
  status complete, exit 0.
- Source classification: failed initial A3 run superseded by
  `mech_a3_caption_resume20_an29_20260713T144233Z`, which is complete, merged,
  R19-scored, and independently audited.
- Source:
  `/tmp/blindgain_checkpoint_archive/mech_a3_caption_an29_20260713T033039Z`.
- Destination:
  `/XYFS02/HDD_POOL/paratera_xy/pxy1289/blindgain_archive/login_tmp_checkpoint_archive/mech_a3_caption_an29_20260713T033039Z`.
- Files: 24; exact bytes: 49,101,916,160.
- Pre-copy source manifest:
  `reports/storage_relocations/20260716/login_tmp_mech_a3_caption_an29_20260713T033039Z_source.sha256`,
  SHA256 `8e659be221dc8bbec1c1d4f7650a9a19d9be751da17c0521b81dcae21bbf16a8`.
- Verified relocation manifest:
  `reports/storage_relocations/20260716/login_tmp_mech_a3_caption_an29_20260713T033039Z_relocation.json`,
  SHA256 `fc8c0ca4ee4ec476de86950ef8269ea79eb37e826279da3b3e6d9483060482fb`.
- The pre-write Tier-S guard used the quota-aware snapshot and projected
  703,303,071,744 bytes remaining, above the 20-GiB floor.
- The source is now a symlink to the verified persistent copy, preserving old
  artifact references without consuming the original scratch bytes.

Problems:
- The generic relocation manifest also contains its internal filesystem-level
  Tier-T check. The authoritative quota check for this move is the preceding
  Tier-S event in the immutable run log and `logs/storage_guard.jsonl`.
- Quota usage is being remeasured because the prior snapshot predates this
  49.1-GB shared write.

Decision:
- Stop after this one minimal move. Do not sweep additional archives unless a
  later guard requires more headroom.
- Login `/tmp` rose from about 45.6 GiB to about 241 GiB free; the Blind Gains
  checkpoint archive fell from about 401 GiB to about 356 GiB.

Next actions:
- Finish the fresh quota snapshot.
- Preserve the new headroom for A2 raw-state retention after its merged
  checkpoint is hash-verified.
