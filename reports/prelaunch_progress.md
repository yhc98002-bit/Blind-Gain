L0 | pass | reports/storage_preflight.md: PI-approved shared save to login-archive sweep passed all nine dry-cycle checks with exact read-back hashes
L1 | pass | reports/parser_agreement_audit_v2.md: canonical-v2 fixtures pass; repeated agreement is 0.915625, below 0.95 and explicitly retained for PI review
L2 | pass | reports/scorer_v2_spec.md: per-run extractor_valid/contract_valid split and exact StrictGain identity fixtures pass
L3 | pass | reports/pilot_reward_spec_v2.md: guarded five-step smoke completed with 13,401 exact shadow rows, all v4 audit checks pass, and 35 focused adversarial tests pass
L4 | pass | reports/a3_caption_path.md: frozen corpus has 100% fixed-caption coverage and sampled caption batches contain no image payload
L5 | pass | required reports: V4 precision filter retains 1,288/2,101 rows; frozen ID SHA256 is 8631d015ee8593669b46cc707b9fe1fb3690391520bccf416b64bbb2306ff7d1
L6 | pass | named reports repaired; four consistency classes and non-gating GPU-hours accounting pass 28 focused tests
L7 | blocked | real/gray/noise/caption are complete; guarded none has a validated 1,104-row resume prefix and awaits restart after the quota-aware storage refresh
L8 | pass | reports/fliptrack_r20_confirmatory.md and .json: 1,200 one-shot pairs and all 11 cells complete; document passes while geometry/chart are downgraded to R19-selected under frozen criteria
L9 | blocked | R20 is complete and the guarded 72B ModelScope checkout passed its full tree hash in an29 /dev/shm; TP4 captioning and standard caption-only QA remain
L10 | blocked | MathVerse and repaired-V2 MMMU 3B/7B rows are complete and published; the five-condition ViRL39K sample audit remains
L11 | pass | reports/document_v_next_calibration.md: one-shot 100-pair batch complete; 3B real=0.69, 7B real=1.00, 7B caption=0.04, verdict too-easy with no iteration
L12 | blocked | preregistration depends on L7 plus PI sign-off and the human R19 audit
L13 | blocked | pilot launch depends on L3, L4, L5, and merged L12 preregistration
