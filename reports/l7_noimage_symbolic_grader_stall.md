# L7 No-Image Symbolic-Grader Stall

Status:
- The first no-image L7 run is a preserved failed attempt, not a completed condition; its launcher finalized with exit code -15 at `2026-07-11T15:35:02Z` after the targeted termination.
- Its durable output prefix contains 100 of 1,889 registered rows.
- A bounded symbolic-grader guard and adversarial regression fixtures are implemented locally; a replacement run remains required.

Evidence:
- Run: `experiments/runs/blind_solvability_v2_geo3k_filtered_v2_none_an29_20260711T141514Z`.
- Placement: one TP1 replica on `an29` GPU 7; the job is not split across nodes.
- The per-item output stopped changing at `2026-07-11T14:25:42Z` after row 100.
- At `2026-07-11T15:28Z`, PID 2471116 was alive for 1:13:35, used approximately one full CPU core, reserved 61,296 MiB on GPU 7, and GPU utilization was 0 percent.
- The log contains no traceback after the row-100 progress record. An attempted read-only `strace` attachment was rejected by the host ptrace policy.
- Generation is followed synchronously by `score_item_pilot`; that path calls MathRuler/SymPy for the pilot verdict and again through the native-r1v shadow. MathRuler itself notes that SymPy can hang. The observed CPU-only state is therefore consistent with, but does not directly prove, a symbolic-grading stall.
- Regression command: `PYTHONPATH=. .venv/bin/pytest -q tests/test_pilot_reward.py tests/test_blind_solvability_v2.py`.
- Regression result: 29 passed in 7.56 seconds.

Problems:
- The pre-fix reward path had no deadline around either symbolic grader call, so one pathological generated answer could prevent an entire condition from completing.
- The first 100 rows were scored before the guard existed. L7's final recomputation audit must rescore all retained responses with the guarded implementation and report mismatches.

Decision:
- Preserve the failed run and its 100-row prefix; do not overwrite it.
- Bound each MathRuler and native-r1v symbolic call at 5 seconds. A timeout follows the existing exception policy: MathRuler receives no accuracy credit, canonical-v2 remains a shadow, and the reason is logged. A native-shadow timeout cannot change the optimized reward and is exposed through `native_r1v_shadow_valid=0`.
- Keep the scientific reward identifier `pilot-reward-v1`: finite-call verdicts and the registered precedence rule are unchanged. Pin the runtime deadline explicitly in every pilot config and by git/config hash.
- Restart no-image in a new immutable run from the validated 100-row prefix after terminating the stalled process. The final L7 audit must verify uniform recomputation across all five conditions.

Next actions:
- Launch a new TP1 no-image run on a single free GPU with `--resume-from` pointing to the preserved prefix.
- Run a replacement five-step reward-plumbing smoke before L12 because the pilot configs now pin the timeout argument.
