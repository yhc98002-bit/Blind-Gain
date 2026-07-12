# Strong Caption Stress Integrity Audit V2

Status:
- `pass` as a measurement-integrity audit. This does not declare a PI gate.
- The L9 deliverable is complete for R19 and R20 under the fixed 72B question-blind captioner and standard 7B caption-only QA protocol.

Evidence:
- Primary report: `reports/strong_caption_stress.md`, SHA256 `1324de119665aba83c2af0ce669dc86937d7c49aa6d80d9483b68a2774967e0a`.
- Machine report: `reports/strong_caption_stress.json`, SHA256 `e3f628d242337a2c66360c628a438041644dfd8773433ddb75e49cf66ab8d353`, `status=complete`.
- Caption-store audit: `reports/strong_caption_store_audit_v1.json`, SHA256 `88f86d7e0418994ac687cb2231c3b34b510627747b23f53aa16f6bc7eaf1bc20`, schema v2, all nine checks true.
- Caption store: 4,800 unique rows/images, SHA256 `2683f7277920d42c1afc9e3d870ab9e63ed21434019b0be15298e984f282fda5`; exact disjoint union of R19 and R20 with zero duplicate hashes and zero file/hash mismatches.
- Caption model/revision/placement: `Qwen/Qwen2.5-VL-72B-Instruct`, `master`, one TP4 replica on an29 GPUs 1,5,6,7; greedy, 384 tokens, fixed question-blind prompt hash `9e8a66fb1fd5b8edc40647c670b0c8d75a99c1552a8edf307131d7648bd00ae0`.
- QA adapters each contain exactly 1,200 pairs and 2,400 images with template counts 600 geometry / 300 document / 300 chart.
- QA placement: R19 on an12 GPU6 and R20 on an12 GPU7, independent TP1 replicas, Qwen2.5-VL-7B, greedy answer protocol.
- Standard aggregation: 2,000 item bootstraps and 1,000 permutations for each package.
- Ephemeral deletion: 146,833,336,607 bytes, model tree SHA256 `2a9b2f96fa1a20764ad675dc6fb35afe869f631a0d1bdfe69ace35052e0333e3`; deletion record confirms the path is absent.

Results:
| Package | Baseline 7B-caption pair accuracy | 72B-caption pair accuracy | 72B 95% bootstrap CI | Delta |
| --- | ---: | ---: | ---: | ---: |
| R19 | 0.0208 | 0.0533 | [0.0417, 0.0667] | +0.0325 |
| R20 | 0.0225 | 0.0617 | [0.0483, 0.0758] | +0.0392 |

Per-template 72B-caption pair accuracy:
| Package | Document | Geometry | Chart |
| --- | ---: | ---: | ---: |
| R19 | 0.0500 | 0.0733 | 0.0167 |
| R20 | 0.0667 | 0.0733 | 0.0333 |

Problems:
- The stronger captioner raises leakage most for geometry, but all observed pair-accuracy cells remain below 0.075.
- This is protocol-specific leakage headroom, not a guarantee against arbitrary captioners or text extractors.
- The result does not repair the separate 7B visual saturation of the document family.

Decision:
- Retain original R19/R20 baseline metrics unchanged and publish the strong-caption deltas alongside them.
- Carry the strongest observed strong-caption cell into preregistration caveats and paper limitations.
- Keep the 72B weights deleted; any rerun requires a new immutable download and manifest.

Next actions:
- Continue the corrected L3 smoke and L10 evaluations; no further strong-caption iteration is scheduled in this round.
