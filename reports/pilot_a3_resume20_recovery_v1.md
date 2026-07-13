# A3 Caption Step-20 Recovery V1

Status:
- Recovery run is active; this report does not mark M2 or any scientific gate passed.
- The recovered workers are resident on an29 GPUs 4-7 and checkpoint loading is in progress.
- No reward, loss, accuracy, or validation value has been inspected.

Evidence:
- Run: `experiments/runs/mech_a3_caption_resume20_an29_20260713T144233Z`.
- Watcher: `experiments/runs/pilot_resume_checkpoint_watch_mech_a3_caption_resume20_login_20260713T144302Z`.
- Git: `f32bc53647b60bd4eba0f9a693267d946b336e5d` (pushed to `origin/agent/gate2-recovery` before launch).
- Placement: an29 GPUs 4-7, TP1, four rollout replicas, seed 1. A2b remains isolated on GPUs 0-3.
- Source config SHA256: `573b1ca7e26f8365ba140ecb40d76f75f23b8b2ff399c9b45d8200740e2d8826`.
- Resume config SHA256: `45ae4c0b5573c2c6cfbab75704c88a4a357c1da7f4ac2de2330d1cf3f20c0945`.
- Machine config audit: `experiments/runs/mech_a3_caption_resume20_an29_20260713T144233Z/resume_config_audit.json`; status `pass`.
- Config differences are restricted to `trainer.experiment_name`, `trainer.save_checkpoint_path`, and `trainer.load_checkpoint_path`. The registered image condition, reward, model, data, seed, optimizer, max steps, save cadence, validation cadence, and rollout settings are unchanged.
- Load path: `checkpoints/pilot/mech_a3_caption/global_step_20`.
- New save path: `checkpoints/pilot/mech_a3_caption_resume20`; registered remaining saves are 40, 60, 80, and 100.
- Raw restore marker: `checkpoints/pilot/mech_a3_caption/global_step_20/actor/RAW_STATE_RESTORED_FOR_RESUME.json`; eight model/optimizer shards were re-read and matched the archive manifest SHA256 `ec04fcb96992d0722667d9cef502cbf20d5ffb1e6721819400e4e8d28c82d2a4`.
- Shared-storage guard passed for 40,954,297,772 required bytes with 1,045,847,011,924 projected free bytes after restore.
- Temp probe: `experiments/runs/mech_a3_caption_resume20_an29_20260713T144233Z/ray_tempdir_probe.json`; status `pass` for driver `tempfile`, driver multiprocessing, Ray worker `tempfile`, Ray worker multiprocessing, and Ray session paths.
- Runtime root: `/dev/shm/bg-ray-c58d9441255f`; all four live A3 workers expose `TMPDIR`, `TMP`, `TEMP`, and `RAY_TMPDIR` under this root.
- At the first residency check, all four workers were loading model shards and GPUs 4-7 each held approximately 49.1 GiB.
- Replacement mechanical completion watchdog: `experiments/runs/m2_pilot_completion_watchdog_login_20260713T144354Z`.

Problems:
- Recovery success is not established until optimizer progress beyond global step 20 is durably logged and a later checkpoint is written.
- an29 `/tmp` remains full due mostly to inaccessible/foreign content. The recovered job no longer uses it for runtime temp files.

Decision:
- Continue the recovery unchanged and exclude failed source steps 21-26 from analysis.
- Treat the additional validation performed by EasyR1 at checkpoint load as resume behavior; do not change the registered config to suppress it.
- Keep the old step-20 raw archive until a later resume checkpoint is hash-verified.

Next actions:
- Verify the explicit step-20 load message, first post-resume optimizer step, and checkpoint watcher behavior.
- Use the 60-minute 16-GPU monitor to audit process survival, progress, storage, temperature, and utilization without sending signals.
