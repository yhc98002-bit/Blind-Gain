# ViRL39K vs Layer-1 Decontamination V1

Status:
- `pass` for the machine conjunction below.
- This is a data-readiness audit, not a PI scientific-gate decision and not M7
  training authorization.

Evidence:
- Source: 38,870 ViRL39K items / 42,908 image records.
- Layer-1 evaluation side: 12,683 image records across
  all seven registered suites.
- Automatic filtering marks 9,182 image records
  spanning 9,114 whole items as conservative contamination
  candidates; 29,756 items remain.
- Filter manifest SHA256: `bf32d808ba7cc46d557dfadfb253451b6540e131bac1725e731c90bea169c797`.
- Frozen dataset SHA256: `d4e0ef8733e0ff4e8604d5e7b15e7206f8e4eb3745ef16e523cdf26eb5c9c4a0`.

| Layer-1 suite | Image records |
| --- | ---: |
| blink | 3,675 |
| hallusionbench | 1,129 |
| mathverse | 3,940 |
| mathvista | 999 |
| mmmu | 1,140 |
| mmstar | 1,500 |
| mmvp | 300 |

Audit:
| Check | Result |
| --- | --- |
| `record_build_pass` | `pass` |
| `source_item_count_exact` | `pass` |
| `source_record_count_exact` | `pass` |
| `seven_suite_record_counts_exact` | `pass` |
| `filter_complete` | `pass` |
| `no_pending_layers` | `pass` |
| `all_registered_layers_complete` | `pass` |
| `frozen_thresholds_exact` | `pass` |
| `filter_source_count_exact` | `pass` |
| `freeze_pass` | `pass` |
| `freeze_uses_exact_filter` | `pass` |
| `whole_item_accounting_exact` | `pass` |
| `frozen_outputs_hashed` | `pass` |
| `caption_image_index_exact` | `pass` |
| `conservative_candidate_language` | `pass` |

Problems:
- Inspect-band records are retained because calibrated inspect thresholds admit
  false positives. They are not confirmed duplicates.
- This report does not establish full 3B/7B caption-store coverage or matched
  training-config readiness.

Decision:
- Freeze by whole item: one automatic-remove image record removes all images and
  the question for that ViRL39K item.
- Preserve source/category strata for the registered H-mixed analysis.

Next actions:
- Generate and audit the full-subset 3B and 7B own-caption stores.
- Fill registered M7/M9 config fields and keep launchers fail-closed until those
  hashes are committed.
