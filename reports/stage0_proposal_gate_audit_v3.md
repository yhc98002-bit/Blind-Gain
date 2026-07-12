# Stage 0 Proposal Gate Audit V3

Status:
- Mechanical accounting remains `conditional`; this document does not declare a PI gate.
- V3 changes only `chat_template_audit` from partial to pass after the dedicated rendered-prompt audit. V2 and all predecessor numbers remain unchanged.
- Published reproduction remains `fail`; no target/tolerance is registered and native metric continuity remains incomplete.

Evidence:
- Machine checklist: `reports/stage0_proposal_gate_audit_v3.json`.
- Chat-template machine artifact: `reports/grpo_chat_template_audit_v2.json`, SHA256 `ead8aeb4fcc4693c1d99364a61488f8408e3923adfa3adcf89bd11799383a396`.
- Chat-template report: `reports/grpo_chat_template_audit_v2.md`, SHA256 `fdc720b91c12415ccc70e82a8c6e170b2bbbadd6cdbef91bbcdd29bf96122e22`.
- Immutable audit run: `experiments/runs/grpo_chat_template_audit_v2_an12_20260712T085609Z`, `status=complete`, `exit_code=0`.
- The Qwen fast-image-processor runtime warning appears in both the anchor and active L3 logs; the audit therefore uses the same environment default rather than silently switching to the slow processor.

Checklist:

| Item | Status | Evidence and rationale |
| --- | --- | --- |
| cluster_bringup | pass | Stage-0 CUDA/DDP/FSDP/NCCL inventory and smoke artifacts remain valid. |
| model_downloads | partial | Qwen2.5-VL 3B/7B and current evaluators exist; the broader optional editor/detector inventory is incomplete. |
| dataset_acquisition | partial | Geometry3K and ViRL39K are usable; proposal-wide acquisition/release provenance is not complete for every listed dataset. |
| license_log | partial | V3 records ten artifacts; several image-derived datasets remain under conservative source-image/provenance review. |
| published_grpo_reproduction | fail | The 100-step run is an engineering anchor with documented deviations and an incomplete native metric history. |
| reproduction_tolerance_defined | fail | No published target and tolerance were registered before observing the run. |
| reward_parser_audit | pass | Canonical-v2 fixtures and the exact 320-row native/canonical agreement audit exist; its below-0.95 warning remains explicit. |
| config_diff_audit | pass | Resolved EasyR1 reference and anchor differ field by field in Markdown and machine JSON. |
| image_preprocessing_audit | pass | The 1,288-row visual-grid audit catches the old double resize and reports zero mismatches after repair. |
| chat_template_audit | pass | Eleven checks pass on 8 train plus 8 test prompts; token ranges are 436-501 and 446-635, all below 2,048. |
| deterministic_eval_audit | pass | V2 verifies base/step-100 hashes, identical item content/contracts, and paired endpoint metrics. |
| checkpoint_discipline | pass | Step-100 merge, hashes, latest-raw retention, shared cleanup, and immutable relocation records are complete. |

Problems:
- The logical AND for full Stage-0 pass remains false because model/dataset/license rows are partial and published reproduction/tolerance rows fail.
- A chat-template implementation pass does not resolve native-versus-canonical parser disagreement.

Decision:
- Retain `overall_proposal_stage0=conditional`.
- Pin r1v prompt SHA256 `f1b62cb8332bdbec38efc8689aff6e9ce65174c0db8967937307880f95f58fca` and Qwen chat-template SHA256 `a0bc6f6fc7a29a80017a433e8f03a1cc1236e838a944a2d034295a60c4f2fddb` for this stack.

Next actions:
- Finish L3 and the step-100 image ablations.
- Resolve only dataset/license items required by the registered experiment or public release; do not overstate redistribution permission from local availability.
