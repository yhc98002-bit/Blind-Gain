# Seed-1 Visual-Evidence Ranking Context V1

Status:
- Complete as a post-seed-1, prospectively registered diagnostic. It is not an
  endpoint from the original pilot preregistration.
- The frozen nine-cell matrix, input-integrity audit, result builder audit, and
  independent raw-score recomputation audit all pass.
- No automatic B1/B2/B3 branch is assigned because no equivalence threshold was
  registered on the log-probability-margin scale.

Evidence:
- Geometry primary, step 100 versus base, real minus no-image: paired-margin
  effect `+0.150142`, paired-bootstrap 95% CI `[+0.144849, +0.155388]`, 600
  pairs.
- Gray robustness gives the same registered geometry estimate and interval.
- The descriptive step-60 geometry effect is `+0.089137`
  `[+0.085755, +0.092493]` under both blind comparators.
- Geometry secondary changes at step 100 are pair success `+0.000000`,
  candidate-set top-1 `+0.008333`, and MRR `+0.007630` against no-image
  (`+0.008497` MRR against gray).
- Geometry real-image pair success was already `0.906667` at base and remains
  `0.906667` at steps 60 and 100. Candidate-set top-1 moves from `0.468333` to
  `0.476667` by step 100.
- `cued chart point-value reading`, secondary: step-100 paired-margin effect
  `+0.072163` `[+0.068532, +0.075720]`; pair-success `+0.010000`; top-1
  `+0.060000`; MRR `+0.031168` against no-image.
- Document/OCR, secondary: step-100 paired-margin effect `+0.200701`
  `[+0.194617, +0.206893]`, while pair success and top-1 remain saturated at
  `1.000000` in the real-image cells.
- In gray/no-image cells, A and B expose the same non-informative visual/text
  input. For the two counterfactual answers, the two side margins are therefore
  exact opposites and their paired mean is zero by construction. The primary
  difference-in-differences consequently isolates the checkpoint change in the
  real-image paired margin.
- Builder audit: `pass`, all nine cells have 1,200 rows and the frozen scorer
  version is exact.
- Independent audit: `pass`; zero stored-metric mismatches, zero effect-summary
  mismatches, and exact reconstruction of all side margins, strict pair success,
  ranks, top-1, MRR, and bootstrap intervals.
- Input audit: `pass`; 1,200 pair identities, 2,400 image hashes, and all three
  model index/shard inventories verified without opening performance values.

Interpretation boundary:
- The primary score separation increased under informative images. This is
  evidence of stronger visual-evidence score margins under the frozen candidate
  contract.
- The strict geometry pair-success outcome is unchanged and candidate top-1
  moves only 0.83 percentage points. The result therefore does not show a broad
  conversion of score-margin changes into different discrete candidate choices.
- B1's joint pattern is not obtained on the primary margin because that margin is
  positive rather than flat; its output/decision concern remains relevant to the
  nearly unchanged discrete geometry outcomes.
- B2's chart-only pattern is not obtained because geometry also has a positive
  primary margin effect.
- The positive geometry margin is directionally compatible with B3, but the
  unchanged pair-success result materially qualifies that comparison. Any claim
  that the end-to-end dissociation contains measurement cancellation must remain
  explicitly partial and tied to the frozen margin statistic.
- Candidate-answer ranking is not a direct perception measure and does not, by
  itself, establish an internal perceptual mechanism.

Decision:
- Report the audited estimates and the margin-versus-decision distinction.
- Leave the formal B1/B2/B3 assignment to the PIs; no post-hoc margin SESOI is
  introduced.
- Keep geometry as the headline construct. Chart remains secondary under the
  exact human-facing label `cued chart point-value reading`.

Artifacts:
- Results: `reports/seed1_visual_evidence_ranking_results_v1.{md,json}`.
- Input provenance: `reports/seed1_visual_evidence_ranking_input_integrity_v1.{md,json}`.
- Builder audit: `reports/seed1_visual_evidence_ranking_builder_audit_v1.json`.
- Independent audit: `reports/seed1_visual_evidence_ranking_audit_v1.json`.
- Frozen registration: `docs/registered_seed1_visual_evidence_ranking_v1.md`.
