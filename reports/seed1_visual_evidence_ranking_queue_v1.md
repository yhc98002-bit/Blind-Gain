# Seed-1 Visual-Evidence Ranking Queue V1

Status:
- Running on an12 GPUs 4–7 as nine immutable TP1 cells.
- The queue and every child manifest retain `performance_values_opened=false`; this
  report contains lifecycle counts only.

Evidence:
- Active queue:
  `experiments/runs/d1_visual_evidence_matrix_queue_login_20260717T175951Z`.
- Placement: an12 GPUs 4, 5, 6, and 7; at most four independent TP1 replicas. M5
  processes on GPUs 0–3 are untouched.
- Queue launch git hash: `fe23061a3d2767d1e900342b38728d66e608e74b`.
- Config SHA256:
  `6abd53bbf7742167aaf672dcc74633465f7d9378220067c651ce4575375b67bf`.
- Candidate registry SHA256:
  `fa9456941a730e174b1ed4bb4caefc151778e3f1adc0ca77db941955a4215f81`.
- The queue records one child run directory per model/condition cell and launches a
  replacement only after the preceding child manifest reaches an exact terminal
  state.
- Explicit `--resume` validates queue placement, config hash, data hash, active child
  manifests, and remote worker PIDs. Resume events are appended to both queue state
  and manifest.

Problems:
- The first login-node `nohup` attempt at
  `experiments/runs/d1_visual_evidence_matrix_queue_login_20260717T175112Z`
  exited before creating state. Its log is empty and no child GPU run was launched.
  The empty directory is preserved as failed launch evidence.
- The replacement uses a named `tmux` session. No scientific input or score changed.

Decision:
- Treat only the state-bearing `20260717T175951Z` queue as authoritative.
- Fail closed on a dead child worker or any cell/hash mismatch; never reuse a partial
  output in place.

Next actions:
- Wait for all nine cell manifests and exact 1,200-row outputs.
- Run the frozen finalizer and then the independent raw-score recomputation audit.
