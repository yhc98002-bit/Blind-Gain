# Registered M7 held-out evaluation split (v1)

Registered 2026-07-26, before any M7 optimizer step and before any M7
evaluation. Governed by `docs/registered_m7_amendment_v1.md` and Extension 3
of `docs/registered_extensions_v1.md`; this document supplies only the split
construction the amendment presumes ("the frozen held-out corpus") and adds no
new prediction, statistic, or interpretation.

## Why this is needed

The amendment's quantities are defined on paired held-out items
(`gain[b,s] = Acc_final(step_final) − Acc_final(step_0)` on held-out items;
stratum eligibility at ≥30 held-out items; 5,000 item-paired bootstrap draws
over the held-out corpus), but the frozen ViRL39K training subset
(`data/virl39k_main_filtered.jsonl`, 29,756 items, dataset SHA256
`d4e0ef87…`) carries a single `train` split. The held-out corpus must
therefore be carved from that subset and frozen before training, so that no
arm ever trains on an evaluated item.

## Construction (fixed here, executed once)

- Source: the frozen subset, in its stored order, keyed by `qid`.
- Stratification key: the joint `(metadata.source, metadata.category)` label —
  the amendment's primary stratum definition — so held-out counts are
  distributed across exactly the strata the rank statistics use.
- Allocation: within each joint stratum, items are ordered by
  `sha256(qid + "|m7-heldout-v1")` and the first `ceil(0.15 × n_stratum)` are
  held out, with a floor of 1 held-out item for any stratum of size ≥ 2.
  Hash ordering makes the split deterministic, seed-free, and independent of
  file order; it uses no model output and no outcome information.
- The complement is the M7 training corpus. Every arm and both M7 seeds train
  on the identical training corpus and are evaluated on the identical
  held-out corpus; item identity is preserved across arms and seeds by `qid`.
- Artifacts: `data/virl39k_m7_train.jsonl`, `data/virl39k_m7_heldout.jsonl`,
  and `data/virl39k_m7_split_manifest.json` recording both file hashes, per
  stratum counts, and the count of strata reaching the amendment's ≥30
  held-out eligibility threshold.

## Fixed properties (verified by the builder, fail-closed)

- Partition: train ∪ held-out = the frozen subset exactly; intersection empty;
  no `qid` duplicated within or across the two files.
- No image leakage by construction is **not** claimed: ViRL items may share
  images across strata, and the amendment's endpoints are item-level. Any
  image overlap between train and held-out is measured and reported in the
  split manifest as a descriptive integrity number, not silently ignored.
- Held-out share is reported overall and per stratum; strata below 30 held-out
  items remain in the published per-stratum table labeled
  `descriptive-small-n` exactly as the amendment requires, and are excluded
  only from the rank statistics.

## What this document does not do

It assigns no interpretation, changes no registered prediction or statistic,
and authorizes no optimizer step: M7 launches remain gated on the amendment's
own conditions and on the M7 launcher's fail-closed checks.
