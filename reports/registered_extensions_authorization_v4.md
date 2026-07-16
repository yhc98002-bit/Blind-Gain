# Registered Extensions Authorization V4

Status:
- The PI ruling dated 2026-07-16 is transcribed into
  `docs/registered_extensions_v1.md`.
- The canonical line `Registration state: merged-at-HEAD; merge is sign-off.`
  is present.
- M5 is authorized after the registered restore-and-resume integrity check.
- M6, M7, and M9 retain their independent data, reward, and readiness
  preconditions; no downstream scientific gate is declared here.

Evidence:
- PI ruling source: `docs/MAIN_PHASE_RULING_20260716.md`, SHA256
  `c4aea3f909852289517be9c4ea75a20ed3b445822295b7cf99558328d8accee0`.
- Active registration: `docs/registered_extensions_v1.md`, SHA256
  `3ee4bad0734c9f155d56dda2eb21200ea05207d17aee83472d6428c23228cadf`.
- M8 report: `reports/blind_solvability_virl39k_7b_sample_v1.md`, SHA256
  `ac97650d0e0eb49838597cfab35b951207494c7851d169116573299ff3f92e73`.
- M8 machine audit: all 15 registered checks true, zero score-recomputation
  mismatches; SHA256
  `1487005f26fcd49f31e5de224f429cee022bfda66af4b1b240bf7d99fc587981`.

Authorization checks:
| Check | Result |
| --- | --- |
| Geometry-primary step-400 contrast defined | pass |
| FLAT/RISING/FALLING/INDETERMINATE rules exact | pass |
| Fixed terminal step 400 and no rerun rule | pass |
| Benchmark context condition recorded | pass |
| Overall/per-category/blind-floor secondaries recorded | pass |
| Single-primary/no-multiplicity rule recorded | pass |
| Exact merged-at-HEAD marker present | pass |
| M8-derived 7B arm rule recorded | pass |
| A2-gray retained by rule rather than discretion | pass |
| M8 sample/store hashes and coverage recorded | pass |
| ViRL source/category stratification amendment present | pass |

Decision:
- Run the M5 one-step restore integrity check. Launch the fixed step-400
  continuation only if that check passes; otherwise use the registered fresh-run
  fallback and disclose it.
- The 7B flagship arm set is A1/A2/A2b/A3, three seeds each. The trigger is the
  precommitted M8 gray-versus-no-image rule: 0.2456 versus 0.1824 with
  non-overlapping confidence intervals.
- Do not treat the 4,096-item M8 caption store as the future full training-subset
  store. That field remains explicitly pending until the training subset freezes.

Next actions:
- Commit this authorization and the four M8 reports in one consistency/ledger
  reconciliation commit.
- Bind the resulting HEAD in the M5 launch manifest.
