# A2b Retry-1 Operational Failure V1

Status:
- `mech_a2b_noimage_retry1` failed before its first checkpoint at
  `2026-07-13T10:39:29Z`.
- M2 remains `blocked`; this is an operational failure record, not a scientific
  result.
- No reward, loss, accuracy, or validation value was inspected.

Evidence:
- Training run:
  `experiments/runs/mech_a2b_noimage_retry1_an29_20260713T100420Z`.
- Run manifest status: `fail`; exit code: `1`; node: an29; GPUs: 0,1,2,3;
  TP: 1; replicas: 4; seed: 1.
- Git: `12b0817432e66cd2f387c704e384431a6e8a8b8e`.
- Effective-config SHA256:
  `d00a8d710e159d87823d8a5beb0e0c1d8870791c326fb4ef1357af92a622137f`.
- Data-manifest SHA256:
  `f3d88dd1e52ccef833f266880e487eef252193f774c1076f7dfbccd180b450e6`.
- No `global_step_*` directory exists in
  `checkpoints/pilot/mech_a2b_noimage_retry1`; no state can be resumed or
  mistaken for a completed checkpoint.
- The traceback records a 15.07-GiB allocation request with 27.18 GiB reserved
  but unallocated. PyTorch explicitly recommends
  `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` for this condition.
- The empty-tree checkpoint watcher was terminated and finalized `fail` at
  `2026-07-13T11:10:49Z`; no retention action occurred.

Problems:
- CUDA allocator fragmentation caused an OOM during the first update even
  though aggregate reserved-but-unallocated memory exceeded the failed request.
- The prior M11 queue treated the resulting free GPUs as capacity. It was stopped
  after one poll and before any cell launch; all 24 cells remain pending.

Decision:
- Start retry 2 from the registered base model because retry 1 has no checkpoint.
- Preserve every scientific configuration field. Change only immutable output
  identity and set the operational allocator environment to
  `expandable_segments:True`.
- Require successful completion of both an29 blind arms before M11 may evaluate
  GPU vacancy. A failed-arm vacancy cannot satisfy this release condition.

Next actions:
- Commit and test the allocator and M11 release-gate changes.
- Launch A2b retry 2 on an29 GPUs 0-3 and verify manifest/config invariants.
- Relaunch M11 as a dormant login-node queue and verify its release evidence
  remains false while either blind arm is incomplete.
