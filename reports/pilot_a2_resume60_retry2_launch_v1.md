# A2 Gray Step-60 Retry2 Launch

Status:
- `blocked`: M2 seed 1 is not complete and no PI gate is declared.
- The externally released `an21` attempt is finalized `fail`; A2 was relaunched from the original verified step-60 state on `an12:0-3`.
- A1, A2b, and A3 training manifests are complete. The replacement mechanical watchdog currently reports `3/4` complete.

Evidence:
- Released attempt: `experiments/runs/mech_a2_gray_resume60_an21_20260714T145532Z`.
- Release evidence: `release_finalization.json`, SHA256 `c77e555caa71f1555dfa0717e47695c1b0ea6699911812b1e86e384e13071612`.
- The released attempt wrote no `global_step_*` directory and no checkpoint tracker. Logged steps 61-64 are explicitly discarded as uncheckpointed work; the attempt is not included in the resumed trajectory.
- Recovery implementation commit: `9b4564f97fca7d35d17385a4f34a3b3b61943a7d`. The finalizer rejects any released attempt containing durable resume state; targeted recovery tests: `10 passed`.
- New training run: `experiments/runs/mech_a2_gray_resume60_retry2_an12_20260715T165701Z`.
- Placement: one synchronous EasyR1 job on `an12`, GPUs `0,1,2,3`, TP1, four rollout replicas. Placement follows the PI single-node rule.
- Start: `2026-07-15T17:00:06Z`; git `9b4564f97fca7d35d17385a4f34a3b3b61943a7d`; config SHA256 `2f41f7155e2a84c7da6e6d62bf3697843c35604f2b0c973c4f8466778b9532e7`; filtered-data SHA256 `f3d88dd1e52ccef833f266880e487eef252193f774c1076f7dfbccd180b450e6`.
- The 40,954,358,136-byte step-60 source passed a 13-file stable-hash audit. Audit SHA256: `f85177ba6fe8f90bc9e11d04c24f508eaee63fb0d2890cc377f734d4f410536f`; file-checksum manifest SHA256: `81d2fd7641099bf674f6c3deef641e0d99a87ae87c4c9893a9ed0acf44771105`.
- The effective config changed only `trainer.experiment_name`, `trainer.load_checkpoint_path`, and `trainer.save_checkpoint_path`; `scientific_config_changed=false`.
- Host preflight observed 851.9/851.8 GiB available before/after probing, above the 650 GiB floor. Ray temporary paths are under `/dev/shm/bg-ray-981ef767b15b`.
- Initial runtime check found four CUDA allocations of approximately 45.4 GiB, live Ray services/workers, and no registered fatal log signature.
- Shared quota snapshot at `2026-07-15T13:52:15Z`: 619,522,174,976 bytes free of 1,610,612,736,000; checkpoint guards remain enabled.
- Health monitor: `experiments/runs/gpu_health_16x60m_login_20260715T170319Z`, observing exactly `an12` and `an29` every 30 seconds for one hour.
- Completion watchdog: `experiments/runs/m2_pilot_completion_watchdog_login_20260715T171008Z`; config SHA256 `f3a4a3b8d4e1b3b593b84234ecde01b14f8ce754918976f07a9f4fe50ee56d57`; current outcomes are A1/A2b/A3 complete and A2 running.
- Registered step-60 R19 evaluations are active on `an29`: A2b on GPUs 0-3 and A3 on GPUs 4-7. Both use four independent TP1 replicas, real images, greedy decoding, 32 output tokens, prompt-contract SHA256 `7ac39f53a2a824490fc5ee22671a888d2d79d55e1d8351919006d7d71c7a8f3f`, and locked R19 SHA256 `e1dde98451e1c7473906637c029713ab4f95ab4f7c915bd035f697953bf2ffb2`.

Problems:
- A2 still has steps 61-100 remaining from the durable source point; M2 cannot close until this run and all registered readouts complete.
- A2b/A3 retention watchers are waiting for their step-60 FlipTrack completion markers.
- A1's original retention watcher failed closed after a code-bundle hash change; its completed checkpoints remain intact and require the audited watcher-recovery path.
- Step-100 and geo3k-test scoring remain pending. No result interpretation is made here.

Decision:
- Treat the `an21` allocation release as an operational interruption, not a scientific observation.
- Discard all uncheckpointed work from that attempt and resume again from the immutable original step-60 state in a new namespace.
- Use `an12` for A2 because it is permanent, has sufficient host-memory headroom, and currently runs no other pilot trainer. Use `an29` for disjoint checkpoint evaluations.

Next actions:
- Monitor A2 through its first post-resume durable progress and the one-hour health window.
- Aggregate each completed R19 evaluation, issue its fail-closed step-60 marker, and let the existing retention watchers process steps 80/100.
- Restart A1 retention with the failed-watcher recovery lineage, preserving only its final merged checkpoint on shared storage.
- Run the remaining registered step-100, geo3k-test, accounting-identity, and mechanism readouts before producing `reports/pilot_4arm_seed1_results_v1.md`.
