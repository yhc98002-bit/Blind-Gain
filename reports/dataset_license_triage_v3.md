# Dataset And License Triage V3

Status:
- V2 remains unchanged; V3 adds the two L10 evaluation datasets, MathVerse and MMMU.
- Both repositories declare permissive licenses for local evaluation use. This does not independently clear third-party image redistribution.

Evidence:
- Machine table: `reports/license_log_v3.csv`.
- Preserved source cards: `reports/license_terms/mathverse_README.md` and `reports/license_terms/mmmu_README.md`.
- MathVerse checkout: `experiments/runs/modelscope_dataset_mathverse_retry_20260711T121224Z`; revision `5fcb08cb5f640b69d9fb23228b4767ec1a6807d2`; working-tree SHA256 `23bf4dccf89ab3627e383666b537db760386fbc5cfd46ea0e2556031dc6c577d`.
- MathVerse adapter: `experiments/runs/prepare_layer1_mathverse_local_v1_20260711T122854Z`; 3,940 rows, 1,959 unique images, output SHA256 `551d74d829d295524572e2bc0a44b757fda2d04f4c5e991a220f00568afdd9c5`.
- MMMU ModelScope checkout revision: `aea177165b56916b6d3528491599aa280149b6d3`.
- ModelScope returned four payloads whose content hashes did not match their LFS OIDs. The failed acquisition remains at `experiments/runs/modelscope_dataset_mmmu_retry_20260711T121224Z`.
- Hash-pinned fallback: `experiments/runs/hf_file_repair_mmmu_modelscope_bad_oids_20260711T123253Z`; all four Hugging Face objects matched the OIDs in the ModelScope commit.
- Post-repair inventory: `experiments/runs/dataset_inventory_mmmu_postrepair_20260711T124731Z`; 95 files, 3,654,024,491 bytes, zero unresolved pointers, tree SHA256 `5fd612d784aea95463e132f4303252b8ed2256abce5bf77fad4eb7710b1c2a10`.
- MMMU adapter: `experiments/runs/prepare_layer1_mmmu_local_v1_20260711T123927Z`; 1,050 dev-plus-validation rows, 1,100 unique images, output SHA256 `362f4f1d193b55ce54773539a86a7a2f2541cb6f29d5d91289957b9af3d3ac91`.

Problems:
- MathVerse and MMMU include images derived from diverse upstream sources. Repository license declarations are not treated as blanket evidence that every source image may be republished.
- The MMMU checkout is mixed-route only for four byte-identical, OID-verified objects. This is recorded as a source deviation, not hidden as a pure ModelScope acquisition.
- MathVerse's official aggregate metric uses an LLM judge. L10 will report canonical-v2 scores and will not label them as the official judged metric unless a calibrated judge is run.

Decision:
- Permit local evaluation for both datasets under the recorded repository declarations.
- Retain per-item outputs and adapter metadata on shared project storage.
- Do not include raw MathVerse or MMMU image payloads in a public release until image-level provenance review is complete.

Next actions:
- Run the pinned 3B and 7B L10 evaluations and append their canonical-v2 validity columns to the versioned Layer-1 table.
- Record the absence of an official MathVerse judge score beside, not inside, the canonical-v2 accuracy column.
