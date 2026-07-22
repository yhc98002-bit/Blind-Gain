# M5 After Seed-3 A2 Lifecycle V1

Status:
- Implementation complete, tested, committed, and launched as `experiments/runs/m5_after_seed3_a2_lifecycle_login_20260722T154457Z`.
- The lifecycle is GPU-inert while A2 runs. It cannot launch a pilot arm and cannot signal or terminate a process.
- This is an operational recovery mechanism. It does not alter M5's model, data, native reward, optimizer state, registered evaluations, or terminal step 400.

Evidence:
- Scheduler: `scripts/run_m5_after_seed3_a2_queue.py`.
- Launcher: `scripts/launch_m5_after_seed3_a2_queue.sh`.
- Fixtures: `tests/test_m5_after_seed3_a2_queue.py`.
- Verification: 64 tests pass across the new queue, segmented M5 recovery, checkpoint/evaluation watchers, storage guards, and in-process run-manifest finalization.
- Exact source boundary: `experiments/runs/m5_anchor_longhorizon_400_resume150_an12_20260721T160431Z`, step 200.
- Exact handoff: `experiments/runs/m5_step200_handoff_login_20260722T145418Z`.
- Launch commit: `b374463ca1bc34aa4d9daf265fd9667dc53e3876`.
- Initial queue state: `waiting_seed3_a2_release`; exact A2 trainer and watcher liveness both pass, every M5 segment is pending, and no restore/preflight/segment child exists.
- Post-launch noninterference check: A1 advanced from logged step 25 to 26 and A2 advanced from step 0 to 1; their original four-GPU allocations remained unchanged.

Problems:
- The previous uninterrupted M5 process accumulated about 7.25 GiB of host memory per optimizer step. Continuing from step 200 to 400 in one process is unsafe even when GPU memory is available.
- A2 currently owns `an12:0-3`; M5 must not preempt it or colocate another synchronous RL trainer.
- The checkpoint guard rejects a storage snapshot older than six hours, while one 50-step segment may run for roughly a day.

Decision:
- Wait for the exact A2 training manifest and its exact watcher manifest to be `complete`, exit zero, and artifact-verified. Also require the step-100 merged index, eight-file raw-relocation marker, and checkpoint tracker.
- At each M5 boundary, re-hash the immutable queue contract, refresh the Lustre project-quota snapshot, require at least 80 GiB free, restore the exact raw state, audit all model/optimizer/extra/dataloader state, and require two stable capacity polls plus at least 650 GiB host memory.
- Run a fresh two-round Ray startup preflight on `an12:0-3`, then launch one natural 50-step M5 segment. TP2 is retained solely for exact anchor continuity.
- Require successful training, checkpoint watcher, merged-relocation watcher, and registered evaluation queue before the next segment. Step 300 and step 400 evaluation markers are mandatory; step 400 merged weights remain on shared storage.
- Refresh quota evidence every two hours while training or finalization waits. Any failed check stops the lifecycle without cleanup, retries, process signals, or a substitute run.

Adversarial fixtures:
- A completed step-100 file set does not release an12 while the A2 watcher still reports `running`.
- A wrong arm, node, GPU set, TP layout, parent watcher, or path traversal is rejected.
- The step-300/400 evaluation queue is bound through its actual `source_training_run` field.
- The scheduler source contains no pilot-arm launcher and no process-signal path.
- The storage heartbeat refreshes before the six-hour checkpoint-guard expiry.
- A `running` child whose exact wrapper identity is absent for three consecutive polls is failed closed instead of being watched forever.

Next actions:
- Continue read-only A1/A2 monitoring; inspect queue artifacts if any fail-closed condition fires.
- After successful A2 plus watcher completion, verify that the queue refreshes storage, restores step 200, passes the new Ray preflight, and launches only segment 200-250.
- Keep A2b/A3 scheduling separate from this queue.
