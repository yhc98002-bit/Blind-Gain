# Registered Extensions V1

Status:
- Transcription prepared from `docs/MAIN_PHASE_BRIEF.md` and updated after the
  audited M1 fork ruling and the PI ruling in
  `docs/MAIN_PHASE_RULING_20260716.md`.
- Registration state: merged-at-HEAD; merge is sign-off.
- M5 is authorized after its restore-and-resume integrity check passes. M6, M7,
  and M9 remain subject to their own registered data, reward, and readiness
  preconditions; this marker does not waive them.
- Fields dependent on M3, M7 data preparation, or M8 retain the PI-requested
  `{computed-pending}` marker.

## Global Contract

- Every training unit is registered before its first optimizer step.
- A launcher's merged-at-HEAD check is fail-closed.
- Every irregularity is one immutable deviations-log line.
- Training and serving jobs are single-node unless a model genuinely requires
  more than eight GPUs.
- Models at or below 7B use TP1; throughput comes from independent replicas.
- Evaluations use the locked prompt contract and greedy decoding unless a
  sampled analysis is explicitly registered below.
- Answer-pointing circles, highlights, and arrows are prohibited for constructs
  claiming localization, search, or correspondence.

## Extension 1: Anchor Long Horizon

Design:
- Resume the engineering anchor from its archived step-100 raw state.
- Continue to the fixed endpoint at optimizer step 400.
- Evaluate the registered benchmark and FlipTrack suites at steps 150, 200,
  300, and 400.
- **Do not stop because the desired curve appears early.**

Precondition:
- Restore the archived step-100 raw state.
- Run a one-step restore-and-resume integrity check.
- Compare restored model, optimizer, scheduler, RNG, and data-cursor hashes
  wherever those states expose stable serialization.
- Record pre-resume and resumed loss continuity. A discrepancy blocks the
  continuation and is entered in the deviations log.

Registered fallback:
- If restore integrity cannot be established, run a fresh 400-step job at the
  exact anchor configuration.
- Disclose the fresh-run fallback in the run manifest and results report.
- The fixed step-400 endpoint and evaluation schedule remain unchanged.

Primary readout:
- The single primary contrast is
  `Delta = R19 geometry pair-acc(step 400) - pair-acc(step 100)`, with an
  item-paired bootstrap 95% confidence interval.
- `FLAT` iff the confidence interval is contained in `[-0.05, +0.05]`.
- `RISING` iff `Delta >= +0.05` and the confidence-interval lower bound is
  greater than zero.
- `FALLING` iff `Delta <= -0.05` and the confidence-interval upper bound is
  less than zero.
- `INDETERMINATE` otherwise, reported exactly as such.
- Step 400 is terminal. There is no extension or rerun under any outcome.
- Steps 150, 200, and 300 are descriptive and cannot select the endpoint.

Context and secondary readouts:
- The “delayed-learning objection answered” context condition holds when the
  Geometry3K benchmark step-300-to-step-400 paired delta has a confidence
  interval containing zero or absolute delta below 0.02. If the benchmark is
  still rising at step 400, report the objection as partially addressed and
  stop.
- Overall R19 uses the same four-way rule as a secondary.
- Report a per-category table.
- Report blind-floor persistence at step 400: gray/noise pair accuracy at most
  0.05 and Collapse Rate at least 0.95.
- There is one primary contrast and no multiplicity correction.

## Extension 2: Mini-A5 Matched Control

Arms:
- CP arm: pair members share one group uid and each member receives the
  broadcast joint reward
  `r_i = acc(a_i) * acc(b_i)`.
- Same-data standard-GRPO arm: identical pair corpus and rollout grouping, with
  member-level accuracy reward.

Corpus:
- One generated pair corpus from training-only templates.
- Training templates are disjoint from every FlipTrack evaluation template.
- The frozen decontamination manifest records template identities, parent
  groups, and hashes.
- Held-out-template FlipTrack is the primary evaluation set.

Matching:
- Same Qwen2.5-VL-3B base model, prompts, G, optimizer budget, rollout token
  budget, batch construction, parser, and checkpoint cadence.
- Fixed duration: `{computed-pending}` steps selected within the PI-decided
  100-150-step range before launch.
- Fixed token budget: `{computed-pending}`.

Primary estimand:
- `Delta_CP - Delta_same-data` on held-out-template FlipTrack, with paired
  item-bootstrap confidence interval.

Required diagnostics:
- Advantage-tensor equivalence test showing that only the registered reward
  assignment differs.
- Catch-trial stability.
- Step-0 reward-hit rate and reward variance for CP and member-level rewards.
- Pair-order and answer-prior checks.
- Template-disjointness check in the decontamination manifest.

Reward fallback rule:
- There is no silent switch to a shaped reward.
- Any fallback reward must be written in a preregistered addendum and approved
  by a PI before its first optimizer step.

## Extension 3: ViRL39K 3B Decomposition

Design:
- Four arms: A1 real, A2 gray, A2b no-image, and A3 fixed question-blind
  captions.
- Two seeds per arm.
- Frozen decontaminated ViRL39K subset.
- Matched model, prompts, G, optimizer steps, token budget, batch size, reward,
  parser, checkpoint cadence, and evaluation protocol.

Computed fields:
| Field | Registered value |
| --- | --- |
| M1 fork row | `strong source/category heterogeneity -> H-mixed becomes the headline; stratify` (`reports/virl_fork_ruling.md`) |
| Frozen subset path | `{computed-pending}` |
| Frozen subset SHA256 | `{computed-pending}` |
| ViRL x Layer-1 decontamination manifest | `{computed-pending}` |
| 3B caption-store path and SHA256 | `{computed-pending}` |
| Caption coverage | `{computed-pending}` |
| Steps and token budget | `{computed-pending}` |
| Seeds | two fixed seeds; exact identifiers `{computed-pending}` |
| Checkpoint cadence | `{computed-pending}` |

Analysis:
- Report the corpus aggregate and all registered source and category strata;
  a pooled-only readout is prohibited by the M1 heterogeneity ruling.
- Apply M10 support sharpening to newly solved items that were 0/16 under the
  arm's own base condition.
- Use item-paired intervals; seed dispersion is separately descriptive.

## Extension 4: 7B Flagship

Arms:
- A1 real.
- A2 gray.
- A2b no-image.
- A3 frozen, question-blind captions produced by the 7B base model.
- A2 is retained because the precommitted M8 fork rule fired: audited 7B
  greedy accuracy is 0.2456 for gray and 0.1824 for no-image, with
  non-overlapping 95% intervals. This is a rule-citation, not a discretionary
  arm-selection decision.

Runs:
- Three seeds per arm, seed 1 first.
- One node per arm.
- TP1 independent replicas for the 7B model.
- Item-paired analyses within each seed and descriptive seed dispersion across
  seeds.

Caption sensitivity:
- Primary A3 uses the frozen 7B own-caption store.
- A fixed-3B-caption condition is evaluated as an inference or small-scale
  sensitivity analysis; it is not silently substituted for primary A3.

Computed fields:
| Field | Registered value |
| --- | --- |
| M8 gray/no-image rule evidence | `reports/blind_solvability_virl39k_7b_sample_v1.md`; gray 0.2456 [0.2327, 0.2595], no-image 0.1824 [0.1702, 0.1939] |
| Final arm set | A1 real, A2 gray, A2b no-image, A3 7B own-caption; three seeds each |
| M8 model revision | `Qwen/Qwen2.5-VL-7B-Instruct@cc594898137f460bfe9f0759e9844b3ce807cfb5` |
| M8 frozen audit sample | `data/virl39k_blind_sample_4096.jsonl`; SHA256 `ffbad6eaff57f6dd11f136b066e4d4206e43381281a3cb24cc677241c360e6d5` |
| M8 audit-sample own-caption store | `experiments/runs/virl39k_sample4096_qwen25vl7b_captionstore384_retry_20260710T163500Z/shards/store_shard_0.jsonl`; SHA256 `426644dae442fcc4ee3d6e023928e179d3ac957ec3857486d37e7bb7a2f66b0c` |
| M8 audit-sample caption coverage | 4,297/4,297 unique frozen-sample images; no missing or extra image hashes |
| M8 machine audit | `reports/blind_solvability_virl39k_7b_sample_v1_audited.json`; status pass, all 15 checks true |
| ViRL subset path and SHA256 | `{computed-pending}` |
| 7B training-subset own-caption store path and SHA256 | `{computed-pending: training subset is not the 4,096-item M8 audit sample}` |
| 7B training-subset caption coverage | `{computed-pending}` |
| A1 config path and SHA256 | `{computed-pending}` |
| A2b config path and SHA256 | `{computed-pending}` |
| A3 config path and SHA256 | `{computed-pending}` |
| Conditional A2-gray config and SHA256 | `{computed-pending}` |
| Seeds, steps, token budget, cadence | `{computed-pending}` |

## Deviations Log

| Time UTC | Training unit | Deviation | Reason | Effect on estimands | PI disposition |
| --- | --- | --- | --- | --- | --- |
