# Frozen Geometry3K Pilot Subset

Status:
- The pilot train subset is frozen as the original 2,101 Geometry3K train rows minus the union of Gate-2 Layer-1 and V4 train-vs-test conservative contamination candidates.
- The union removes 813 rows and retains 1,288 rows; the four pilot configs now read the same immutable local JSONL.
- The ID list, local dataset, provenance hashes, and distribution-shift summary are complete.

Evidence:
- Freeze run: `experiments/runs/freeze_geo3k_pilot_subset_login_20260711T105426Z`, exit code 0, git `a12047b`.
- Frozen ID list: `data/geo3k_pilot_filtered_ids.json`, SHA256 `8631d015ee8593669b46cc707b9fe1fb3690391520bccf416b64bbb2306ff7d1`.
- Training JSONL: `data/geo3k_pilot_filtered.jsonl`, SHA256 `f3d88dd1e52ccef833f266880e487eef252193f774c1076f7dfbccd180b450e6`.
- Machine manifest: `data/geo3k_pilot_filtered_manifest.json`, SHA256 `4e584262a50b2e8d21ee93f0c1d3f3b5275cd24df693511493d36492d321b24a`.
- Gate-2 Layer-1 filter: 463 candidates; train-vs-test V4 filter: 498 candidates; intersection: 148; union: 813.
- Base-difficulty proxy: existing 3B real-image 16-sample audit at 512 tokens, `experiments/runs/blind_solvability_geo3k_real_an12_20260710T074916Z/per_item.jsonl`. L7 will replace this proxy with the registered 2,048-token pilot contract.

Derived category shift:
| Value | Original n (%) | Filtered n (%) | Delta pp |
| --- | ---: | ---: | ---: |
| `angle_lines` | 411 (19.56) | 228 (17.70) | -1.86 |
| `area_volume` | 126 (6.00) | 116 (9.01) | +3.01 |
| `circle_arc_tangent` | 176 (8.38) | 134 (10.40) | +2.03 |
| `coordinate_geometry` | 2 (0.10) | 0 (0.00) | -0.10 |
| `length_ratio_similarity` | 57 (2.71) | 44 (3.42) | +0.70 |
| `other` | 441 (20.99) | 251 (19.49) | -1.50 |
| `quadrilateral_polygon` | 324 (15.42) | 192 (14.91) | -0.51 |
| `triangle_trigonometry` | 202 (9.61) | 114 (8.85) | -0.76 |
| `underspecified_visual` | 362 (17.23) | 209 (16.23) | -1.00 |

Answer-type shift:
| Value | Original n (%) | Filtered n (%) | Delta pp |
| --- | ---: | ---: | ---: |
| `decimal` | 410 (19.51) | 283 (21.97) | +2.46 |
| `expression_or_text` | 163 (7.76) | 97 (7.53) | -0.23 |
| `fraction` | 62 (2.95) | 31 (2.41) | -0.54 |
| `integer` | 1,463 (69.63) | 875 (67.93) | -1.70 |
| `other` | 3 (0.14) | 2 (0.16) | +0.01 |

Question length and base difficulty:
| Measure | Original | Filtered | Change |
| --- | ---: | ---: | ---: |
| Mean question tokens | 10.249 | 10.188 | -0.061 |
| Median question tokens | 9 | 9 | 0 |
| Base greedy accuracy | 0.1080 | 0.1025 | -0.0056 |
| Mean sampled correctness | 0.0549 | 0.0495 | -0.0054 |
| Sampled correctness exactly zero | 66.49% | 68.94% | +2.45 pp |
| Sampled correctness in [0.25, 0.75) | 7.28% | 6.29% | -0.99 pp |

Problems:
- `hiyouga/geometry3k` exposes no source category field. The category table is a deterministic question-text taxonomy and is explicitly a proxy; image-only generic questions remain `underspecified_visual`.
- Filtering removes every row in the two-row `coordinate_geometry` proxy cell. This cell is too small for a stable category claim and remains visible rather than pooled into another class.
- The base-difficulty rows use the earlier 512-token canonical-v1 audit, not the L7 pilot reward/2,048-token contract.
- Removed rows are conservative contamination candidates, never confirmed duplicates.

Decision:
- Freeze the ID and dataset hashes above for L3, L4, L7, L12, and L13.
- Keep the 1,288-row corpus unchanged across A1, A2, A2b, and A3; only `image_condition` may differ.
- Do not silently reintroduce inspect-only removals or regenerate the list after preregistration.

Next actions:
- Validate the fixed 3B caption store against all retained image hashes and sample real/caption EasyR1 batches.
- Use L7 to compute registered difficulty values on this exact ID set.
