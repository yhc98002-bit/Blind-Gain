# Blind Gains Project Directory Structure

Generated: 2026-07-10 01:45 Asia/Shanghai
Workspace: `/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain`

This is a pruned recursive tree intended for code review. It includes source, configs, scripts, tests, reports, manifests, and run-summary files. It intentionally omits `.git/`, `.venv/`, model checkpoints, downloaded model artifacts, Python caches, generated image files under `data/fliptrack_v01/**/images`, and large experiment logs. Those omitted directories are not needed for source audit and would make the review package noisy.

```text
BlindGain/
├── CLAUDE.md
├── README.md
├── configs/
│   ├── env/
│   │   ├── default_paths.sh
│   │   ├── easyr1_or_verl_recovery.yaml
│   │   └── proxy.sh
│   └── train/
│       ├── a1_real_3b_pilot.yaml
│       ├── a2_gray_3b_pilot.yaml
│       ├── easyr1_qwen25vl3b_geo3k_recovery30.yaml
│       ├── easyr1_qwen25vl3b_geo3k_smoke.yaml
│       └── qwen25vl3b_grpo_repro.yaml
├── data/
│   ├── fliptrack_renderable_900_manifest.jsonl
│   ├── fliptrack_renderable_900_scored.jsonl
│   ├── fliptrack_v0_manifest.jsonl
│   ├── fliptrack_v0_manifest_scored.jsonl
│   ├── fliptrack_v01_manifest.jsonl
│   ├── fliptrack_v01_scored.jsonl
│   └── fliptrack_v01/
│       └── renderable/
│           ├── chart/
│           │   ├── images/  [generated PNGs omitted from archive]
│           │   └── masks/   [generated PNG masks omitted from archive]
│           ├── doc/
│           │   ├── images/  [generated PNGs omitted from archive]
│           │   └── masks/   [generated PNG masks omitted from archive]
│           └── geometry/
│               ├── images/  [generated PNGs omitted from archive]
│               └── masks/   [generated PNG masks omitted from archive]
├── docs/
│   ├── easyr1_sdpa_patch.diff
│   └── pi_request.md
├── experiments/
│   ├── manifests/
│   │   └── model_registry.jsonl
│   └── runs/
│       ├── latest_*_run.txt
│       └── [run directories with logs, shards, metrics, and manifests]
├── logs/
│   ├── downloads/
│   ├── gpu_jobs/
│   ├── gpu_util_an12.jsonl
│   ├── gpu_util_an29.jsonl
│   ├── setup/
│   └── tunnels/
├── reports/
│   ├── artifact_gate_v01.md
│   ├── artifact_manifest.json
│   ├── dataset_license_triage.json
│   ├── dataset_license_triage.md
│   ├── deterministic_eval_audit.md
│   ├── experiment_status_20260708_1145.md
│   ├── experiment_status_20260708_1308.md
│   ├── fliptrack_caption_leakage_audit.md
│   ├── fliptrack_v01_hardness.md
│   ├── gpu_inventory.json
│   ├── grpo_chat_template_audit.md
│   ├── grpo_config_diff.md
│   ├── grpo_image_preprocessing_audit.md
│   ├── grpo_reproduction_recovery.md
│   ├── grpo_reward_parser_audit.md
│   ├── license_log.csv
│   ├── literature_overlap_20260708.md
│   ├── local_serving_smoke.md
│   ├── model_downloads.md
│   ├── network_probe.md
│   ├── project_directory_structure_20260710_0145.md
│   ├── recovery_gate1.json
│   ├── recovery_gate1.md
│   ├── repo_watch.md
│   ├── review_selected_files_manifest_20260710_0145.txt
│   ├── stage0_cluster_bringup.md
│   ├── stage0_done.json
│   ├── stage0_lit_repo_audit.md
│   ├── stage0_proposal_gate_audit.json
│   ├── stage0_proposal_gate_audit.md
│   ├── stage0_reproduction.md
│   ├── stage1_fliptrack_v0.md
│   ├── stage2_pilot_readiness.md
│   ├── training_stack_decision.md
│   └── work_done_detailed_20260710_0133.md
├── scripts/
│   ├── aggregate_fliptrack_eval.py
│   ├── apply_easyr1_sdpa_patch.sh
│   ├── bootstrap_env.sh
│   ├── caption_fliptrack.py
│   ├── check_env.py
│   ├── collect_gpu_util.sh
│   ├── ddp_sanity.py
│   ├── download_modelscope_model.py
│   ├── eval_caption_qa_fliptrack.py
│   ├── eval_qwen_vl_fliptrack.py
│   ├── fsdp_toy_train.py
│   ├── gpu_profile.py
│   ├── launch_an12.sh
│   ├── launch_an29.sh
│   ├── launch_caption_qa_shards.sh
│   ├── launch_easyr1_geo3k_recovery30.sh
│   ├── launch_easyr1_geo3k_smoke.sh
│   ├── launch_fliptrack_caption_shards.sh
│   ├── launch_fliptrack_eval_shards.sh
│   ├── launch_fliptrack_v01_eval_shards.sh
│   ├── net_probe.sh
│   ├── qwen_vl_smoke.py
│   ├── run_dir.sh
│   ├── start_gpu_logging.sh
│   ├── sync_nodes.sh
│   ├── torch_gpu_sanity.py
│   └── vllm_qwen_vl_smoke.py
├── src/
│   ├── __init__.py
│   ├── data/
│   │   ├── __init__.py
│   │   └── model_registry.py
│   ├── eval/
│   │   ├── __init__.py
│   │   ├── fliptrack_metrics.py
│   │   └── local_vlm_client.py
│   ├── fliptrack/
│   │   ├── __init__.py
│   │   ├── artifact_attackers.py
│   │   ├── artifact_gate.py
│   │   ├── build_renderable_v0.py
│   │   ├── build_v01.py
│   │   ├── natural_scene_pipeline.py
│   │   ├── render_chart.py
│   │   ├── render_doc.py
│   │   ├── render_geometry.py
│   │   └── schema.py
│   └── rewards/
│       ├── __init__.py
│       ├── answer_reward.py
│       └── cp_grpo_reward.py
└── tests/
    ├── test_easyr1_sdpa_patch.py
    ├── test_fliptrack_metrics.py
    └── test_reward_parser.py
```

## Omitted Large/Generated Directories

```text
.git/
.venv/
artifacts/
checkpoints/
data/fliptrack_v01/**/images/
data/fliptrack_v01/**/masks/
experiments/runs/*/logs/
experiments/runs/*/shards/
logs/
__pycache__/
.pytest_cache/
```
