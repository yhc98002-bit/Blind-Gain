P0.1 | pass | final-answer-span scorer implemented; adversarial fixtures pass; `reports/scorer_v2_spec.md` written
P0.2 | blocked | parser fixed and nested-brace tests pass, but recovery run logged 0 usable generations for the required >=300 agreement audit
P0.3 | pass | within-template key-shuffle null and auxiliary swap null implemented with unit tests and aggregator outputs
P0.4 | pass | cached V0.1 predictions re-scored in `reports/fliptrack_v01_rescored.md`
P0.5 | pass | resolved EasyR1 reference config materialized and `reports/grpo_config_diff.md` regenerated
P1.1 | blocked | immutable recipe-scale retry is in the optimizer path at `experiments/runs/anchor_a0_recipe_3b_geo3k_20260709T224852Z`; completion pending
P1.2 | blocked | VLMEvalKit pinned at `6a02ab9`; isolated install and ModelScope-first local judge acquisition are in progress
P1.3 | blocked | not started; requires coordinated two-node NCCL/FSDP window
P1.4 | pass | 600-pair opaque package passes all linter checks; see `reports/fliptrack_v02_packaging.md` and `reports/fliptrack_v02_lint.json`
P1.5 | blocked | retained package passes pooled/DINO attacks but coordinate frequency/metadata and header metadata fail; 200-pair template expansions required by CI rule
P1.6 | pass | 300-pair retained set has chart/document/geometry templates meeting final-answer real/caption/gray/pair-shared-noise criteria; format caveat reported
P1.7 | blocked | degradation and real-model scale controls pass per retained template; 3B caption-only scale side remains
P1.8 | blocked | R2 7B question-blind 384-token captions complete; hash-keyed store plus geometry3k/3B coverage remain
P1.9 | blocked | dataset/license acquisition not started in this turn; must avoid failed `load_dataset()` path for ViRL39K
P1.10 | blocked | not started; calibration datasets and Layer-1 manifests pending
P1.11 | pass | generated data untracked with checksums, gate AND-logic tested, logical commits created, and worktree clean
P2.1 | blocked | waits for P0/P1.1 and EasyR1 image-condition data path
P2.2 | blocked | waits for P0.1/P0.2 and blind-solvability harness implementation
P3.1 | blocked | prepare-only; waits for V0.2 template freeze
P3.2 | blocked | informational prepare-only; no execution requested
