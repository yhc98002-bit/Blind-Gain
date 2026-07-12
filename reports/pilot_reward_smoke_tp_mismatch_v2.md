# Pilot Reward Smoke Placement Mismatch V2

Status:
- `fail`. The hardened v5 audit independently rejects the historical five-step smoke's placement and config provenance.
- L3 remains `blocked`; no L12 or L13 dependency may treat the old smoke as valid completion evidence.

Evidence:
- Historical smoke: `experiments/runs/pilot_reward_smoke_an29_20260711T165700Z`.
- Machine re-audit: `reports/pilot_reward_smoke_historical_reaudit_v5.json` (`status=fail`).
- Machine re-audit SHA256: `2e029125b941c7b93e5e8d5fa8ad136014b56830b48d796246f8ccb739cddaf6`.
- Reward and partition checks remain valid: all 13,401 rows, reward identities, guard stamps, native shadows, step markers, and validation ordering pass.
- Placement failures are exact: the config is not a run-local immutable snapshot; its current hash does not match the historical manifest; the manifest's replica count is not derived; runtime log TP is `[2]`, not TP1; and the checkpoint path used the shared future-pilot namespace.
- The v5 audit obtains runtime TP values from the immutable log rather than trusting manifest prose.
- Focused reward and placement suite: 32 tests passed, including the historical TP2 adversarial fixture.

Problems:
- The old v4 audit tested reward plumbing and step completion but did not cross-check effective YAML, runtime TP, or placement fields.
- The historical manifest points to a mutable repository config, so later TP1 edits could otherwise conceal the TP2 runtime setting.

Decision:
- Preserve the original v3 machine audit and v2 reward report as superseded historical artifacts.
- Require every replacement audit to pass `blind-gains.pilot-reward-smoke-audit.v5`, including the nested placement audit.
- Require a read-only `effective_config.yaml` inside the immutable run directory, matching `base_config_hash`.
- Derive TP width and rollout replica count from that snapshot and confirm runtime TP from the log.
- Keep the replacement final-save payload in `checkpoints/smoke/<run_id>`, then checksum-delete it after audit.

Next actions:
- Run the replacement five-step TP1 smoke on four free GPUs when L9 releases its current allocation.
- Publish `reports/pilot_reward_spec_v3.md` and a new machine audit only if every v5 sub-check passes.
