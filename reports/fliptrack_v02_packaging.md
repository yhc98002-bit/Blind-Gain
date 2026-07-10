# FlipTrack V0.2 Packaging and Leakage Linter

Status:
- P1.4 implementation and final-candidate lint are complete.
- The 900-pair R17 package has `status=true` for every enumerated linter check. Earlier package sections remain as calibration history.

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
- The original `data/fliptrack_v02/` decision is superseded by the R17 section below.
- Keep answers and template/source-side metadata in the private key; do not distribute the salt.
- Advance the actual package to P1.5 while P1.6 hardness scoring proceeds on the source manifest.

Next actions:
- Run grouped k-fold metadata/statistical/DINO attackers on this package.
- Finish real/gray/noise/caption model scoring and retain only templates meeting P1.6 acceptance.

## R8 Retained Candidate

Status:
- A new 700-pair package was built from the expanded document slice and the preregistered R7 geometry batch.
- All 12 linter checks pass. This candidate is not frozen because its artifact gate still fails on chart metadata.

Evidence:
- Selection config: `configs/data/fliptrack_v02r8_retained.json`.
- Selection record: `experiments/manifests/fliptrack_v02r8_selection.json`.
- Source manifest: `data/fliptrack_v02r8_retained_source_manifest.jsonl`, SHA256 `060ebef35a9527a7d8f8da67c59482ad06a95b417c723ee8a063c4d231a908b0`.
- Composition: chart 100, document 300, R7 geometry 300 pairs.
- Package run: `experiments/runs/fliptrack_v02_package_20260710T012454Z`, exit code 0.
- Release manifest: `data/fliptrack_v02r8_retained/manifest.jsonl`, SHA256 `983ba2517314b68c1ea4e9a5e10e807857c70c6d65c57f0e72829d95a91ad4e1`.
- Linter output: `reports/fliptrack_v02r8_lint.json`, SHA256 `8513b670ecdbac8f55decb5bc4a096cf89b5af98555f0a16becbea5e82c0160c`.

| Check | R8 result |
| --- | ---: |
| Pairs | 700 |
| Members | 1,400 |
| Opaque IDs/paths | pass |
| Equal mtimes / clean PNG chunks | pass |
| Truthful masks / distinguishable answers | pass |
| Member order | 364 `ab`, 336 `ba` |
| Chart side-size KS | 0.0600 |
| Document side-size KS | 0.0400 |
| Geometry side-size KS | 0.0433 |

Decision:
- Preserve R8 as an immutable failed-gate candidate.
- Expand chart with the independent R9 seed batch before constructing the next package.

## R17 Three-Family Candidate

Status:
- Packaging and all 12 leakage-linter checks pass on the scientifically selected 900-pair candidate.
- Artifact-attack robustness remains a separate P1.5 computation and is not implied by this result.

Evidence:
- Selection config: `configs/data/fliptrack_v02r17_retained.json`.
- Selection record: `experiments/manifests/fliptrack_v02r17_selection.json`.
- Source manifest: `data/fliptrack_v02r17_retained_source_manifest.jsonl`, SHA256 `c7c92384673ec5ef352e1590895172edcd485dbf361a99b6633110296ef81007`.
- Composition: document 300, R10 geometry 300, R16 chart 300.
- Package run: `experiments/runs/fliptrack_v02_package_20260710T121644Z`, exit code 0.
- Release manifest: `data/fliptrack_v02r17_retained/manifest.jsonl`, SHA256 `bda74d29260a9ac5d9308d2ce6e387259de26b42840a6843e733af0d98e59991`.
- Machine linter: `reports/fliptrack_v02r17_lint.json`, SHA256 `09d60384863d7121b0f5ca8c8ae36d4e8f23e5108494154a30c7ff1cb37b5ef0`.
- Private key and salt: `.private/fliptrack_v02r17_key.jsonl` and `.private/fliptrack_v02r17_salt.bin`; both remain outside the release and Git.

| Check | R17 result |
| --- | ---: |
| Pairs / members | 900 / 1,800 |
| Asset files | 2,700 |
| Opaque IDs and paths | pass |
| One fixed mtime / clean PNG chunks | pass |
| Truthful masks / distinguishable answers | pass |
| Member order | 428 `ab`, 472 `ba` |
| Geometry side-size KS | 0.0200 |
| Document side-size KS | 0.0400 |
| Chart side-size KS | 0.0267 |

Decision:
- Use R17 as the sole current freeze candidate and preserve prior packages as failed or superseded calibration artifacts.
- Do not request final human audit until the R17 grouped artifact attacker finishes.

Next actions:
- Run frequency/statistical, metadata, and DINOv2 attackers on R17 without changing thresholds.
- Generate final content-hash caption stores from the re-encoded R17 images.
