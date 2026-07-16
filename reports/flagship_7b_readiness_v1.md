# Flagship 7B Readiness V1

Status:
- `blocked`. The M8 inference-only base audit and its audit-sample caption store
  are complete, but the 7B flagship training unit is not launch-ready.
- No M9 optimizer step is authorized by this report.

Evidence:
- Five-condition, 4,096-item report:
  `reports/blind_solvability_virl39k_7b_sample_v1.md`.
- Independent machine audit:
  `reports/blind_solvability_virl39k_7b_sample_v1_audited.json`; all 15 checks
  true and zero score-recomputation mismatches.
- Exact model revision:
  `Qwen/Qwen2.5-VL-7B-Instruct@cc594898137f460bfe9f0759e9844b3ce807cfb5`.
- Frozen audit sample: `data/virl39k_blind_sample_4096.jsonl`, SHA256
  `ffbad6eaff57f6dd11f136b066e4d4206e43381281a3cb24cc677241c360e6d5`.
- Audit-sample 7B caption store:
  `experiments/runs/virl39k_sample4096_qwen25vl7b_captionstore384_retry_20260710T163500Z/shards/store_shard_0.jsonl`,
  SHA256 `426644dae442fcc4ee3d6e023928e179d3ac957ec3857486d37e7bb7a2f66b0c`;
  exact coverage is 4,297/4,297 unique images.
- The precommitted M8 rule fixes the M9 arm set to A1/A2/A2b/A3, three seeds
  each. This is recorded in `docs/registered_extensions_v1.md`.

Problems:
- The frozen ViRL training subset and its SHA256 do not yet exist.
- The 7B own-caption store for that training subset does not yet exist; the
  audit-sample store cannot be silently substituted.
- A1/A2/A2b/A3 flagship training configs, hashes, seeds, step budget, token
  budget, and cadence remain `{computed-pending}` in M4.

Decision:
- Treat the five-condition audit as completed M8 scientific input but keep the
  M8/M9 training-readiness conjunction fail-closed.
- Fill only fields directly supported by frozen M8 artifacts. Preserve all
  training-subset/config placeholders until their own audit lands.

Next actions:
- Freeze the decontaminated ViRL training subset, generate the full 7B caption
  store, and prepare four matched flagship configs before changing this status.
