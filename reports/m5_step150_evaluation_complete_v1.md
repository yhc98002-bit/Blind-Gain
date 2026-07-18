# M5 Step-150 Evaluation Completion V1

Status:
- The registered step-150 structural evaluation is complete.
- Geometry3K contains exactly 601 rows and R19 real-image evaluation contains
  exactly 1,200 pairs.
- No performance value was opened by the queue or this completion report.
- M5 itself remains `blocked`; this is not the fixed-terminal step-400 result
  and is not a scientific gate decision.

Evidence:
- Machine report: `reports/m5_step150_evaluation_complete_v1.json`.
- Source marker:
  `experiments/runs/m5_anchor_longhorizon_400_an12_20260716T173030Z/evaluations/step150_evaluation_complete.json`.
- Geometry3K run:
  `experiments/runs/m5_geo3k_step150_an12_gpu4_20260718T051839Z`, complete,
  exit code 0.
- R19 run:
  `experiments/runs/m5_r19_step150_real_an12_20260718T051758Z`, complete with
  three 400-pair shards.
- R19 aggregate:
  `experiments/runs/fliptrack_aggregate_m5_step150_m5_anchor_longhorizon_400_an12_20260716t173030z_real_20260718T053827Z`, complete, exit code 0.
- Joint watcher:
  `experiments/runs/m5_step150_evaluation_watch_login_20260718T052100Z`,
  complete, exit code 0.
- Queue:
  `experiments/runs/m5_checkpoint_evaluation_queue_login_20260718T051317Z`,
  complete, exit code 0.

Problems:
- Gray and noise R19 cells are not registered at step 150; they remain
  required at the registered terminal step 400.
- The original M5 parent remains a preserved failed lifecycle after its host
  memory incident.

Decision:
- Accept the step-150 evaluation lifecycle as structurally complete without
  interpreting its metrics.
- Keep the exact step-150 raw restore as the recovery source.
- Let the existing capacity queue start fixed-terminal recovery only after A1
  seed 2 releases `an29` GPUs 2,5,6,7 and host available memory reaches the
  registered 650-GiB admission threshold.
