# Stage 0 Proposal Gate Audit V2

Status:
- Mechanical accounting remains `conditional`; this document does not declare a PI gate.
- The 100-step engineering anchor, final checkpoint, and deterministic pre/post evaluation now exist.
- Published reproduction remains `fail`: no published target/tolerance is defined, and the native metric record is discontinuous.
- The predecessor `reports/stage0_proposal_gate_audit.md` and `.json` remain unchanged and are superseded by this version.

Evidence:
- Machine checklist: `reports/stage0_proposal_gate_audit_v2.json`.
- Engineering-anchor completion: `reports/grpo_reproduction_recovery_v2.md`.
- Endpoint evaluation: `reports/grpo_anchor_step100_prepost_v1.md` and `.json`.
- Metric continuity failure: `reports/anchor_metric_continuity_audit_v1.md` and `.json`.
- Current dataset/license inventory: `reports/dataset_license_triage_v3.md` and `reports/license_log_v3.csv`.

Checklist:

| Item | Status | Evidence and rationale |
| --- | --- | --- |
| cluster_bringup | pass | Stage-0 CUDA/DDP/FSDP/NCCL inventory and smoke artifacts remain valid. |
| model_downloads | partial | Qwen2.5-VL 3B/7B and required current evaluators exist; the broader optional editor/detector inventory is incomplete. |
| dataset_acquisition | partial | Geometry3K and ViRL39K are usable; proposal-wide acquisition/release provenance is not complete for every listed dataset. |
| license_log | partial | V3 records ten artifacts; several image-derived datasets remain under conservative source-image/provenance review. |
| published_grpo_reproduction | fail | The 100-step run is an engineering anchor with documented recipe deviations and an incomplete native metric history. |
| reproduction_tolerance_defined | fail | No published target and tolerance were registered before observing this run. |
| reward_parser_audit | pass | Canonical-v2 fixtures and the exact 320-row native/canonical agreement audit exist; the below-0.95 agreement warning remains explicit. |
| config_diff_audit | pass | The resolved EasyR1 reference and anchor differ field by field in both Markdown and machine JSON. |
| image_preprocessing_audit | pass | The exact Qwen visual-grid audit covers all 1,288 frozen pilot rows, catches the old double-resize failure, and reports zero mismatches after repair. |
| chat_template_audit | partial | Template path/hash and rendered evaluation prompts are pinned, but the originally requested dedicated 8-train/8-validation rendered-prompt artifact is not yet published. |
| deterministic_eval_audit | pass | V2 verifies base/step-100 output hashes, identical item content/contracts, and paired endpoint metrics. |
| checkpoint_discipline | pass | Step-100 merge, hashes, latest-raw retention, shared cleanup, and immutable relocation records are complete. |

Problems:
- The logical AND for a full `pass` is false because multiple checklist rows are partial or fail.
- The anchor's favorable endpoint cannot be used to define a post hoc reproduction tolerance.
- Dataset acquisition and release permission are separate: local evaluation availability does not clear third-party image redistribution.

Decision:
- Retain `overall_proposal_stage0=conditional`; do not promote it to pass.
- Use the completed run as an engineering anchor and keep the published-reproduction limitation explicit in every downstream report.

Next actions:
- Publish the dedicated rendered chat-template sample audit.
- Complete remaining dataset/license provenance only where it blocks the registered experiments or release.
- Finish the L3 replacement smoke and step-100 gray/noise ablations without changing the anchor claim.
