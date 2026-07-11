L0 | pass | reports/storage_preflight.md: PI-approved shared save to login-archive sweep passed all nine dry-cycle checks with exact read-back hashes
L1 | pass | reports/parser_agreement_audit_v2.md: canonical-v2 fixtures pass; repeated agreement is 0.915625, below 0.95 and explicitly retained for PI review
L2 | pass | reports/scorer_v2_spec.md: per-run extractor_valid/contract_valid split and exact StrictGain identity fixtures pass
L3 | blocked | reports/l7_noimage_symbolic_grader_stall.md: original five-step smoke passed, but the new pinned symbolic-grader guard requires a replacement five-step smoke before L12
L4 | pass | reports/a3_caption_path.md: frozen corpus has 100% fixed-caption coverage and sampled caption batches contain no image payload
L5 | pass | required reports: V4 precision filter retains 1,288/2,101 rows; frozen ID SHA256 is 8631d015ee8593669b46cc707b9fe1fb3690391520bccf416b64bbb2306ff7d1
L6 | pass | named reports repaired; four consistency classes and non-gating GPU-hours accounting pass 28 focused tests
L7 | blocked | real/gray/noise are active on an29; guarded none resumed from row 100 on an29 GPU7 and guarded caption resumed from row 332 on an12 GPU6; all five conditions remain incomplete
L8 | pass | reports/fliptrack_r20_confirmatory.md and .json: 1,200 one-shot pairs and all 11 cells complete; document passes while geometry/chart are downgraded to R19-selected under frozen criteria
L9 | blocked | R20 is complete; the 72B stress awaits a four-GPU single-node TP window and a guard-confirmed ephemeral weight footprint
L10 | blocked | MathVerse and repaired-V2 MMMU 3B/7B rows are complete and published; the five-condition ViRL39K sample audit remains
L11 | blocked | one declared 100-pair dense-document batch is generated and validated; 3B/7B real plus 7B caption scoring remains for free GPUs
L12 | blocked | preregistration depends on L7 plus PI sign-off and the human R19 audit
L13 | blocked | pilot launch depends on L3, L4, L5, and merged L12 preregistration
