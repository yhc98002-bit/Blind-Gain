L0 | pass | reports/storage_preflight.md: PI-approved shared save to login-archive sweep passed all nine dry-cycle checks with exact read-back hashes
L1 | pass | reports/parser_agreement_audit_v2.md: canonical-v2 fixtures pass; repeated agreement is 0.915625, below 0.95 and explicitly retained for PI review
L2 | pass | reports/scorer_v2_spec.md: per-run extractor_valid/contract_valid split and exact StrictGain identity fixtures pass
L3 | blocked | L0/L1 dependencies are complete; custom pilot reward implementation and five-step smoke remain
L4 | pass | reports/a3_caption_path.md: frozen corpus has 100% fixed-caption coverage and sampled caption batches contain no image payload
L5 | pass | required reports: V4 precision filter retains 1,288/2,101 rows; frozen ID SHA256 is 8631d015ee8593669b46cc707b9fe1fb3690391520bccf416b64bbb2306ff7d1
L6 | pass | named reports repaired; four consistency classes and non-gating GPU-hours accounting pass 28 focused tests
L7 | blocked | blind-solvability v2 depends on L1, L2, L3, and L5
L8 | blocked | one-shot 1,200-pair generation and leakage lint pass; grouped attacker and all seven hardness cells remain
L9 | blocked | 72B captioner is selected for compute-node dev-shm; stress run still depends on R20 generation
L10 | blocked | Layer-1 completion and ViRL39K audit wait for L0 and Wave-1 contracts
L11 | blocked | document calibration remains lowest priority and may run only on genuinely free GPUs
L12 | blocked | preregistration depends on L7 plus PI sign-off and the human R19 audit
L13 | blocked | pilot launch depends on L3, L4, L5, and merged L12 preregistration
