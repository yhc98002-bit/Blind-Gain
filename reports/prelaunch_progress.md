L0 | pass | reports/storage_preflight.md: PI-approved shared save to login-archive sweep passed all nine dry-cycle checks with exact read-back hashes
L1 | pass | reports/parser_agreement_audit_v2.md: canonical-v2 fixtures pass; repeated agreement is 0.915625, below 0.95 and explicitly retained for PI review
L2 | pass | reports/scorer_v2_spec.md: per-run extractor_valid/contract_valid split and exact StrictGain identity fixtures pass
L3 | pass | reports/pilot_reward_spec.md: five optimizer steps, 12,800 training plus 601 sequence-verified validation shadows, zero identity errors, and clean exit
L4 | pass | reports/a3_caption_path.md: frozen corpus has 100% fixed-caption coverage and sampled caption batches contain no image payload
L5 | pass | required reports: V4 precision filter retains 1,288/2,101 rows; frozen ID SHA256 is 8631d015ee8593669b46cc707b9fe1fb3690391520bccf416b64bbb2306ff7d1
L6 | pass | named reports repaired; four consistency classes and non-gating GPU-hours accounting pass 28 focused tests
L7 | blocked | all five runs are active: real/gray/noise/none on an29 at 20260711T141452Z/141458Z/141503Z/141514Z and caption on an12 at 20260711T142842Z
L8 | pass | reports/fliptrack_r20_confirmatory.md and .json: 1,200 one-shot pairs and all 11 cells complete; document passes while geometry/chart are downgraded to R19-selected under frozen criteria
L9 | blocked | 72B captioner is selected for compute-node dev-shm; stress run still depends on R20 generation
L10 | blocked | MathVerse 3B/7B inference and canonical-v2 postprocess recovered; corrupt MMMU v1 TSV is preserved, V2 3B/7B TP1 reruns are active on an12 GPUs 4/5, and five-condition ViRL39K remains
L11 | blocked | one declared 100-pair dense-document batch is generated and validated; 3B/7B real plus 7B caption scoring remains for free GPUs
L12 | blocked | preregistration depends on L7 plus PI sign-off and the human R19 audit
L13 | blocked | pilot launch depends on L3, L4, L5, and merged L12 preregistration
