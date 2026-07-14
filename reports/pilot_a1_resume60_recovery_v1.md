# A1 Step-60 Recovery

Status:
- A1 recovery is `running`; no gate is declared passed.

Evidence:
- Recovery run: `experiments/runs/mech_a1_real_resume60_an12_20260714T080855Z`.
- Launch commit: `7341ddf77d1a14cbeba2a102ffb7396b031d1e8e`, pushed to `origin/agent/gate2-recovery` before launch.
- Placement: an12 GPUs `0,1,2,3`, TP1, four replicas, one synchronous pilot trainer on the node.
- Preflight `MemAvailable`: `899277564` KiB initially and `899154248` KiB immediately before launch, above the 650 GiB floor.
- Source: `checkpoints/pilot/mech_a1_real/global_step_60`.
- Checkpoint audit: `experiments/runs/mech_a1_real_resume60_an12_20260714T080855Z/resume_checkpoint_audit.json`.
- The audit verified four model ranks, four optimizer ranks, four extra-state ranks, and dataloader state: 13 stable files totaling `40954358136` bytes. Checksum-manifest SHA256: `330c03440fbbafd927bf87a607583c0818bbb6783a761c0ba43e8c10ca7411da`.
- Resume config SHA256: `511e6c3276e37b893aeb50be643036635dbd9be165188e8f7e8ccf7d4247e1ab`; audit records `scientific_config_changed=false`.
- Ray temporary-directory probe passed with all driver, worker, multiprocessing, and Ray session paths under job-local `/dev/shm`.
- Checkpoint watcher: `experiments/runs/pilot_resume60_checkpoint_watch_mech_a1_real_resume60_login_20260714T081118Z`; it handles only steps 80 and 100.
- Post-launch observation: all four assigned GPUs reached 100% utilization with about 51.5 GiB allocated each while the log explicitly loaded model, optimizer, and extra-state ranks from the source `global_step_60`; host `MemAvailable` remained about 706 GiB.

Problems:
- The first monitor intervals occurred during CPU/Ray initialization and are expected warnings. Device loading and resumed step-60 validation are now observed; the first post-resume optimizer step is still pending at this report revision.

Decision:
- Keep the job running and require subsequent process/log/GPU progress plus host-memory headroom before describing recovery as stable.
- Preserve the source step-60 merged checkpoint for the registered FlipTrack readout.

Next actions:
- Observe the one-hour health run and checkpoint watcher.
- On step 80, merge/hash and apply latest-raw retention; retain final step 100 merged output on shared storage.
- Do not inspect or interpret pilot performance metrics during operational monitoring.
