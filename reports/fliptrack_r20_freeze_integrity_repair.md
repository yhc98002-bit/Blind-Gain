# FlipTrack R20 Freeze-Integrity Repair

Status:
- R20 outputs remain unchanged and are not regenerated.
- The freeze checker now verifies the exact historical metric implementation used in the R20 freeze instead of requiring the live scorer module to remain forever immutable.
- The two full-suite failures caused by this path-aliasing defect are repaired without changing any frozen hash.

Evidence:
- Frozen logical input: `src/eval/fliptrack_metrics.py`.
- Frozen SHA256: `935efc67d027a020a1e1e4dc011d1b1a41fb01ac63f6a8b1c17f3c05cfc3b655`.
- Historical source commit: `4058924530ee70b98a9d1ce3a6b448a8fe2baa70`.
- Dedicated byte-exact snapshot: `src/fliptrack/frozen_r20/fliptrack_metrics.py`.
- Current live scorer SHA256: `7812612c4b0fcbd24e2c20b1afc48cf33b7884efd3b9e2baaea368f42d28b446`; it changed later for optimized permutation-null computation.
- Before repair, the full suite reported 397 passes and exactly two failures, both from `verify_frozen_inputs` comparing the historical hash against the later live file.
- After repair, the targeted R20 tests pass 3/3 and the full repository suite passes 400/400 in 76.54 seconds.

Problems:
- A freeze declaration had been represented as a hash over a mutable working path. Legitimate post-freeze scorer maintenance therefore made the historical generator test fail even though R20 generation code, seeds, counts, and outputs were unchanged.
- Replacing the expected hash with the current hash would falsely rewrite the freeze and is explicitly rejected.

Decision:
- Keep the original logical key and expected hash in R20 metadata.
- Resolve only this changed logical input to a dedicated snapshot whose bytes match the recorded hash. Record the source commit in code and test it.
- Keep the live scorer as the maintained evaluation implementation; do not import or execute the frozen snapshot in new evaluations.

Next actions:
- Preserve this report with the R20 confirmatory package so future scorer changes cannot be mistaken for generator drift.
