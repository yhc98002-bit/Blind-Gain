L0 | blocked | reports/storage_preflight.md: guards/tests pass, but which writable persistent local paths on an12/an29 should hold pilot checkpoints while preserving the 40 GiB floor?
L1 | blocked | canonical-v2 parser work waits for L0
L2 | blocked | validity-field split waits for L0
L3 | blocked | pilot reward depends on L0 and L1 before its smoke run
L4 | blocked | A3 caption path waits for L0
L5 | blocked | pilot-corpus decontamination waits for L0
L6 | blocked | consistency auditor and report repairs wait for L0
L7 | blocked | blind-solvability v2 depends on L1, L2, L3, and L5
L8 | blocked | R20 confirmatory generation waits for L0
L9 | blocked | stronger-caption stress depends on L0 captioner decision and L8 generation
L10 | blocked | Layer-1 completion and ViRL39K audit wait for L0 and Wave-1 contracts
L11 | blocked | document calibration may run only after L0 on genuinely free GPUs
L12 | blocked | preregistration depends on L7 plus PI sign-off and the human R19 audit
L13 | blocked | pilot launch depends on L3, L4, L5, and merged L12 preregistration
