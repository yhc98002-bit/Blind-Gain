# Evaluation Queue Storage Decoupling V2

Status:
- R3 implementation audit: `pass`.
- V2 extends V1 through the Geometry3K queue, launcher, and independent audit.
- The failed queue at
  `experiments/runs/pilot_geo3k_step100_queue_a2_gray_login_20260716T153042Z`
  is preserved unchanged.

Evidence:
- The fresh A2 R19 lifecycle completed and produced the exact registered marker while
  `RAW_STATE_RELOCATED.json` was absent. The first Geometry3K queue then failed before
  GPU launch with `retention_marker: absent` and
  `performance_values_inspected: false`, proving an unpatched relocation dependency.
- Queue validation now requires the complete training identity, exact R19 marker,
  complete merged checkpoint index, and all marker checks; it does not query archive
  relocation state.
- The launcher computes the checkpoint-index SHA256 and requires exact equality with
  the R19 marker. A valid retention marker is used as stronger optional provenance;
  an absent or stale marker cannot block evaluation.
- The independent audit accepts either `retention_marker` or `r19_marker_index`
  provenance. In the latter mode, it verifies the R19 marker hash, complete marker
  checks, checkpoint path, index binding, and on-disk index hash.
- Implementation hashes:
  - `scripts/run_pilot_geo3k_step100_queue.py`:
    `0b88857424126592915cf5044c922c25f5405b171ed91c365eba525fb0718ce4`.
  - `scripts/launch_pilot_geo3k_step100_eval.sh`:
    `864979583a40c0c29d3c1f0fe8fd559c75fd51b124a0d3e1a7815c3c8489db7c`.
  - `scripts/audit_pilot_geo3k_step100_eval.py`:
    `b25137f21860b79c26b8999b6ec4652e025679960b04701bd0169e79033d9074`.
- Focused queue/evaluation/audit suite: `27 passed`.
- Adversarial fixtures remove `RAW_STATE_RELOCATED.json`; marker validation and the
  independent provenance audit must still pass. The prior code fails both fixtures.

Problems:
- Raw-state relocation and latest-only retention remain operationally required, but
  they are asynchronous storage duties and no longer gate scientific evaluation.

Decision:
- Checkpoint merge and evaluation depend on checkpoint identity and integrity.
- Archive relocation remains separately guarded, logged, retryable, and incapable of
  withholding an otherwise valid evaluation marker or queue launch.

Next actions:
- Launch a fresh immutable A2 Geometry3K queue from the already complete R19 marker.
- Require exactly 601 rows and a passing independent audit before opening any of the
  four registered arm values.
