# M1 ViRL39K Audit Readiness

Status:
- The 4,096-item five-condition audit and independent machine audit are complete.
- M1 remains `blocked`: M0 has not merged, `reports/virl_fork_ruling.md` is intentionally absent, and no PI-confirmed fork row is recorded.
- This report is descriptive readiness evidence, not a fork ruling or gate declaration.

Evidence:
- Summary: `reports/blind_solvability_virl39k_sample_v1.md`, SHA256 `90889962d5927f7c1de4c53a8971963ebd22b1bc6eaf2224e73b3807a9fd25ab`.
- Machine summary: `reports/blind_solvability_virl39k_sample_v1.json`, SHA256 `55d9b585cce52962b1db07da75186e3bbf3544d4fbc04f5fc68997a6873dc`.
- Independent audit: `reports/blind_solvability_virl39k_sample_v1_audited.json`, SHA256 `e0f39f3e45579ba31de18e597c3861abac382a67676becc32c5bb2cec6442620`, `status=pass`.
- Audit report: `reports/blind_solvability_virl39k_sample_v1_audited.md`, SHA256 `cc8ba63acdbb43c728a32fea90b1371d6fdd7011e56b76c21d18127ab1b0206b`.
- Aggregation run: `experiments/runs/virl39k_blind_v1_summary_login_20260712T202352Z`; source commit `2de840e748bfb9be86c7f36f1248ab074751154e`; exit code 0.
- All 15 audit checks are true; each condition has exactly 4,096 unique frozen identities; score mismatches, missing images, and image-hash mismatches are all zero.

Overall base-model results:

| Condition | Greedy accuracy | Mean q_i | q_i 95% CI |
| --- | ---: | ---: | ---: |
| real | 0.2947 | 0.5115 | [0.5028, 0.5205] |
| gray | 0.2102 | 0.4188 | [0.4093, 0.4278] |
| noise | 0.2126 | 0.4251 | [0.4159, 0.4344] |
| no-image | 0.1624 | 0.4151 | [0.4065, 0.4237] |
| caption | 0.1868 | 0.4355 | [0.4267, 0.4443] |

Registered-fork diagnostics:
- Caption minus real mean q_i: `-0.0761`; caption is below real, but not near the Jeffreys floor.
- Gray minus no-image mean q_i: `+0.0037`; their aggregate reward-opportunity estimates are close.
- Gray minus no-image greedy accuracy: `+0.0479`; whether this is `material` is a registered-ruling decision, not inferred here without its criterion.
- Category q_i ranges are large: real `0.3483`, gray `0.2800`, noise `0.3040`, no-image `0.3104`, caption `0.4087`.
- These facts make the strong source/category heterogeneity row descriptively relevant, while also showing substantial zero-bit q. This sentence is not the fork ruling.

Problems:
- The mandatory fork is applied only after M0 merges. Selecting a row now would reverse the required ordering.
- Item-bootstrap intervals capture item uncertainty, not model-run variance.

Decision:
- Preserve all five-condition numbers and category tables without sealing or interpretation changes.
- After M0 merges, Richard and the PIs record the obtaining row in `reports/virl_fork_ruling.md`; only then can M1 pass.
