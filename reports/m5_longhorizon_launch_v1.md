# M5 Long-Horizon Launch V1

Status:
- Active. The restore-and-resume engineering precondition passed all eight checks, and the registered fixed step-400 continuation is running.
- M5 remains blocked pending training, registered checkpoint evaluations, and the terminal readout. No PI gate is declared.

Evidence:
- Engineering audit: `reports/m5_restore_resume_integrity.json` and `.md`, created `2026-07-16T17:28:14Z`; status `pass`; 8/8 checks true; `scientific_gate_decision=null`.
- One-step child: `experiments/runs/m5_anchor_resume_integrity_step101_an12_20260716T164403Z`, complete at `2026-07-16T17:26:18Z`, exit 0.
- Step-101 checkpoint audit: `experiments/runs/m5_integrity_queue_login_20260716T163532Z/step101_checkpoint_audit.json` plus SHA256 inventory; files were stable during hashing.
- Long-horizon run: `experiments/runs/m5_anchor_longhorizon_400_an12_20260716T173030Z`.
- Placement: an12 GPUs 0/1/2/3, TP2, two replicas, single-node synchronous RL.
- Source commit: `65d1a17043c34943cf7fd2f8496e39d6b3b24373`; config hash: `73ff58bd3b6a5a9a190f6f379a927bc6405c88001bd524f61846ffb22996f48c`.
- Fixed target: step 400; terminal with no extension. Registered evaluation steps: 150, 200, 300, 400.
- Retention watcher: `experiments/runs/m5_checkpoint_watch_login_20260716T173053Z`.
- Merged-relocation watcher: `experiments/runs/m5_merged_relocation_watch_login_20260716T173053Z`; evaluation remains independent of relocation.

Problems:
- The terminal scientific result is not available. Steps 150/200/300 are descriptive; only the registered step-400 versus step-100 geometry contrast determines the terminal category.
- The step-101 integrity checkpoint currently occupies shared storage and must not be moved while its just-completed audit is being reconciled into provenance.

Decision:
- Let the fixed run continue untouched to step 400 under the merged R1 rule.
- Do not stop, extend, or rerun based on intermediate curve shape.

Next actions:
- Monitor process health and checkpoint lifecycle without opening scientific metrics early.
- Score the registered checkpoints and publish `reports/anchor_longhorizon_400_results_v1.md` after terminal completion.
