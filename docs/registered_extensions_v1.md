# Registered Extensions V1

Status:
- Transcription prepared from `docs/MAIN_PHASE_BRIEF.md`.
- This commit is not registration sign-off. The document remains inactive until
  Richard confirms the transcription and merges a follow-up that changes this
  state to `merged-at-HEAD; merge is sign-off`.
- Fields dependent on M1, M3, or M8 retain the PI-requested
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
- Report the four checkpoint evaluations and the predeclared flat/rising curve
  verdict. Do not choose a terminal checkpoint from observed performance.

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
| M1 fork row | `{computed-pending}` |
| Frozen subset path | `{computed-pending}` |
| Frozen subset SHA256 | `{computed-pending}` |
| ViRL x Layer-1 decontamination manifest | `{computed-pending}` |
| 3B caption-store path and SHA256 | `{computed-pending}` |
| Caption coverage | `{computed-pending}` |
| Steps and token budget | `{computed-pending}` |
| Seeds | `{computed-pending}` |
| Checkpoint cadence | `{computed-pending}` |

Analysis:
- Report corpus aggregate and registered source/category strata.
- Apply M10 support sharpening to newly solved items that were 0/16 under the
  arm's own base condition.
- Use item-paired intervals; seed dispersion is separately descriptive.

## Extension 4: 7B Flagship

Arms:
- A1 real.
- A2b no-image.
- A3 frozen, question-blind captions produced by the 7B base model.
- Reinstate A2 gray if M3's pooled gray/no-image equivalence interval is not
  fully contained in the registered +/-0.05 margin.

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
| M3 gray/no-image equivalence ruling | `{computed-pending}` |
| Final arm set | `{computed-pending}` |
| ViRL subset path and SHA256 | `{computed-pending}` |
| 7B own-caption store path and SHA256 | `{computed-pending}` |
| 7B caption coverage | `{computed-pending}` |
| A1 config path and SHA256 | `{computed-pending}` |
| A2b config path and SHA256 | `{computed-pending}` |
| A3 config path and SHA256 | `{computed-pending}` |
| Conditional A2-gray config and SHA256 | `{computed-pending}` |
| Seeds, steps, token budget, cadence | `{computed-pending}` |

## Deviations Log

| Time UTC | Training unit | Deviation | Reason | Effect on estimands | PI disposition |
| --- | --- | --- | --- | --- | --- |
