# Pilot Seed-2 Execution Status V2

Status:
- This is an operational status report, not an M3 scientific pass.
- A1-real, A2-gray, and A2b-no-image have completed step 100. A2 and A2b both exited with code 0.
- A3-caption is healthy at step 62 on `an29` GPUs `0,1,2,3`; no fatal training-log pattern is present.
- Performance values remain unopened.

Evidence:
- Check time: `2026-07-21T07:48:37Z`.
- A2 run: `experiments/runs/mech_a2_gray_seed2_resume20_an12_20260719T125918Z`.
- A2b run: `experiments/runs/mech_a2b_noimage_seed2_resume20_an29_20260719T125447Z`.
- A3 run: `experiments/runs/mech_a3_caption_seed2_an29_20260720T125144Z`.
- A3 GPU utilization was 100% on all four assigned GPUs at the check; host `MemAvailable` was `547,704,984` KiB.
- Shared Lustre project usage was `1,379,202,620` KiB, leaving about 184.7 GiB under the conservative 1,500-GiB ceiling.
- Login-node `/tmp` had about 225 GiB free.

Problems:
- The original pilot checkpoint watchers serialized all steps behind the step-60 evaluation marker. This left step-80/100 raw states for completed arms on shared storage and reduced conservative headroom to about 39.7 GiB during the repair.
- One A2b shutdown log line reports a Ray worker receiving SIGTERM. The parent training manifest completed with exit code 0 after step 100, so this is retained as shutdown evidence rather than classified as a training failure.
- Step-60 and step-100 registered evaluations remain pending; no result may be opened before the fail-closed multi-arm lifecycle audit.

Decision:
- Commit `dd923ae` changes both watcher variants to retain the step-60 merged checkpoint for evaluation while continuing step-80/100 merge and raw retention. The deferred step-60 merged relocation occurs only after the exact evaluation marker arrives.
- Ten focused regression tests pass, including fixtures that require steps 80 and 100 to precede the deferred step-60 barrier.
- The three old waiting-only watchers were superseded with SIGTERM at `2026-07-21T07:08:58Z`; their wrappers recorded immutable `fail/-15` terminal states. No training process was signaled.
- Replacement watchers:
  - `experiments/runs/pilot_resume_checkpoint_watch_mech_a2_gray_seed2_resume20_login_20260721T070922Z`.
  - `experiments/runs/pilot_resume_checkpoint_watch_mech_a2b_noimage_seed2_resume20_login_20260721T073022Z`.
  - `experiments/runs/pilot_checkpoint_watch_mech_a3_caption_seed2_login_20260721T071146Z`.

Verified retention:
- A2 step 100 raw archive checksum-manifest SHA256: `2d6ede7625558f3869221eb6cbbdc079a4a03e15be8016405988c18bd626bb22`.
- A2b step 80 raw archive checksum-manifest SHA256: `5131d33e96b6c117b9d5d4ea040c2ab3bc5c7497953b6b60b7d51f757b99ddb9`.
- A3 step 60 raw archive checksum-manifest SHA256: `3c3d8d789839a2d6f22c955d2a27815baad814899005933ab98b27432581371f`.

Next actions:
- Finish A2b step-100 merge and raw retention under the replacement watcher.
- Continue A3 to fixed step 100; its watcher now processes later checkpoints independently of the step-60 evaluation marker.
- Run registered step-60/100 evaluations and the complete seed-2 lifecycle audit before opening the four-arm readout.
- Use the released `an12` node for the next registered priority after its fail-closed startup and storage preflights pass.
