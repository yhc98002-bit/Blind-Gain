# Stale ST3 claim release — 2026-08-17

Run st3_std_seed1_7b_an29_20260817T162124Z died at config parse (val_files
null); manifest status=fail, all 8 an29 GPUs idle at 2 MiB, no log advancing.
Its claims were left behind because the launcher did not release them on a
failed liveness check — fixed in the same commit. Claims removed:
  an29_gpu0.claim: {"gpu":0,"run_id":"st3_std_seed1_7b_an29_20260817T162124Z","pid":null,"eval_run_dir":"experiments/runs/st3_std_seed1_7b_an29_20260817T162124Z","written_utc":"2026-08-17T16:21:24Z","written_by":"scripts/launch_st3_7b_arm.sh"}
  an29_gpu1.claim: {"gpu":1,"run_id":"st3_std_seed1_7b_an29_20260817T162124Z","pid":null,"eval_run_dir":"experiments/runs/st3_std_seed1_7b_an29_20260817T162124Z","written_utc":"2026-08-17T16:21:26Z","written_by":"scripts/launch_st3_7b_arm.sh"}
  an29_gpu2.claim: {"gpu":2,"run_id":"st3_std_seed1_7b_an29_20260817T162124Z","pid":null,"eval_run_dir":"experiments/runs/st3_std_seed1_7b_an29_20260817T162124Z","written_utc":"2026-08-17T16:21:27Z","written_by":"scripts/launch_st3_7b_arm.sh"}
  an29_gpu3.claim: {"gpu":3,"run_id":"st3_std_seed1_7b_an29_20260817T162124Z","pid":null,"eval_run_dir":"experiments/runs/st3_std_seed1_7b_an29_20260817T162124Z","written_utc":"2026-08-17T16:21:29Z","written_by":"scripts/launch_st3_7b_arm.sh"}
  an29_gpu4.claim: {"gpu":4,"run_id":"st3_std_seed1_7b_an29_20260817T162124Z","pid":null,"eval_run_dir":"experiments/runs/st3_std_seed1_7b_an29_20260817T162124Z","written_utc":"2026-08-17T16:21:31Z","written_by":"scripts/launch_st3_7b_arm.sh"}
  an29_gpu5.claim: {"gpu":5,"run_id":"st3_std_seed1_7b_an29_20260817T162124Z","pid":null,"eval_run_dir":"experiments/runs/st3_std_seed1_7b_an29_20260817T162124Z","written_utc":"2026-08-17T16:21:33Z","written_by":"scripts/launch_st3_7b_arm.sh"}
  an29_gpu6.claim: {"gpu":6,"run_id":"st3_std_seed1_7b_an29_20260817T162124Z","pid":null,"eval_run_dir":"experiments/runs/st3_std_seed1_7b_an29_20260817T162124Z","written_utc":"2026-08-17T16:21:35Z","written_by":"scripts/launch_st3_7b_arm.sh"}
  an29_gpu7.claim: {"gpu":7,"run_id":"st3_std_seed1_7b_an29_20260817T162124Z","pid":null,"eval_run_dir":"experiments/runs/st3_std_seed1_7b_an29_20260817T162124Z","written_utc":"2026-08-17T16:21:37Z","written_by":"scripts/launch_st3_7b_arm.sh"}
