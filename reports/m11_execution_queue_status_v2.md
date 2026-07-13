# M11 Generalization Execution Queue Status V2

Status:
- M11 remains `blocked`: no non-Qwen performance result is reported.
- The replacement queue is active in its smoke phase with 24/24 cells pending.
  It is waiting for stable free capacity on `an29`, not for completion of an
  unrelated training manifest.

Correction from V1:
- V1 incorrectly made all four M2 run manifests hard prerequisites. M11 is an
  independent gap-filler in `docs/MAIN_PHASE_BRIEF.md`; GPU availability, not M2
  completion, is its execution dependency.
- The V1 queue
  `experiments/runs/m11_generalization_queue_login_20260713T044555Z` was stopped
  before any child or GPU job started. All 24 cells remained pending. Its manifest
  is preserved with exit code 143, status `fail`, and end time
  `2026-07-13T05:06:39Z`.
- No generated data, predictions, metrics, or model-performance observations were
  produced by the superseded queue.

Replacement evidence:
- Queue run: `experiments/runs/m11_generalization_queue_login_20260713T050649Z`.
- Code commit: `2c9c0bf09babfc84e6a01fc36249f2a87216858f`.
- Config SHA256:
  `4619c1d673b4e0b9e4b4d30651c0d9e752c9608d5727798d96ac120486090fe6`.
- Run status: `running`; queue status: `smoke`; GPU allocation: none.
- Placement: login-only scheduler; child jobs remain one-node, one-GPU, TP1,
  one replica.
- Capacity gate: memory used at most 1,024 MiB and utilization at most 10% for
  two consecutive 300-second polls. A one-poll gap cannot launch a child.
- Singleton gate: the launcher refuses while another M11 queue manifest is
  `running`; the live V1 queue fixture returned exit code 73 before replacement.
- Neighbor M2 manifests remain recorded in the config for operational context but
  are not scientific or mechanical prerequisites.

Scientific execution contract:
- Six one-pair R19 smoke cells (two backends by three conditions) run first.
  Any failed smoke closes the full phase.
- The registered full matrix remains 12 FlipTrack cells (two backends by two
  splits by three conditions) plus six 4,096-item ViRL cells (two backends by
  three conditions).
- Decoding and scoring remain unchanged: greedy; temperature 0; top-p 1; n=1;
  fixed 384/2,048 output-token limits; canonical-v2; fixed prompt contract.
- InternVL3-9B and Gemma-3-12B-IT stages are local-files-only under `an29`
  `/dev/shm`; Gemma explicitly pins `use_fast=False` after the V1 processor
  preflight.

Verification:
- Focused queue and adapter tests: 14/14 passed.
- Literal required suite: `python -m pytest tests/`, 536/536 passed in 255.81
  seconds.
- At replacement launch, every `an29` GPU remained occupied above the capacity
  thresholds, so no smoke cell was started.

Decision:
- Preserve all active M2 jobs and opportunistically use only capacity that remains
  free for two complete polls.
- Keep M11 blocked until `reports/generalization_audits_v1.md` and
  `reports/generalization_audits_v1.json` pass the complete 18-cell conjunction.

Next actions:
- Monitor the stable-capacity gate and all child manifests.
- Audit six smoke outputs before the full phase opens automatically.
- Publish the complete machine report, update the ledger to `pass` only from its
  status, and rerun the main-objective audit.
