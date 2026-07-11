# EasyR1 Image-Grid Consistency Audit V1

Status:
- Pass for the preprocessing implementation audit. The repaired real/gray/noise payload contract has zero predicted Qwen2.5-VL prompt-token versus worker-feature grid mismatches on the frozen 1,288-row pilot corpus.
- This implementation check does not pass L3; the five-step reward-plumbing smoke must still complete.

Evidence:
- Immutable run: `experiments/runs/easyr1_image_grid_audit_login_20260711T114727Z`.
- Machine artifact: `experiments/runs/easyr1_image_grid_audit_login_20260711T114727Z/audit.json` (`status=pass`).
- Data SHA256: `f3d88dd1e52ccef833f266880e487eef252193f774c1076f7dfbccd180b450e6`.
- Old double-resize path: 4/1,288 mismatches (0.003106); feature deltas are +14 for three rows and +12 for one row.
- Fixed single-source path: 0/1,288 mismatches.
- Frozen row 7 maps the first resize to 686x381 and the second resize to 687x381. Qwen2.5-VL maps those to 336 tokens and 350 features respectively, reproducing the failed smoke's 14-feature delta.
- Adversarial fixture: `tests/test_image_grid_consistency.py`; the independent 20x36 case reproduces the same +14 drift.
- Reproducible EasyR1 patch: `docs/easyr1_multimodal_grid_patch.diff`.

Problems:
- The audit models the exact EasyR1 area resize and Qwen2.5-VL smart-grid arithmetic. End-to-end FSDP/vLLM agreement remains the responsibility of the active smoke.
- Gray and noise preserve source dimensions by design, so they share the same grid result as real images; this audit does not assess their pixel semantics.

Decision:
- Keep `min_pixels=262144` and `max_pixels=4194304` unchanged.
- Derive both prompt-processor pixels and worker payloads from the same unresized real or deterministic sibling image, with each consumer applying the area resize exactly once.

Next actions:
- Require the active repaired smoke to pass the formerly failing first log-probability phase and complete five optimizer steps.
- Run the shadow-log audit before publishing `reports/pilot_reward_spec.md` or changing the L3 ledger status.
