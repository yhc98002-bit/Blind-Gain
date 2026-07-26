# Registered D2 test-time image-access ablation (v1)

Registered 2026-07-26 before any D2 inference. Inference-only; alters no frozen
endpoint, launches no training, and does not reopen any sealed value. Uses only
seed-1 and seed-2 lineages whose values are already open.

## Status and scope

Every completed Blind Gains contrast varies image access **during training**.
This diagnostic varies it **at test time** on the frozen Geometry3K pilot
evaluation set, holding the model fixed. Human-facing text uses
`test-time image access`; the layer names remain `candidate-evidence ranking`
and `open-form realization` (this diagnostic measures open-form realization
only). `already perceived/understood` remains hypothesis language per
`docs/registered_x2_ladder_v1.md`.

## Question

A1 gains ~+25pp on Geometry3K, and that gain requires real images during
training (blind arms recover little). It does not follow that the trained
model still needs the image at inference: the gain could be carried by an
image-independent policy or answer-production change. D2 separates these.

## Frozen inputs

- Evaluation manifest: `data/geometry3k_caption_images_manifest.jsonl`
  (601 registered rows), identical to the registered pilot Geometry3K
  evaluations.
- Decoding contract identical to those evaluations: format prompt
  `artifacts/repos/EasyR1/examples/format_prompt/r1v.jinja`, prompt contract
  `answer-tags-v1` (SHA256 `7ac39f53…`), greedy, `max_tokens` 2048,
  `max_model_len` 8192, seed 20260710, canonical-v2 parser.
- Conditions from `src/eval/conditioned_inputs.py`: `real`, `gray`, `none`
  (identical materialization to the training-side conditions).
- Models (merged step-100 actors, index SHA256 pinned in the run manifests):
  - `a1_seed1_step100`: `checkpoints/pilot/mech_a1_real_resume60/global_step_100/actor/huggingface`
  - `a1_seed2_step100`: `checkpoints/pilot/mech_a1_real_seed2/global_step_100/actor/huggingface`
  - `a2b_seed1_step100`: `checkpoints/pilot/mech_a2b_noimage_retry4/global_step_100/actor/huggingface`
  - `a2b_seed2_step100`: `checkpoints/pilot/mech_a2b_noimage_seed2_resume20/global_step_100/actor/huggingface`
- Base-model cells are **not re-measured**: the registered arm step-0
  evaluations already measure the identical frozen base under all three
  conditions on this exact set and contract, and are pinned here as inputs —
  base/real 0.1747 (A1 step 0), base/gray 0.0899 (A2 step 0), base/none
  0.0682 (A2b step 0).

## Cells (8)

`a1_seed{1,2}_step100` × {real, gray, none}; `a2b_seed{1,2}_step100` × {real}.
The `a1 × real` cells are also a pipeline reproduction check against the
published step-100 values (0.4276 seed 1, 0.4210 seed 2); a deviation beyond
±0.01 invalidates the run and is reported instead of the readings.

## Registered statistics

Per model M and condition c: `Acc_final(M, c)` on the 601 rows, with a
1,000-resample item bootstrap 95% CI (percentile, seed 20260710).

Primary, per seed:

    RetainedGainBlind = [Acc(A1, none) − 0.0682] / [Acc(A1, real) − 0.1747]

Secondary, per seed: the same ratio with `gray` in place of `none`;
`Acc(A2b, real) − Acc(A2b, none)` using the published A2b step-100 value as
the `none` term (test-time image benefit retained by a blind-trained arm);
and the absolute test-time drop `Acc(A1, real) − Acc(A1, none)`.

## Registered readings (pre-committed, before any cell runs)

- **(a) RetainedGainBlind ≤ 0.25** → the Geometry3K task gain is
  predominantly image-mediated at test time: the trained policy still needs
  the image to realize its gain.
- **(b) 0.25 < RetainedGainBlind < 0.75** → mixed: a substantial part of the
  gain is realized without image access, the remainder is image-mediated.
- **(c) RetainedGainBlind ≥ 0.75** → the gain is predominantly
  image-independent at test time; training-time image access was necessary to
  acquire a capability that inference does not exercise through the image.

Both seeds must fall in the same band. If they do not, no branch is assigned
and both values are reported. No SESOI is registered for these quantities, so
this diagnostic assigns no B1/B2/B3 gate decision.

## Execution constraints

- Inference-only, four TP1 cells at a time on GPUs 4–7 of whichever node has
  no trainer on those GPUs; trainer GPUs are never touched.
- Values open only after all eight cells complete and the finalizer runs;
  partial matrices must not be interpreted.

## Deliverables

Eight immutable prediction files with run manifests, and
`reports/d2_testtime_ablation_v1.{md,json}` plus an audit artifact containing
the registered tables and the branch under the rule above.
