# Support-Sharpening Registry V3

Status:
- The PI-fixed follow-up seed rule is registered and executable.
- Candidate files remain the immutable 47/8/7/18 seed-1 sets from V2.
- Registration state: merged-at-HEAD; merge is sign-off.
- No follow-up response was inspected before this rule was written.

Registered draw rule:
- Draw indices are exactly `j = 16,...,79`.
- Per-draw seed is exactly `20260716 + j`, yielding 64 distinct seeds
  `20260732,...,20260795`.
- Every call requests `n=1`, temperature `1.0`, top-p `1.0`, and 2,048 maximum
  tokens from the frozen Qwen2.5-VL-3B base model.
- The model, arm-specific condition, prompt, parser, pilot reward, image/caption
  inputs, and answer contract match the original 16-sample audit.
- Each draw writes one explicit `(item, draw_index, seed, response, score)` row.
- Coincidentally identical text responses are retained as separate stochastic
  draws and are never treated as a seed-stream failure.
- The original `n=16`, seed `20260710` sampling call is not reused.

Evidence:
- Machine contract: `configs/eval/support_sharpening_v2.json`.
- Candidate selection and posterior implementation:
  `src/analysis/support_sharpening.py`.
- Execution command: `scripts/run_support_sharpening_followup.py` through
  `scripts/launch_support_sharpening_followup.sh`.
- Capacity queue: `scripts/launch_support_sharpening_queue.sh` watches only
  an12 GPUs 5-6 after their current M11 cells release them. It does not claim
  an29 capacity reserved for seed 2 and the M11 repair, and it never opens
  response values.
- Regression fixture: `tests/test_support_sharpening.py` proves 64 distinct
  registered seeds, 64 `n=1` calls, no original seed/call reuse, and retention
  of duplicate response text.

Readout:
- Combine the original 16 pilot-reward outcomes with the new 64 outcomes.
- Zero successes in all 80 is labeled
  `high-confidence support-expansion candidate` and receives a Jeffreys 95%
  posterior interval.
- Any follow-up success is labeled
  `observed in support-sharpening samples`.
- Allowed language remains `mass sharpening within observed support` and
  `not observed in the base K-sample set`; causal capability-creation language
  is prohibited.

Problems:
- None in the seed specification. GPU execution and immutable output audits
  remain pending until the four follow-up runs complete.

Decision:
- Execute the four arm-specific candidate sets under this exact rule. Do not
  alter seeds or deduplicate outputs after observing responses.
