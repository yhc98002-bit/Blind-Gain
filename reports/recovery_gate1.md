# Recovery Gate 1

Status:
- Gate status: pass for the machine-checkable Recovery Gate 1 criteria.
- Important caveat: the first artifact gate still fails on the packaged V0.1 manifest because path/member metadata predicts A/B side with AUC 1.0.
- Stage 0 proposal gate remains conditional, not pass.

Evidence:
- GRPO recovery anchor completed 30 global steps on `an12` GPUs 0,1.
- Checkpoint tracker: `checkpoints/stage0_repro/easyr1_geo3k_recovery30/checkpoint_tracker.json`.
- Final saved actor path: `checkpoints/stage0_repro/easyr1_geo3k_recovery30/global_step_30/actor`.
- FlipTrack V0.1 has 300 generated/scored pairs: 100 chart, 100 document/OCR, 100 geometry.
- Qwen2.5-VL-3B V0.1 real pair accuracy: 0.8933.
- Qwen2.5-VL-3B V0.1 caption-only pair accuracy: 0.1000.
- Qwen2.5-VL-7B V0.1 real pair accuracy: 0.9333.
- Qwen2.5-VL-7B V0.1 caption-only pair accuracy: 0.5167.
- Artifact gate on packaged paths: metadata AUC 1.0, DINOv2 AUC 0.4717, best AUC 1.0.
- Artifact gate after sanitized symlink paths: metadata AUC 0.4217, DINOv2 AUC 0.4719, best AUC 0.4719.

Problems:
- V0.1 is not release-ready until filenames/paths stop encoding pair side.
- ViRL39K acquisition is still blocked by loader handling of `images.zip`.
- The GRPO run is an engineering anchor, not a published reproduction, because published target/tolerance and pre/post checkpoint evaluation are not complete.
- Qwen2.5-VL-7B caption-only is below the aggregate 0.60 ceiling but shows template-level leakage/compressibility on the starred legend template.

Decision:
- Treat Recovery Gate 1 as passed for the requested gate predicates, with artifact packaging cleanup required before any artifact-robustness claim.
- Keep Blind Gains framed as a controlled decomposition and counterfactual measurement paper.
- Treat CP-GRPO as constructive unless the overlap audit later establishes standalone novelty.

Next actions:
- Repackage FlipTrack V0.1 with randomized/equalized paths, rerun artifact gate, and regenerate release manifests.
- Run base-model and `global_step_30` checkpoint evaluation on the same validation slice.
- Continue ViRL39K loader/license triage; keep Geometry3K as engineering fallback only.
- Harden V0.1 starred legend and symbol-grid templates against 7B caption compression.
