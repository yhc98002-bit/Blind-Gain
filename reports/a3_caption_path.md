# A3 Fixed-Caption Data Path

Status:
- The `caption` image condition is implemented and audited on the frozen 1,288-row Geometry3K pilot corpus.
- All 986 unique retained image hashes have fixed Qwen2.5-VL-3B question-blind captions; missing-caption coverage is zero.
- Representative real-mode batches carry image tensors, while caption-mode batches carry no image token, image tensor, or `multi_modal_data` payload.

Evidence:
- Integration run: `experiments/runs/a3_caption_path_audit_login_20260711T110048Z`, exit code 0, git `6aeb8aa`, config hash `9985adf14fdd7241539a4303aec78867a5421179fa4da8af848774406237ff94`.
- Audit JSON: `experiments/runs/a3_caption_path_audit_login_20260711T110048Z/audit.json`, SHA256 `27908bce638cbebc8b8f839d61eb1533574f98c9979e2733ff119eb86dfe4e2d`.
- Frozen input: `data/geo3k_pilot_filtered.jsonl`, 1,288 rows, SHA256 `f3d88dd1e52ccef833f266880e487eef252193f774c1076f7dfbccd180b450e6`.
- Caption model: `artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct`.
- Caption prompt SHA256: `9e8a66fb1fd5b8edc40647c670b0c8d75a99c1552a8edf307131d7648bd00ae0`.
- Canonical merged caption-store SHA256: `f71a91cdb60649cb849940a548ddd8053b5c19f5f4358dc739c2424ec0168e44`.
- Reproducible patches: `docs/easyr1_image_condition_patch.diff` (`ad06e17e...06d0`) and `docs/easyr1_caption_condition_patch.diff` (`eda01a27...0557d`).
- Installer: `scripts/apply_easyr1_caption_condition_patch.sh`, SHA256 `f57f290d14dd23c93693d9d150a5bc56dfaa37e3aedaa0b7d3c15e29a49c8d91`.
- Focused real/caption integration selection: 3 tests pass in 90.33 seconds; the complete six-fixture caption/image-condition suite passed before the frozen-data integration fixture was added.

Coverage:
| Measure | Value |
| --- | ---: |
| Frozen rows / image references | 1,288 / 1,288 |
| Unique retained image hashes | 986 |
| Total fixed-store image hashes | 1,736 |
| Missing retained hashes | 0 |
| Retained-hash coverage | 100% |

Exact frozen insertion template:
```text
\n[Question-blind image description {index}: {caption}]\n
```

Question-blind contract:
- Caption generation is complete before QA or pilot training.
- Store rows are keyed only by image-content SHA256.
- Rows containing `question`, `problem`, `answer`, `answer_a`, or `answer_b` fail loading.
- Mixed caption models or prompt hashes fail loading.
- A missing content hash raises immediately; there is no online fallback.

Sampled batch checks:
| Source row | Real image payload | Caption image payload | Fixed caption block | Residual image token |
| ---: | --- | --- | --- | --- |
| 0 | present | absent | present | absent |
| 1,060 | present | absent | present | absent |
| 2,099 | present | absent | present | absent |

Problems:
- The pinned EasyR1 checkout is intentionally modified by reproducible patch files because upstream does not provide this `image_condition` contract. The checkout itself is an ignored nested repository; the patch files and tests are the source of record.
- The fixed caption store covers the full Geometry3K train/test image set, so 750 hashes are unused by the filtered pilot corpus. This is harmless but must not be interpreted as 1,736 training images.
- The caption audit proves data-path isolation and coverage, not caption quality or blind-solvability hardness; L7 measures those endpoints under the exact pilot contract.

Decision:
- Freeze `image_condition: caption`, the exact insertion string above, and the 3B store hash for A3.
- Use `data/geo3k_pilot_filtered.jsonl` for all four pilot arms; A3 differs only in `image_condition` and arm identity.
- Fail closed on any missing caption rather than dropping or substituting rows.

Next actions:
- Bind the L3 pilot reward and run its five-step smoke on this same corpus.
- Stamp the caption model, prompt hash, and store hash into every A3 run manifest.
