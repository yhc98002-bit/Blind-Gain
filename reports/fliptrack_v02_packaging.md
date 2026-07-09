# FlipTrack V0.2 Packaging and Leakage Linter

Status:
- P1.4 implementation and actual-package lint are complete.
- The 600-pair V0.2 package has `status=true` for every enumerated linter check. This is an engineering task result, not a PI Gate 2 decision.

Evidence:
- Source manifest: `data/fliptrack_v02_source_manifest.jsonl` (600 pairs; SHA256 `720f755c3e6ba4feae9f1493fbb4ed42bf90fba52d1fccffa60babda04a86942`).
- Opaque release manifest: `data/fliptrack_v02/manifest.jsonl` (SHA256 `2437a25ee26f45543a4b84654d74b689d320b38f8cf70eba77b7c3a7dfab10ba`).
- Private answer key: `.private/fliptrack_v02_key.jsonl`; salt: `.private/fliptrack_v02_salt.bin`. Both are outside the release directory and ignored by Git.
- Run: `experiments/runs/fliptrack_v02_package_20260709T222032Z` on login node `ln207`; exit code 0.
- Machine linter output: `reports/fliptrack_v02_lint.json`.
- Tests: `tests/test_manifest_linter.py`, including a leaky filename/PNG metadata/mtime/mask fixture and the required `7` versus `7.0` rejection.

| Check | Result |
| --- | --- |
| Pairs | 600 |
| Asset files after content deduplication | 1,531 |
| Opaque unique IDs and filenames | pass |
| Uniform, non-leaky paths | pass |
| Equalized mtimes | pass |
| PNG ancillary chunks absent | pass |
| Within-pair dimensions equal | pass |
| Pixel changes outside masks | 0 |
| Answer cross-matches | 0 |
| Randomized member order | 303 `ab`, 297 `ba` |
| Gross side file-size separation | none |

Per-template file-size KS:
| Template | KS | p-value | Gross |
| --- | ---: | ---: | --- |
| `coordinate_slope_v02` | 0.12 | 0.4695 | no |
| `dense_table_code_v01` | 0.09 | 0.8154 | no |
| `indexed_symbol_grid_v02` | 0.04 | 1.0000 | no |
| `parallel_angle_marker_v02` | 0.11 | 0.5830 | no |
| `starred_series_value_v02` | 0.07 | 0.9684 | no |
| `triangle_missing_angle_v02` | 0.14 | 0.2819 | no |

Problems:
- The historical V0.1 dry run failed mask truthfulness on exactly 100/100 chart pairs, confirming the old per-member RNG defect. V0.2 fixes this with pair-seeded shared content and exact pixel-difference masks.
- Passing this linter does not establish learned-feature artifact robustness; P1.5 DINO/statistical attackers remain required.

Decision:
- Use `data/fliptrack_v02/` as the only candidate release package.
- Keep answers and template/source-side metadata in the private key; do not distribute the salt.
- Advance the actual package to P1.5 while P1.6 hardness scoring proceeds on the source manifest.

Next actions:
- Run grouped k-fold metadata/statistical/DINO attackers on this package.
- Finish real/gray/noise/caption model scoring and retain only templates meeting P1.6 acceptance.
