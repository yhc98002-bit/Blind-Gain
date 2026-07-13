# M11 Generalization Execution Queue Status V1

Status:
- M11 remains `blocked`: no non-Qwen performance result is reported yet.
- The immutable login scheduler is active and waiting for all four M2 seed-1
  prerequisite manifests to complete before requesting a GPU.

Evidence:
- Queue run: `experiments/runs/m11_generalization_queue_login_20260713T044555Z`.
- Queue state: `waiting_prerequisites`; 24/24 cells are pending and none has
  started.
- Code commit: `598f1cc14fbd6193da6b6ad79a12379aea407505`.
- Config: `configs/eval/m11_generalization_v1.json`, SHA256
  `ad3258f3c1446ed1a2d5010fb57f405b897ed0439cf284fc0a17b2fe35c9214f`.
- Placement: the scheduler runs on the login node with no GPU. Child jobs are
  restricted to one free GPU on `an29`, TP1, one replica, with no cross-node
  inference state.
- Inputs are frozen at 1,200 R19 pairs, 1,200 R20 pairs, and the 4,096-item
  ViRL39K blind-solvability sample.
- Verified ephemeral model stages remain present on `an29`: InternVL3-9B
  (`18G`) and Gemma-3-12B-IT (`23G`).
- The literal required command `python -m pytest tests/` completed successfully:
  533 tests passed in 309.79 seconds.

Execution contract:
- Prerequisites are the exact M2 A1, A2-gray, A2b-no-image, and A3-caption run
  manifests registered in the queue config. A failed prerequisite closes M11.
- Phase 1 is six one-pair smoke cells: two backends by three conditions on R19.
  Any failed smoke closes the full phase.
- Phase 2 is 12 full FlipTrack cells (two backends by R19/R20 by
  real/no-image/caption) and six full ViRL cells (two backends by three
  conditions).
- Decoding is greedy with temperature 0, top-p 1, n=1, and fixed maximum output
  lengths of 384 tokens for FlipTrack and 2,048 for ViRL.
- Every child writes an immutable run manifest, per-item output, metrics, and
  model/data/config hashes. The final report builder rejects missing cells,
  row-count drift, prompt/parser drift, decoding drift, or incomplete runs.

Problems:
- Both nodes are occupied by the four registered M2 arms. Starting M11 now would
  compete with proposal-critical training, so the scheduler waits instead of
  treating occupied GPUs as anomalous.
- Model stages are intentionally ephemeral. The launchers verify that each staged
  model directory still exists before a child run starts and fail closed if a
  node restart removes it.

Decision:
- Preserve M2 placement and let the logged queue acquire genuinely free `an29`
  GPUs only after M2 completion.
- Keep M11 `blocked` until `reports/generalization_audits_v1.md` and its machine
  JSON exist and pass the complete 18-cell evidence conjunction.

Next actions:
- Monitor the four M2 prerequisite manifests and queue PID.
- Run the six smoke cells automatically when the prerequisite conjunction lands.
- Execute and audit the full matrix, then update the M11 ledger line only from the
  machine report status.
