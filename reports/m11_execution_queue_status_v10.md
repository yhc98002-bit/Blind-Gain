# M11 Generalization Execution Queue Status V10

Status:
- The full-only login-node recovery queue is `running` in
  `waiting_m2_priority` state.
- Zero M11 child GPU jobs are running; all 18 full cells remain pending.
- M11 remains `blocked` until the full matrix and machine audit complete.

Evidence:
- Queue run:
  `experiments/runs/m11_generalization_full_recovery_login_20260715T182317Z`.
- Launch commit: `43015791c28989a226f85117012eb8a21f7912da`.
- Config SHA256:
  `13801b90d341ac6229f1110a69a58ea0ec1b3a4faf99bf7a037287f7b6042171`.
- Scheduler placement: login node, no GPU, TP width `0`, replica count `0`.
- Pinned smoke evidence: six validated cells; queue cells: 18 full cells only.
- M2 priority state: `false`; A1, A2-gray, A2b, and A3 exact step-100
  FlipTrack markers are all currently absent.
- A second launcher invocation exited `73` after detecting this active queue;
  no duplicate scheduler was created.

Decision:
- Leave the watcher active. It polls without GPU allocation while any M2 marker
  is absent.
- Once all four markers validate, require two consecutive free-capacity polls
  before independent TP1 child jobs can launch on `an29`.
- Do not inspect or report model performance from smoke or future full cells
  until the registered audit builder completes the matrix.

Next actions:
- Finish M2 checkpoint retention and step-100 evaluation first.
- Monitor the queue manifest/state for fail-closed termination or M2-gate
  transition.
- Publish M11 results only from `reports/generalization_audits_v1.json` after
  its conjunction status is computed.
