# Seed-1 Visual-Evidence Ranking Analysis Template V1

Status:
- Complete before any candidate score or scientific result was opened.
- The frozen scoring config, primary estimand, candidate sets, and bootstrap contract
  are unchanged.

Evidence:
- The lifecycle queue retained `performance_values_opened=false` when this template
  was finalized.
- The result builder now renders all 27 absolute model/condition/template cells for
  paired margin, pair success, candidate top-1, and candidate MRR.
- It also renders the already frozen raw-sum score as a length-handling robustness
  difference-in-differences. Mean-token log probability remains the only primary
  candidate score.
- The independent auditor reconstructs both side margins, strict pair success,
  conservative tie ranks, top-1, MRR, and raw-sum robustness from candidate scores,
  then independently recomputes every published effect and bootstrap interval.
- Focused suite: `13 passed in 2.32s` on an12.

Problems:
- These extra tables increase reporting completeness but do not create additional
  primary endpoints or an automatic B1/B2/B3 verdict.

Decision:
- Keep geometry/no-image step-100 paired-margin difference-in-differences as the
  single primary diagnostic estimate.

Next actions:
- Finalize only after all nine immutable cells complete, then run the separate raw-
  score recomputation audit before updating the diagnostic ledger.
