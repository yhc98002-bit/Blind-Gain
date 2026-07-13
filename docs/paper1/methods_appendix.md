# Methods Appendix

## Registration and Provenance

The four-arm Geometry3K pilot is governed by
`reports/preregistration_pilot_v1.md` (SHA256
`fb7e220f1dee62a01a0ce9ee8c4a9f1f1543f189239eb0e83466ed64ad1c1edb`).
Its merged-at-HEAD authorization predates every pilot optimizer step. Each run
records the registration commit, git/config/data hashes, node and GPU IDs,
tensor-parallel width, replica count, seed, command, times, artifact paths, and
deviations in an immutable `run_manifest.json`.

Extensions use a separate fail-closed registry. A document that merely
mentions registration is not authorization; the exact merged-at-HEAD marker
must be a standalone line before the associated optimizer step.

## Training Stack

The pilot uses Qwen2.5-VL-3B with EasyR1/GRPO, SDPA selected through
`EASYR1_ATTN_IMPLEMENTATION=sdpa`, a frozen vision tower, group size `G=5`,
and one single-node colocated training/rollout job per arm. Models at or below
7B use TP1; parallelism comes from independent replicas rather than unnecessary
tensor-parallel width. Configs are identical across A1 real, A2 gray, A2b
no-image, and A3 caption except for `image_condition` and the data-path fields
that condition requires.

The published-recipe anchor is not pooled with the pilot. It retains its native
reward and launched configuration as prior-observation evidence; every anchor
versus pilot deviation is disclosed in the preregistration.

## Prompt, Parser, and Reward

All pilot arms share one frozen prompt contract. Canonical-v2 normalizes only
the extracted final-answer span, records `extractor_valid` separately from
contract-exact `contract_valid`, and preserves every native/canonical
disagreement row. `Acc_strict = contract_valid AND Acc_final`; the accounting
identity `StrictGain = AnswerGain + G_format` is fixture-enforced.

The pilot reward performs canonical-v2 extraction and then mathruler grading.
When canonical numeric equivalence and mathruler disagree, mathruler controls
the optimized reward and a reason-coded disagreement is retained. Accuracy and
format components are weighted 0.5/0.5, matching the quoted native r1v source;
native r1v remains a per-rollout shadow field.

## Storage, Checkpointing, and Placement

Pilot checkpoints save first to shared storage because compute-node `/tmp` is
not persistent or large enough for them. A quota-aware guard refuses writes
that would leave less than 20 GiB shared headroom. The watcher verifies merged
checkpoint hashes before moving raw state and intermediate merged checkpoints
to the login-node archive; only the latest raw state is retained for resume and
only final merged checkpoints remain on shared storage. Node-local scratch uses
a separate 40 GiB floor.

Every training and serving job is single-node unless a model genuinely needs
more than eight GPUs. Foreign researcher processes are normal neighbors and are
never killed or treated as anomalous.

## Statistical Analysis

Primary cross-arm estimands use final-minus-step-0 greedy `Acc_final` on the
same Geometry3K test items with paired item-bootstrap intervals. Recovery
fractions are conditional on a nontrivial A1 gain. Gray/no-image equivalence is
supported only when its paired interval lies fully inside the registered
`+/-0.05` margin.

The primary mechanism analysis is a hurdle contrast: per-item gain among
items with at least one of 16 base samples correct versus items at the observed
`0/16` floor, separately under each arm's own information condition. Secondary
analyses use tie-corrected Spearman association with Jeffreys-smoothed reward
opportunity `q_i`; `q_i` is an estimate, not an observed latent. Newly solved
floor items receive 64 additional base samples before support-expansion
language is used.

FlipTrack reports pair accuracy, collapse rate, catch stability, permutation
nulls, paired bootstrap intervals, and per-template results. R19 geometry is
primary, R19 overall is key secondary, and cued chart point-value reading is
reported separately. R20 is robustness evidence and is never pooled with R19.

## Decontamination

Flagged rows are conservative contamination candidates, never confirmed
duplicates.

The Geometry3K pilot trains on the frozen 1,288-item ID set at
`data/geo3k_pilot_filtered_ids.json` (SHA256
`8631d015ee8593669b46cc707b9fe1fb3690391520bccf416b64bbb2306ff7d1`).
It removes the union of registered Layer-1 and train-versus-test automatic
removal candidates. ViRL39K decomposition uses a separately frozen,
source/category-stratified subset and a ViRL-by-Layer-1 decontamination
manifest before any training unit launches.

## Evaluation Lock

Checkpoint evaluations are greedy with temperature 0, top-p 1.0, one output,
fixed maximum tokens, and the same prompt contract at base and every trained
checkpoint. Blind conditions preserve the question and registered text while
changing only the information channel. A3 captions are fixed, question-blind,
content-hash keyed, and inserted without image tokens; missing captions fail
loudly.

The sampled blind-solvability audits are distinct from checkpoint evaluation:
they use 16 registered samples per item at the pilot rollout temperature and
2048-token response limit, plus a separate greedy pass. Condition, decoding,
prompt, parser, reward, and output hashes are retained per row and independently
recomputed in the audited artifact.
