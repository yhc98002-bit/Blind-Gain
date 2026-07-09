# GRPO Reward Parser Audit

Status:
- Local answer parser tests pass for the project parser in `src/rewards/answer_reward.py`.
- EasyR1 recovery run uses the upstream example reward function: `artifacts/repos/EasyR1/examples/reward_function/r1v.py:compute_score`.
- This audit is sufficient for recovery launch but not yet sufficient for headline reproduction claims.

Evidence:
- Test file: `tests/test_reward_parser.py`
- Local parser handles:
  - `<answer>...</answer>`
  - `\boxed{...}`
  - final-answer lines
  - numeric equivalence for dollars, commas, fractions, and percentages
- Previous test result: `10 passed` across reward and FlipTrack metric tests.

Known risk:
- EasyR1 `r1v.py` delegates mathematical equivalence to `mathruler`; the smoke log showed warnings for LaTeX macro substitution such as `\frac`.
- The recovery run should report parse/reward behavior from `experiment_log.jsonl`; if rewards are mostly zero, inspect generated samples before scaling.

Decision:
- Mark local reward parser audit as pass for Blind Gains utilities.
- Mark EasyR1 reward parser as recovery-usable but requiring sample-level audit before a long run.

Next actions:
- After `easyr1_geo3k_recovery30`, sample correct/incorrect reward cases from `generations.log`.
- Add tests for Geometry3K-specific answer formats if parse failures dominate.
