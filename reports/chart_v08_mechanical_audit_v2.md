# Chart V08 Mechanical Audit V2

Status:
- Mechanical renderer audit: `pass`.
- This closes CPU-side pair construction and diagnostic plumbing only.
- M12 remains incomplete until human legibility, model sensitivity, caption gates, attackers, and the one-shot confirmatory split are reported.
- The declared calibration pair images and answer keys were not edited.

Evidence:
- Machine audit: `reports/chart_v08_mechanical_audit_v2.json`.
- Source: `data/fliptrack_chart_v08_calibration_v1_manifest.jsonl` (`d90f3f13c1f3304669c8ca6c717ae58eaa7cfe4e785fab3bae8520e15065c292`).
- Explicit member-level diagnostic sidecar: `data/fliptrack_chart_v08_calibration_v1_diagnostics_v2.jsonl` (`18ccefd2be6efc0d10ff6c710e25e56c67fd2b65818872aa398f68941f12f800`).
- Pairs: `100`; templates: `{'chart_v08_legend_target_flip': 50, 'chart_v08_point_value_flip': 50}`.

Checks:
| Check | Result |
| --- | --- |
| `source_manifest_exact_expected_unique_pairs` | `true` |
| `two_subfamilies_exact_expected_count` | `true` |
| `source_images_hash_and_metadata_reconstruct` | `true` |
| `answers_and_pair_mechanics_exact` | `true` |
| `changed_region_masks_exact` | `true` |
| `no_answer_pointing_cues` | `true` |
| `difficulty_controls_only_crossings_and_granularity` | `true` |
| `dual_coding_distinct` | `true` |
| `normal_palette_cie76_at_least_25` | `true` |
| `severe_cvd_palette_cie76_at_least_15` | `true` |
| `member_specific_no_star_and_random_star_sidecars` | `true` |
| `random_star_is_answer_discordant` | `true` |

Color Accessibility:
- Palette separation is measured after severity-100 linear-RGB simulation; color remains supplementary to distinct line and marker coding.
| Vision mode | Minimum CIE76 |
| --- | ---: |
| normal | 26.4339 |
| protanopia | 20.7071 |
| deuteranopia | 18.0853 |
| tritanopia | 16.1750 |

Crossing Density:
- Member A fraction: min `0.4000`, mean `0.6818`, max `0.9500`.
- Member B fraction: min `0.4000`, mean `0.6738`, max `0.9333`.
- This measures crossings in the two segments adjacent to the queried x-coordinate; no answer-pointing cue is used as a difficulty control.

Decision:
- Score each no-star and randomized-star image against that member's original answer. Randomized targets are forced to imply a different answer.
- Keep the original calibration manifest immutable; consumers join the diagnostic sidecar by `pair_id`.
