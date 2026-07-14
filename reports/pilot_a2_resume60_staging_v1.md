# A2-Gray Step-60 Staging

Status:
- A2-gray recovery is `queued`, not launched; no gate is declared passed.

Evidence:
- Failed source: `experiments/runs/mech_a2_gray_an12_20260713T033946Z`.
- The obsolete source checkpoint watcher was terminated alone and finalized `fail` with exit code `-15` at `2026-07-14T08:00:31Z`; no compute trainer was signaled.
- Guarded restore run: `experiments/runs/a2_step60_raw_restore_login_20260714T080108Z`, status `complete`, exit code `0`, artifacts verified.
- Restore source: `/tmp/blindgain_checkpoint_archive/mech_a2_gray_an12_20260713T033946Z/global_step_60/actor`.
- Restore verified eight raw model/optimizer shards totaling `40954297772` bytes against archived checksum-manifest SHA256 `4b04a8d660727e03d6aac89892060806cfaea50507a7bb0e3dd3ae40343d4fc9`.
- Shared-space snapshot before restore reported `970548559872` free bytes; the Tier-S guard allowed the write.
- Release queue: `experiments/runs/a2_resume60_release_queue_login_20260714T081148Z`, status `waiting`, `metric_access=false`.

Problems:
- an29 still hosts A2b and A3, while an12 now hosts A1 recovery. Starting A2 immediately would repeat an unsafe two-pilot host-memory placement.

Decision:
- The queue may launch A2 only when either A1 has completed and released an12, or both A2b and A3 have completed and released an29.
- The selected node must then pass the same no-trainer, GPU-memory, `/dev/shm`, and 650 GiB host-memory checks.
- The launcher performs a fresh full rank-set/SHA256 checkpoint audit immediately before A2 starts.

Next actions:
- Keep the restored raw state and source step-60 merged checkpoint intact.
- Let the lifecycle-only queue select the first fully released node.
- Start a replacement four-arm completion watchdog automatically after A2 launches.
