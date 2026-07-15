# M2 Step-100 Lifecycle Status V3

Status:
- M2 remains `blocked`; this report makes no scientific gate decision.
- V3 supersedes the operational snapshot in V2 without modifying V1, V2, or any
  immutable run artifact.
- A1, A2b, and A3 retain complete R19 markers and independently audited 601-row
  Geometry3K-test readouts. A2-gray remains active through optimizer step 70.
- Two independent CPU-only A2 queues now cover the remaining ordered lifecycle:
  R19 first, then the locked Geometry3K readout and independent score audit.
- No pilot performance value was opened or interpreted for this lifecycle report.

Evidence:
- Queue implementation and exact A2 config: commit
  `09efc3f6d10c6fcdf84ecc910da244e7f4adde22`.
- Validation: 24 focused evaluator/auditor/queue tests passed; Python compilation,
  Bash parsing, ShellCheck, `git diff --check`, and the main-objective audit passed.
- The adversarial fixtures prove that the queue cannot launch before the exact R19
  marker, rejects any false marker check, rejects an audit from another evaluation
  run, and rejects the released node `an21`.

| Arm | Mechanical training state | R19 lifecycle | Geometry3K lifecycle |
| --- | --- | --- | --- |
| A1 real | complete | complete, exact marker | 601 rows; independent audit pass; `0 / 0 / 0` static, score, strict mismatches |
| A2 gray | running; step 70 | queue `waiting_training` | queue `waiting_r19_marker` |
| A2b no-image | complete | complete, exact marker | 601 rows; independent audit pass; `0 / 0 / 0` static, score, strict mismatches |
| A3 caption | complete | complete, exact marker | 601 rows; independent audit pass; `0 / 0 / 0` static, score, strict mismatches |

- A2 training run:
  `experiments/runs/mech_a2_gray_resume60_retry2_an12_20260715T165701Z`,
  single-node placement on `an12:0-3`.
- Primary retention watcher:
  `experiments/runs/pilot_resume60_checkpoint_watch_mech_a2_gray_resume60_retry2_login_20260715T170029Z`.
- R19 queue:
  `experiments/runs/pilot_step100_eval_queue_a2_gray_login_20260715T211716Z`;
  observed `waiting_training` at poll 18.
- Geometry3K queue:
  `experiments/runs/pilot_geo3k_step100_queue_a2_gray_login_20260715T213231Z`;
  observed `waiting_r19_marker` at poll 3 with
  `performance_values_inspected=false`.
- The Geometry3K queue pins the exact training run, step-100 checkpoint, R19 marker,
  permanent node, one TP1 GPU, 601-row source, and frozen scoring contract. Terminal
  completion additionally requires the independent audit to bind to that exact child
  evaluation and report all structural checks true with zero mismatch counts.
- `an21` is released and excluded from this queue's accepted node set. No new run is
  scheduled there.

Problems:
- A2-gray still requires steps 71-100, step-80/100 checkpoint retention, R19
  evaluation, the 601-row Geometry3K readout, and its independent audit.
- Four-arm joins, paired intervals, StrictGain accounting, hurdle/rank analyses,
  and `reports/pilot_4arm_seed1_results_v1.md` remain prohibited until the fourth
  audited arm lands.

Decision:
- Preserve all completed per-item artifacts unchanged and keep scientific values
  unopened until the four-arm lifecycle is complete.
- Let the two committed queues enforce dependency order and capacity checks. Neither
  queue sends process signals or allocates a GPU while waiting.
- Keep M11 fail-closed until all four exact R19 markers validate.

Next actions:
- Monitor A2 and the primary retention watcher mechanically.
- Let the R19 queue consume `an12:4-7` only after training and retention complete.
- Let the Geometry3K queue consume one free TP1 GPU only after the exact R19 marker.
- Build the registered seed-1 report only after the fourth independent audit passes.

Machine-readable companion:
- `reports/m2_step100_lifecycle_status_v3.json`.
