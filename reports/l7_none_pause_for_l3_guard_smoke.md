# L7 No-Image Pause for Guarded L3 Smoke

Status:
- `resume required`. The guarded L7 no-image condition was deliberately paused to release the fourth colocated GPU required by the replacement L3 reward-plumbing smoke.
- The pause is orchestration-only; no prompt, decoding, reward, parser, corpus, condition, seed, or model setting changed.

Evidence:
- Paused run: `experiments/runs/blind_solvability_v2_geo3k_filtered_v2_timeoutguard_none_an29_20260711T153747Z` on `an29` GPU 7, TP1, one replica.
- Targeted child PID 2647947 was terminated; the wrapper finalized `fail`, exit -15, at `2026-07-11T16:54:53Z`.
- Durable prefix: `experiments/runs/blind_solvability_v2_geo3k_filtered_v2_timeoutguard_none_an29_20260711T153747Z/per_item.jsonl`.
- Prefix rows: `1,104 / 1,889`, exactly aligned to batch size 4.
- Prefix SHA256: `01a630b768f1c3f1aef8171ea32003bb9755fc9687a1e2adaa3830b2774a1b2f`.
- `load_validated_v2_resume_prefix` accepts all 1,104 rows against the frozen filtered train plus untouched test corpus, no-image condition, seed 20260710, 2,048-token contract, canonical-v2, and pilot-reward-v1.
- L7 real, gray, and noise conditions are complete; caption remains active on `an12` GPU 6.

Problems:
- The symbolic-grader guard changed the pinned pilot config after the original L3 smoke. L3 cannot return to `pass` until a new five-step smoke proves the guarded reward path under the actual four-GPU pilot configuration.
- `an29` has exactly four project-usable GPUs after real completed; leaving no-image active would prevent the required single-node colocated smoke.

Decision:
- Preserve the failed paused run and immutable prefix; do not count it as a completed L7 condition.
- Use `an29` GPUs 1, 5, 6, and 7 for one synchronous EasyR1/GRPO smoke with TP1 workers and no cross-node rollout/training split.
- Resume no-image in a new immutable run through the validated `--resume-from` path after the smoke releases GPU 7.

Next actions:
- Launch and audit the guarded five-step L3 smoke.
- Resume no-image from the 1,104-row prefix and complete L7's five-condition recomputation audit.
