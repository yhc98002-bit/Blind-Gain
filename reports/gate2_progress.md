P0.1 | pass | final-answer-span scorer implemented; adversarial fixtures pass; `reports/scorer_v2_spec.md` written
P0.2 | blocked | parser fixed and nested-brace tests pass, but recovery run logged 0 usable generations for the required >=300 agreement audit
P0.3 | pass | within-template key-shuffle null and auxiliary swap null implemented with unit tests and aggregator outputs
P0.4 | pass | cached V0.1 predictions re-scored in `reports/fliptrack_v01_rescored.md`
P0.5 | pass | resolved EasyR1 reference config materialized and `reports/grpo_config_diff.md` regenerated
P1.1 | blocked | SDPA padding-free failure diagnosed and fixed; immutable retry running at `experiments/runs/anchor_a0_recipe_3b_geo3k_20260709T222659Z`
P1.2 | blocked | not started; VLMEvalKit/local judge setup still pending
P1.3 | blocked | not started; requires coordinated two-node NCCL/FSDP window
P1.4 | pass | 600-pair opaque package passes all linter checks; see `reports/fliptrack_v02_packaging.md` and `reports/fliptrack_v02_lint.json`
P1.5 | blocked | corrected attackers ran and first candidate failed (DINO pooled 0.625; parallel 1.0); R2 balanced-side rerun pending
P1.6 | blocked | 600 pairs and six contact sheets built; 3B real and 7B caption hardness scoring are running on `an29`
P1.7 | blocked | waits for P1.6 retained V0.2 templates
P1.8 | blocked | 7B V0.2 captions at 384 tokens are running; hash-keyed caption store and geometry3k/3B coverage remain
P1.9 | blocked | dataset/license acquisition not started in this turn; must avoid failed `load_dataset()` path for ViRL39K
P1.10 | blocked | not started; calibration datasets and Layer-1 manifests pending
P1.11 | pass | generated data untracked with checksums, gate AND-logic tested, logical commits created, and worktree clean
P2.1 | blocked | waits for P0/P1.1 and EasyR1 image-condition data path
P2.2 | blocked | waits for P0.1/P0.2 and blind-solvability harness implementation
P3.1 | blocked | prepare-only; waits for V0.2 template freeze
P3.2 | blocked | informational prepare-only; no execution requested
