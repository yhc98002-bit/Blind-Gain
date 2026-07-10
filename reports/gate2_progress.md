P0.1 | pass | final-answer-span scorer and all adversarial fixtures are complete
P0.2 | pass | 320 recovered-step-30 generations audited; agreement is 0.921875 with 25 categorized disagreements and versioned fixes required
P0.3 | pass | within-template key-shuffle and auxiliary swap nulls are implemented and tested
P0.4 | pass | cached V0.1 predictions are re-scored in `reports/fliptrack_v01_rescored.md`
P0.5 | pass | resolved EasyR1 reference diff covers every required field
P1.1 | blocked | recipe-scale anchor is healthy through step 21/100; step-20 validation and merged checkpoint are preserved
P1.2 | pass | MMStar/MathVista/BLINK plus HallusionBench/MMVP complete for 3B/7B; registered MMStar/MathVista blind cells complete
P1.3 | blocked | coordinated two-node NCCL/FSDP window not yet run
P1.4 | blocked | R8 candidate passes all 12 linter checks, but no scientifically valid final package is frozen
P1.5 | blocked | R8 fails only chart metadata; required R9 expansion then fails the 3B visual floor
P1.6 | blocked | R15 five-series chart passes the 3B real gate at 0.5733; required 7B/caption/blind/degradation controls are active
P1.7 | blocked | R10 passes both controls and R7 diagnoses caption leakage; final three-template set absent
P1.8 | blocked | Geometry3K and R8 stores complete for 3B/7B and budget comparison reported; final retained V0.2 package is absent
P1.9 | pass | ViRL39K/MMK12 loaders cover all rows and critical model/dataset licenses are resolved
P1.10 | pass | calibrated full Geometry3K x 7,603-row Layer-1 hash/DINO/BGE/OCR manifest is complete with zero pending layers
P1.11 | blocked | gate logic passes, but worktree contains external `CLAUDE.md` deletion and untracked `AGENTS.md`
P2.1 | blocked | image-condition path and three matched configs pass tests; execution waits for P0.2/P1.1
P2.2 | blocked | vLLM harness and report generator pass tests; real/gray/noise/no-image full Geometry3K runs are active and caption is queued
P3.1 | blocked | prepare-only sensitivity control waits for a valid V0.2 freeze
P3.2 | blocked | informational CP-GRPO note requires no execution in this phase
