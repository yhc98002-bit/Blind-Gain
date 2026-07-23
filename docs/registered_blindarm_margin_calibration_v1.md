# Registered Blind-Arm Margin-Calibration Diagnostic V1

## Status and scope

This is a post-seed-1, prospectively registered calibration diagnostic. It is
inference-only, alters no frozen pilot endpoint, launches no training, and does not
retroactively promote any seed-1 result. It extends the registered seed-1
visual-evidence ranking instrument, unchanged, to the three blind/caption seed-1
checkpoints in order to calibrate the observed candidate-margin inflation against
generic confidence sharpening.

At registration, none of the three models below had been run under this scoring
contract. Human-facing text uses `visual-evidence ranking` or `candidate-answer
ranking`. The phrase `perception improved` is prohibited without additional direct
evidence.

## Question

The seed-1 diagnostic observed that A1 real-image training raises the registered
image-dependent paired log-probability margin by approximately +0.089 (step 60) and
+0.150 (step 100) while discrete pair success stays flat. Two accounts are
compatible with that observation:

1. **Image-linked evidence use:** training strengthens the association between real
   visual input and the correct candidate; margin inflation requires visually
   informative training.
2. **Generic confidence sharpening:** RL training sharpens candidate log-probability
   spreads regardless of whether training carried useful visual information; margin
   inflation would appear in blind-trained models as well.

This diagnostic separates the two by measuring the identical margin statistic on
matched seed-1 checkpoints whose training carried no useful visual information
(A2 gray, A2b no-image) or caption-mediated information only (A3).

## Frozen inputs

- Instrument, candidate registry, prompt contract, processor, scoring, and pair
  definitions: identical to `docs/registered_seed1_visual_evidence_ranking_v1.md`;
  the candidate registry is `data/fliptrack_r19_visual_evidence_candidates_v1.jsonl`,
  SHA256 `fa9456941a730e174b1ed4bb4caefc151778e3f1adc0ca77db941955a4215f81`.
- Configuration: `configs/eval/blindarm_margin_calibration_v1.json`. It differs from
  the seed-1 configuration only in the `models` table, `schema_version`, and `scope`.
- Models (seed-1 lineages, merged step-100 actors, model-index SHA256 pinned in the
  configuration):
  - `a2_step100`: `checkpoints/pilot/mech_a2_gray_resume60_retry2/global_step_100/actor/huggingface`
  - `a2b_step100`: `checkpoints/pilot/mech_a2b_noimage_retry4/global_step_100/actor/huggingface`
  - `a3_step100`: `checkpoints/pilot/mech_a3_caption_resume20/global_step_100/actor/huggingface`
- Conditions: `real`, `gray`, `no_image` — nine cells total.
- The scorer implementation (`scripts/eval_qwen_vl_visual_evidence_ranking.py`) is
  used unchanged. Queue and cell-launcher parameterization is operational only and
  does not alter scoring.

## Registered statistics

Primary, per model M in {a2_step100, a2b_step100, a3_step100}:

- image-dependent paired-margin effect of M
  = mean paired margin of M under `real` − mean paired margin of the frozen base
  under `real`, with the same 95% paired bootstrap over pairs used in the seed-1
  diagnostic. Blind-condition margins are structurally zero by input symmetry and
  are retained as integrity controls (any nonzero blind-condition margin marks a
  broken cell, not a finding).

Secondary, same estimators as the seed-1 diagnostic: candidate top-1, candidate
MRR, pair success, raw-sum robustness.

Calibration-specific secondary statistics, computed by the finalizer over both the
seed-1 cells and these nine cells from the immutable per-candidate score vectors:

- candidate-distribution normalized entropy (softmax over mean-token-log-prob
  scores within the frozen candidate set);
- top1-minus-top2 score gap under each condition.

These quantify condition-independent sharpening directly.

## Registered interpretation rule

Fixed before any cell runs:

- If the blind arms' real-input margin effects are small relative to A1 step 100
  (point estimates below half of the A1 effect, with non-overlapping 95% CIs
  against the A1 effect), the calibration supports margin inflation being specific
  to real-image training.
- If any blind arm's real-input margin effect is comparable to A1 step 100
  (CI overlapping the A1 effect), margin inflation cannot be attributed to
  image-linked evidence use, and the seed-1 margin observation must be described
  as generic confidence sharpening pending further evidence.
- Because no margin-scale SESOI was registered for the seed-1 diagnostic, this
  rule is descriptive calibration, not a B1/B2/B3 gate. No automatic scientific
  gate decision follows from these cells alone.
- Entropy and top1-top2 statistics are reported descriptively in the same tables.

## Execution constraints

- Placement: `an29` GPUs 4–7 only, one TP1 cell per GPU, while the seed-3 A1
  trainer holds `an29` GPUs 0–3. The queue is restricted to GPUs 4–7 by command
  line and cannot occupy trainer GPUs at any point, including after A1 release.
- No cell may start unless its target GPU reports zero compute processes.
- Image caches and outputs live in each cell run directory on shared storage;
  nothing is written to node-local `/tmp`.
- Performance values stay closed until all nine cells complete and the finalizer
  and audit run; partially complete matrices must not be interpreted.

## Deliverables

- Nine immutable `scores.jsonl` cells with run manifests.
- A finalizer report versioned as `reports/blindarm_margin_calibration_results_v1.{md,json}`
  containing the registered tables and the calibration verdict under the rule above.
