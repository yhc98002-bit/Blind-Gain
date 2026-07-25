# B1 renderable geometry track — declared calibration batch (v1)

One declared 100-pair batch (docs/EXPERIMENT_TODO.md Track B), scored on
the real, blind (no-image), and question-blind-caption cells with the
frozen base model. One shot; no acceptance iteration. Facts only.

- Batch SHA-256: `b5f01945bf5e1b36…`
- Overall pair-correct: real 0.330, blind 0.030, caption 0.040

## Pair-correct by intervention type

| intervention | pairs | real pair | real member | blind pair | blind member | caption pair | caption member |
|---|---|---|---|---|---|---|---|
| fact_read | 20 | 0.600 | 0.700 | 0.000 | 0.200 | 0.000 | 0.125 |
| chained_premise | 20 | 0.000 | 0.150 | 0.000 | 0.350 | 0.050 | 0.325 |
| binding_swap | 16 | 0.188 | 0.375 | 0.000 | 0.188 | 0.062 | 0.250 |
| distractor_only | 16 | 0.438 | 0.438 | 0.125 | 0.125 | 0.062 | 0.125 |
| style_twin | 14 | 0.643 | 0.750 | 0.071 | 0.071 | 0.071 | 0.179 |
| prior_conflict | 14 | 0.143 | 0.429 | 0.000 | 0.107 | 0.000 | 0.250 |

Scoring note: consistency pairs (distractor_only, style_twin) are scored
single-gold — the frozen FlipTrack member scorer's two-gold ambiguity
guard structurally fails equal-gold items (a correct answer matches both
golds and is treated as ambiguous). Flip pairs keep the frozen scorer.

Per-item single-sample blind-solvability estimates are in the machine JSON
(`blind_solvability_qhat_single_sample`). Premise probes for the chained
items are stored in the batch metadata for future scoring; they are not
part of the declared three-cell calibration.
