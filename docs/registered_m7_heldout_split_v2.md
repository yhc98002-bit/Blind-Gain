# Registered M7 held-out evaluation split (v2, image-disjoint)

Registered 2026-07-26, before any M7 optimizer step and before any M7
evaluation. **Supersedes `docs/registered_m7_heldout_split_v1.md`**, which was
registered minutes earlier and whose artifacts were never consumed by any
training run, evaluation, or readout.

## Why v1 is superseded

The v1 item-level construction was executed and its own integrity check
reported that **954 images appear in both the training and held-out corpora**
(19.5% of the 4,894 held-out images) — ViRL39K carries several items per
image. That is a defect for this specific study: A1 trains with real images,
so held-out items whose images were seen in training can be answered partly
from memorized image content, while the blind arms (gray, no-image) have no
such channel. The amendment's registered recovery statistic divides blind gain
by the A1 gain, so an inflated A1 denominator would deflate every recovery
fraction — biasing the dose-response test in a direction that is hard to
distinguish from the hypothesis being tested. The fix must precede training.

## Construction (fixed here, executed once)

- Source: the frozen subset `data/virl39k_main_filtered.jsonl` (29,756 items,
  dataset SHA256 `d4e0ef87…`), keyed by `qid`.
- **Image-disjoint grouping:** items are grouped into connected components
  under the relation "shares at least one `metadata.image_sha256` value".
  Components are the indivisible unit of allocation, so no image can appear on
  both sides of the split.
- Stratification: each component is labeled by the joint
  `(metadata.source, metadata.category)` of its lexicographically smallest
  `qid` (components are overwhelmingly single-stratum; the rule is fixed here
  so the label never depends on an outcome).
- Allocation: within each joint stratum, components are ordered by
  `sha256(component_key + "|m7-heldout-v2")` where `component_key` is the
  smallest `qid` in the component, and components are taken in that order
  until at least `0.15 × n_items_in_stratum` items are held out; strata with
  ≥2 components hold out at least one component.
- The complement is the M7 training corpus. Every arm and both M7 seeds train
  on the identical training corpus and are evaluated on the identical held-out
  corpus, with item identity preserved by `qid`.
- Artifacts: `data/virl39k_m7_train_v2.jsonl`,
  `data/virl39k_m7_heldout_v2.jsonl`, `data/virl39k_m7_split_manifest_v2.json`.

## Fixed properties (verified by the builder, fail-closed)

- Exact partition of the frozen subset; no duplicated or missing `qid`.
- **Zero shared images between train and held-out** — the builder refuses to
  write artifacts otherwise.
- Per-stratum held-out counts published, with the amendment's ≥30 held-out
  eligibility flag; strata below it stay in the published per-stratum table
  labeled `descriptive-small-n` and are excluded only from rank statistics.
- Because allocation is by whole components, realized per-stratum held-out
  shares deviate from 15%; the realized shares are recorded per stratum and
  the corpus total is reported.

## What this document does not do

It changes no registered prediction, statistic, threshold, or interpretation
from `docs/registered_m7_amendment_v1.md`, and authorizes no optimizer step.
