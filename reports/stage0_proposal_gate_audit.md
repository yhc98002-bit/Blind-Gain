# Stage 0 Proposal Gate Audit

Status:
- The narrow infrastructure marker `reports/stage0_done.json` is pass.
- The proposal-level Stage 0 gate is only `conditional`.
- The main gap is scientific: a 2-step smoke is not a meaningful GRPO reproduction anchor. A 30-step Geometry3K recovery run is now launched but not complete at the time of this audit.

Evidence:
- Cluster bring-up: `reports/stage0_cluster_bringup.md`, `reports/gpu_inventory.json`, DDP/FSDP sanity reports.
- Model downloads: Qwen2.5-VL-3B and 7B are downloaded and checksummed; Qwen3-VL and editor/detector stack are not complete.
- Dataset acquisition: Geometry3K is cached; ViRL39K/MMK12/COCO/VisMin/VQAv2 are triaged but not all downloaded.
- GRPO smoke: `checkpoints/stage0_repro/easyr1_geo3k_smoke/global_step_2/actor`.
- Recovery GRPO run in progress: `experiments/runs/easyr1_geo3k_recovery30_20260708T043244Z`.

Checklist:

| Item | Status | Rationale |
| --- | --- | --- |
| cluster_bringup | pass | SSH, GPU inventory, CUDA, DDP/NCCL, cross-node DDP, FSDP toy passed. |
| model_downloads | partial | Qwen2.5-VL-3B/7B present; broader model/editor/detector stack incomplete. |
| dataset_acquisition | partial | Geometry3K present; proposal datasets not all acquired. |
| license_log | partial | Log exists, but several licenses remain VERIFY/TBD. |
| published_grpo_reproduction | partial | 2-step smoke completed; 30-step engineering anchor is in progress. |
| reproduction_tolerance_defined | fail | No published target/tolerance yet. |
| reward_parser_audit | pass | Local parser tests pass; EasyR1 r1v reward still needs deeper mathruler spot audit. |
| config_diff_audit | partial | Recovery config is compared at high level; detailed line-by-line diff is pending. |
| image_preprocessing_audit | partial | EasyR1 image resizing path inspected; arm-specific transforms need full audit. |
| chat_template_audit | partial | r1v prompt path identified; no example-by-example audit yet. |
| deterministic_eval_audit | partial | Deterministic FlipTrack eval exists; GRPO pre/post eval still pending. |
| checkpoint_discipline | partial | Immutable run dirs/checkpoints exist; long-run manifest discipline is being hardened. |

Decision:
- Do not claim proposal Stage 0 pass.
- Treat current status as conditional until the 30-step recovery anchor completes or fails with a root-cause fix.

Next actions:
- Complete/inspect `easyr1_geo3k_recovery30`.
- Add detailed config diff, reward parser, image preprocessing, chat template, and deterministic eval audits before a longer run.
