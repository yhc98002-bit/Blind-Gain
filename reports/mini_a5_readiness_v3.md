# Mini-A5 Readiness V3

Status:
- `blocked`. Corpus, reward/grouping logic, matched configs, advantage
  equivalence, and step-0 reward statistics are complete. Catch-trial inputs,
  the merged exact registration marker, and a registered EasyR1 GPU plumbing
  smoke remain required before either M6 arm may take an optimizer step.
- No PI gate decision is made.

Evidence:
- Step-0 inference run:
  `experiments/runs/mini_a5_step0_qwen25vl3b_an12_20260716T183755Z`.
  It completed on an12 GPU7 with TP1, one replica, exit code 0, and
  `optimizer_steps=0`.
- Source run-manifest SHA256:
  `6b1dc6799f16460ae30d66b85e5b8f79098d3664c433e47ab62028834e0d6821`.
- Predictions: 1,920 rows; SHA256
  `5a796f7ea69cb7a1d40dcd8ec318cb3f872a0cfa5ee5e63d660e59297cd3e126`.
- Independent summary run:
  `experiments/runs/mini_a5_step0_summary_login_20260716T184555Z`.
- Machine summary: `reports/mini_a5_step0_reward_audit_v1.json`, SHA256
  `debc84d4ae0c22f44f43345fb3510033aea6b8bfee09ed71f6f768bbbe97107f`.
- Human-readable summary: `reports/mini_a5_step0_reward_audit_v1.md`, SHA256
  `bb179e3a2a881ecabaf44b5804162c33be168b4c7356eb12629f6b2a149dc7ff`.

Step-0 reward statistics:

| Scope | Reward | N | Hit rate | Population variance |
| --- | --- | ---: | ---: | ---: |
| Overall | CP unique pair outcome | 960 | 0.146875 | 0.125303 |
| Overall | member outcome | 1,920 | 0.252604 | 0.188795 |
| code matrix | CP unique pair outcome | 320 | 0.375000 | 0.234375 |
| code matrix | member outcome | 640 | 0.495313 | 0.249978 |
| labeled scatter | CP unique pair outcome | 320 | 0.053125 | 0.050303 |
| labeled scatter | member outcome | 640 | 0.184375 | 0.150381 |
| named trajectory | CP unique pair outcome | 320 | 0.012500 | 0.012344 |
| named trajectory | member outcome | 640 | 0.078125 | 0.072021 |

Audit checks:
- All 192 fixed pairs contain exactly A/B times five rollout identities.
- All 960 unique CP outcomes and 1,920 member outcomes are present.
- Independent recomputation has zero reward mismatches.
- Every decoding, model, parser, reward, prompt, and sample-manifest field has
  exactly one value across the artifact.
- Side-A member hit rate is 0.252083; side-B is 0.253125; A-minus-B is
  -0.001042. There is no material pair-order imbalance in this fixed sample.
- All 1,920 reward-disagreement reason codes are `none`.

Interpretation boundary:
- Overall CP reward is not zero or constant, so the registered exact product
  has observable base-model signal on this sample.
- Signal is strongly template-dependent. Named trajectory has only four joint
  successes in 320 unique outcomes. This is reported as a throughput/variance
  risk, not used to remove, replace, reweight, or regenerate the frozen
  template.
- No shaped-reward fallback is selected. Any future fallback still requires a
  preregistered PI-approved addendum under the standing rule.

Problems:
- The registered catch-trial stability set is not frozen yet.
- The exact config/corpus/step-0 hashes have not yet been merged into the final
  mini-A5 launch marker.
- The detached EasyR1 overlay has passed CPU/config tests but has not yet run a
  registered real-GPU generation -> batch reward -> advantage -> update smoke.

Decision:
- Preserve all three frozen templates and the exact product reward.
- Build and audit the held-out answer-preserving catch set next, then merge the
  exact registration marker. Only that marker may authorize the GPU smoke; the
  two 120-step arms remain fail-closed until the smoke passes.
