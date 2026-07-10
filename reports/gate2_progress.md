P0.1 | pass | final-answer-span scorer and all adversarial fixtures are complete
P0.2 | pass | 320 recovered-step-30 generations audited; agreement is 0.921875 with 25 categorized disagreements and versioned fixes required
P0.3 | pass | within-template key-shuffle and auxiliary swap nulls are implemented and tested
P0.4 | pass | cached V0.1 predictions are re-scored in `reports/fliptrack_v01_rescored.md`
P0.5 | pass | resolved EasyR1 reference diff covers every required field
P1.1 | blocked | recipe-scale anchor is healthy through step 30/100; validations 0/10/20/30 and merged step-20 checkpoint are preserved
P1.2 | pass | MMStar/MathVista/BLINK plus HallusionBench/MMVP complete for 3B/7B; registered MMStar/MathVista blind cells complete
P1.3 | blocked | measured NCCL and actual-3B FSDP smokes are implemented; full 2x8 window is blocked by active project jobs plus an unrelated four-GPU service on an29
P1.4 | pass | 1,200-pair same-salt R19 package passes all 12 leakage-linter checks
P1.5 | pass | all-inclusive same-salt R19 expansion passes grouped frequency, metadata, and DINOv2 point/CI rules
P1.6 | pass | document, R10 geometry, and R16 chart provide three accepted 300-pair templates with contact sheets
P1.7 | pass | all three R17 candidate templates pass degradation and model/caption scale controls
P1.8 | blocked | final R19 3B store covers all 2,400 release hashes exactly; 7B R17/R18 generation and exact merge remain active
P1.9 | pass | ViRL39K/MMK12 loaders cover all rows and critical model/dataset licenses are resolved
P1.10 | pass | calibrated full Geometry3K x 7,603-row Layer-1 hash/DINO/BGE/OCR manifest is complete with zero pending layers
P1.11 | blocked | gate logic passes, but worktree contains external `CLAUDE.md` deletion and untracked `AGENTS.md`
P2.1 | blocked | image-condition path and three matched configs pass tests; execution waits for P0.2/P1.1
P2.2 | pass | all five 2,702-item Geometry3K conditions and bootstrapped blind-solvability report are complete
P3.1 | blocked | prepare-only sensitivity control waits for a valid V0.2 freeze
P3.2 | blocked | informational CP-GRPO note requires no execution in this phase
