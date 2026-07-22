# M5 Segmented Recovery Plan V1

Status:
- Step 200 is a complete recovery boundary, not a scientific stopping point.
- The 200-to-250 segment launcher is implemented and tested but has not yet taken an optimizer step.
- The registered terminal remains step 400 under the merged M4 rule.

Evidence:
- Source run: `experiments/runs/m5_anchor_longhorizon_400_resume150_an12_20260721T160431Z`.
- Step-200 merge: `experiments/runs/easyr1_checkpoint_merge_m5_anchor_longhorizon_400_step200_an12_20260722T135506Z`.
- Step-200 evaluation marker: `experiments/runs/m5_anchor_longhorizon_400_resume150_an12_20260721T160431Z/evaluations/step200_evaluation_complete.json`.
- Raw and merged archive size: 54,452,413,276 bytes; embedded checksum target counts are 8 raw files and 14 merged files.
- Successful exact-process handoff: `experiments/runs/m5_step200_handoff_login_20260722T145418Z`; status `handoff_complete`, SIGTERM, no SIGKILL.
- Observed recent host-memory slope: 7.2536 GiB per optimizer step. `MemAvailable` recovered from 258,727,096 KiB at handoff authorization to more than 860,000,000 KiB after exact process cleanup.
- Fifty focused M5/restore/watcher/manifest tests pass.

Problems:
- A single uninterrupted Ray process is unsafe to carry from step 200 to step 400 because worker/offload host memory grows approximately linearly. Ray object-store use was not the source of the growth.
- The first handoff controller used SIGINT, which the trainer ignored. It timed out without escalation and did not alter the checkpoint.
- The existing anchor recipe uses rollout TP2 for the 3B model. Segmented continuation retains TP2 solely for exact checkpoint/config continuity, although the standing placement preference is TP1 for models at or below 7B.

Decision:
- Execute four natural process segments: 200-to-250, 250-to-300, 300-to-350, and 350-to-400.
- Each segment loads the complete model, optimizer, constant scheduler, extra-state, and dataloader checkpoint. The segment process sets `trainer.max_steps` to its endpoint only to exit naturally; reward, data, model, sampling, optimizer, validation cadence, save cadence, and scientific terminal are unchanged.
- Each launcher refuses an existing target checkpoint, a stale or mismatched Ray preflight, fewer than 650 GiB available host memory, occupied GPUs, an uncommitted contract, or an invalid restore audit.
- One segment runs at a time on one node. Evaluation stays independent of archive relocation. Step 300 and step 400 receive the registered evaluations; step 250 and step 350 remain operational checkpoints.

Next actions:
- Restore and SHA256-audit the step-200 raw state from the login-node archive.
- Run a fresh two-round Ray runtime/GPU preflight on `an12:0-3`.
- Launch 200-to-250 only after both artifacts pass, then inspect operational health without opening performance values.
- At step 250, merge and verify before latest-raw retention expires step 200; repeat the same restore/preflight discipline for later segments.
