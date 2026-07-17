# Seed-1 Visual-Evidence Ranking Readiness V1

Status:
- The post-seed-1 prospective diagnostic is specified and its candidate registry is
  frozen before inference.
- This is not part of the original pilot preregistration and does not reopen M2.
- Full inference and the result report are pending.

Evidence:
- Registration: `docs/registered_seed1_visual_evidence_ranking_v1.md`.
- Config: `configs/eval/seed1_visual_evidence_ranking_v1.json`.
  SHA256 `6abd53bbf7742167aaf672dcc74633465f7d9378220067c651ce4575375b67bf`.
- Candidate registry: `data/fliptrack_r19_visual_evidence_candidates_v1.jsonl`,
  1,200 pairs, SHA256
  `fa9456941a730e174b1ed4bb4caefc151778e3f1adc0ca77db941955a4215f81`.
- Candidate metadata: `reports/fliptrack_r19_visual_evidence_candidate_registry_v1.json`.
- Candidate counts: document 16, geometry 14, chart 9 per pair.
- Focused adversarial fixtures cover exact span alignment, length normalization,
  strict two-sided pair success, conservative ties, deterministic distractors,
  mathematical equivalence, unit-changing negatives, and pair-identity-locked
  difference-in-differences.
- Verification on `an12`: `11 passed in 2.09s`; Python compilation, JSON parsing,
  shell syntax, and `git diff --check` also completed without error.

Problems:
- No margin-scale SESOI was provided. Branch estimates can be reported, but an
  automatic `flat`/branch declaration would require inventing a threshold and is
  therefore disabled.

Decision:
- Geometry/no-image step-100 difference-in-differences is the single primary
  diagnostic estimate. Gray, step 60, top-1, MRR, chart, and document are secondary
  or robustness analyses.
- Reports must use `visual-evidence ranking` or `candidate-answer ranking`; they may
  not say `perception improved`.

Next actions:
- Commit the frozen registry, config, implementation, tests, and registration.
- Run a small post-registration GPU smoke without opening scientific values.
- Launch the nine immutable base/step-60/step-100 by real/no-image/gray cells and
  publish the audited result bundle.
