# M5 Checkpoint Evaluation Plumbing V1

Status:
- The registered M5 checkpoint evaluation path is implemented, tested, committed at `6ee812f`, and pushed to `origin/agent/gate2-recovery`.
- Step-150 Geometry3K and R19 real-image inference are active. M5 remains blocked overall until recovery reaches fixed step 400 and all registered readouts complete.

Evidence:
- Geometry3K launcher: `scripts/launch_m5_geo3k_checkpoint_eval.sh`; exact 601-row test split, greedy decoding, 2,048-token limit, seed `20260710`, canonical-v2 plus pilot-reward scoring, TP1.
- R19 launcher: `scripts/launch_m5_fliptrack_checkpoint_eval.sh`; exact R19 SHA256 `e1dde984...`, greedy decoding, 32-token limit, TP1 replicas.
- Joint finalizer: `scripts/finalize_m5_step_evaluation.py`; requires exact checkpoint/source identity, 601 Geometry3K rows, 1,200 R19 pairs, locked prompt/decoding, and immutable source-manifest snapshots.
- Step-400 finalization fails closed unless real, gray, and noise R19 cells are all structurally complete. Steps 150/200/300 permit only the registered real-image descriptive cell.
- Queue: `scripts/run_m5_checkpoint_evaluation_queue.py`; waits for merged checkpoints and two stable capacity polls, discovers existing immutable children after restart, never preempts processes, and never reads performance fields.
- Future recovery launch now starts the step-200/300/400 evaluation queue before the first recovery optimizer step. Evaluation remains independent of raw-state or merged-checkpoint relocation.
- Tests: 25 focused tests passed in 170.70 seconds; ShellCheck and Python compilation passed.
- Adversarial fixtures reject cross-step resume substitution, checkpoint substitution, malformed GPU snapshots, duplicate restart children, and step-400 completion without gray/noise cells.

Active step-150 runs:

| Role | Run | Placement | State at launch audit |
| --- | --- | --- | --- |
| Capacity/restart queue | `experiments/runs/m5_checkpoint_evaluation_queue_login_20260718T051317Z` | login CPU | running |
| Geometry3K | `experiments/runs/m5_geo3k_step150_an12_gpu4_20260718T051839Z` | `an12:4`, TP1 | running |
| R19 real | `experiments/runs/m5_r19_step150_real_an12_20260718T051758Z` | `an12:5,6,7`, 3x TP1 | running |
| Joint structural watcher | `experiments/runs/m5_step150_evaluation_watch_login_20260718T052100Z` | login CPU | running |

Problems:
- The original M5 trainer remains failed from the documented Ray host-memory OOM. No scientific performance value from post-step-150 failed-process logs is used.
- The raw step-150 restore has copied and source-verified all eight shards, while its independent checkpoint audit is still running. This does not block inference from the already hash-bound merged checkpoint.

Decision:
- Evaluate step 150 now on disjoint `an12` GPUs because the merged checkpoint is complete and evaluation is explicitly decoupled from relocation/optimizer-state restore.
- Keep the fixed-terminal recovery queue on `an29` GPUs `2,5,6,7` after A1 seed 2 releases them and the 650-GiB host-memory admission passes.
- Do not mark M5 passed and do not open intermediate scientific values.

Next actions:
- Let the step-150 watcher aggregate cached predictions and emit `step150_evaluation_complete.json` after both structural inputs pass.
- Let the raw restore audit complete; the existing recovery-capacity queue then waits for A1 seed-2 completion and two stable capacity polls before resuming M5 from step 150.
- Automatically evaluate steps 200, 300, and 400; require the gray/noise floor cells at step 400 before the terminal marker.
