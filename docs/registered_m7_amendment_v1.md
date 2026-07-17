# Registered M7 Mechanism Amendment V1

Status:
- Registration state: merged-at-HEAD; merge is sign-off.
- This amendment governs M7 together with Extension 3 of
  `docs/registered_extensions_v1.md`.
- No M7 optimizer step has run.
- The future M7 launcher must require this exact tracked document at `HEAD`
  before any arm takes its first optimizer step.

## Informed-Prediction Disclosure

This prediction was written after the completed Geometry3K seed-1 readout.
The observed Geometry3K recovery anchors are `0.0789` for A2 gray and `0.1184`
for A2b no-image. The direction registered below is therefore informed rather
than a fully prospective cross-corpus hypothesis. No ViRL39K training outcome
has been observed.

The 3B ViRL39K blind-solvability audit is the primary basis for the M7
prediction. Its source/category heterogeneity and arm-specific base
reward-opportunity estimates are frozen in
`reports/blind_solvability_virl39k_sample_v1.json`. The audited 7B ViRL39K
result is corroborating evidence only and does not replace the 3B basis.

## Primary Within-Corpus Mechanism Prediction

Within ViRL39K, strata with higher baseline blind reward-opportunity `q_bar`
are expected to show larger blind-arm gains and recovery fractions.

Arms and conditions:
- A2 uses its own gray-condition base `q_i` values.
- A2b uses its own no-image-condition base `q_i` values.
- A3 uses its own fixed-caption-condition base `q_i` values.
- A1 is the real-image reference and is not called a blind arm.

Frozen stratification:
- The primary strata are the joint `(source, category)` labels already present
  in the frozen ViRL39K metadata.
- A stratum enters a rank statistic only when the frozen held-out evaluation
  set contains at least 30 items in that stratum. The threshold depends only on
  sample count, never on a model outcome.
- Every smaller mechanically valid stratum remains in the published per-stratum
  table and is labeled `descriptive-small-n`; it is not merged, discarded, or
  used in the rank statistic.
- Source-only and category-only tables are descriptive robustness views. They
  do not replace the registered joint-stratum analysis.

Quantities, separately for each blind arm `b` and eligible stratum `s`:
- `q_bar[b,s]` is the item mean of the frozen Jeffreys-smoothed base `q_i`
  estimates under arm `b`'s own information condition. It is an estimate of
  reward opportunity, not a directly observed latent.
- `gain[b,s]` is the mean across the two fixed M7 seeds of
  `Acc_final(step_final) - Acc_final(step_0)` on paired held-out items.
- `gain[A1,s]` is computed identically for the real-image reference.
- `recovery[b,s] = gain[b,s] / gain[A1,s]` only when `gain[A1,s] > 0` and is
  at least two paired standard errors above zero. Otherwise recovery is
  reported `undefined-unstable-denominator`; the stratum stays in the gain
  analysis but is omitted from the recovery rank statistic.

Registered association statistics:
- `rho_gain[b]`: tie-corrected Spearman association across eligible strata
  between `q_bar[b,s]` and `gain[b,s]`.
- `rho_recovery[b]`: tie-corrected Spearman association across strata with a
  stable A1 denominator between `q_bar[b,s]` and `recovery[b,s]`.
- The directional prediction is `rho_gain[b] > 0` and
  `rho_recovery[b] > 0`; a nonpositive estimate is reported as a failed
  direction. No minimum effect magnitude is implied.

Uncertainty:
- Use 5,000 item-bootstrap draws.
- In each draw, resample held-out items with replacement within every frozen
  joint stratum, preserving item identity across step 0, all arms, and both
  seeds.
- Recompute stratum `q_bar`, seed-averaged gains, A1 denominator stability,
  recoveries, and both tie-corrected Spearman statistics in every draw.
- Report percentile 95% intervals, the number of eligible strata, the number
  of recovery strata, and the count of draws where a rank statistic is
  undefined. Undefined draws are not replaced with zero; if more than 5% are
  undefined, the corresponding interval is labeled unstable.
- Bootstrap RNG seed is `20260716`, with deterministic statistic/arm labels
  hashed into independent streams. Seed-to-seed dispersion is also reported
  descriptively and is not replaced by item-bootstrap uncertainty.

## Secondary Cross-Corpus Directional Prediction

Aggregate blind-arm recovery on ViRL39K is expected to be greater than the
completed Geometry3K seed-1 anchors:

| Arm | Geometry3K seed-1 recovery anchor |
| --- | ---: |
| A2 gray | 0.0789 |
| A2b no-image | 0.1184 |

For each arm, compute the ViRL39K aggregate recovery from the two-seed mean
blind gain divided by the two-seed mean A1 gain, conditional on the same stable
A1-denominator rule. Use 5,000 item-paired bootstrap draws across the frozen
held-out corpus, preserving item identity across arms and seeds. Report the
ViRL recovery, its 95% interval, and the difference from the fixed Geometry3K
anchor. The registered direction is simply greater than the anchor; no
numeric minimum difference and no use of `substantially` are authorized. A
failed direction is reported as such.

## Readout Discipline

- Corpus aggregate, every joint stratum, and source-only/category-only
  descriptive tables are all published; a pooled-only readout is prohibited.
- A2/A2b/A3 results are never pooled into one generic blind arm.
- The informed Geometry3K comparison is labeled as such in every report and
  paper table.
- M10 support-sharpening language remains non-causal.
- Any irregularity is appended to the M7 deviations log before values are
  interpreted.

## Deviations Log

| Time UTC | Deviation | Reason | Effect on estimands | PI disposition |
| --- | --- | --- | --- | --- |
