L0 | pass | reports/storage_preflight.md: PI-approved shared save to login-archive sweep passed all nine dry-cycle checks with exact read-back hashes
L1 | pass | reports/parser_agreement_audit_v2.md: canonical-v2 fixtures pass; repeated agreement is 0.915625, below 0.95 and explicitly retained for PI review
L2 | pass | reports/scorer_v2_spec.md: per-run extractor_valid/contract_valid split and exact StrictGain identity fixtures pass
L3 | blocked | pilot reward depends on L0 and L1 before its smoke run
L4 | blocked | A3 caption-path unit-test work started; the fixed caption store coverage must still be established
L5 | blocked | geometry3k train-vs-test decontamination and frozen filtered IDs are now in progress
L6 | pass | named reports repaired; four consistency classes and non-gating GPU-hours accounting pass 28 focused tests
L7 | blocked | blind-solvability v2 depends on L1, L2, L3, and L5
L8 | blocked | one-shot R20 generation is now unblocked; complete pipeline artifacts do not yet exist
L9 | blocked | 72B captioner is selected for compute-node dev-shm; stress run still depends on R20 generation
L10 | blocked | Layer-1 completion and ViRL39K audit wait for L0 and Wave-1 contracts
L11 | blocked | document calibration remains lowest priority and may run only on genuinely free GPUs
L12 | blocked | preregistration depends on L7 plus PI sign-off and the human R19 audit
L13 | blocked | pilot launch depends on L3, L4, L5, and merged L12 preregistration
