# M2 Step-100 Lifecycle Status V1

Status:
- M2 remains `blocked`; this is an operational lifecycle report and makes no
  scientific gate decision.
- Three of four registered step-100 R19 markers are structurally complete: A1,
  A2b, and A3. A2-gray remains in training.
- Locked 601-row Geometry3K-test readouts for A1, A2b, and A3 are active as
  independent TP1 jobs on `an12:4-6`.
- No pilot training, validation, FlipTrack, or Geometry3K performance value was
  opened or interpreted while producing this report.

Evidence:
- Evaluator implementation commit: `01839373c176b8f1b6247b3583301bb4ce707558`.
- Focused evaluator/reward/parser suite: `52 passed` before launch; the main
  objective consistency audit returned `pass` with zero errors.

| Arm | Training state | Step-100 R19 marker | Marker SHA256 | Geometry3K readout |
| --- | --- | --- | --- | --- |
| A1 real | complete | complete; all 15 checks true | `613c6c453ed53c14aa484cbff03c4890a95c9dbd6b3fa3d0a46780f745de9865` | `experiments/runs/m2_geo3k_a1_real_seed1_step100_an12_gpu4_20260715T210056Z` |
| A2 gray | running; mechanically at step 69 | pending | n/a | waits for step 100, retention, and exact R19 marker |
| A2b no-image | complete | complete; all 15 checks true | `72063f92807b809afef582b5816813007cbe9bafce195edf2d6008bae2ffaf6f` | `experiments/runs/m2_geo3k_a2b_noimage_seed1_step100_an12_gpu5_20260715T210056Z` |
| A3 caption | complete | complete; all 15 checks true | `18d231ff8966dca99be4bb18d8809209e20ff6f1dcce944abbd34b72b2fe83ff` | `experiments/runs/m2_geo3k_a3_caption_seed1_step100_an12_gpu6_20260715T210056Z` |

- A1 aggregation completed at `2026-07-15T20:53:44Z`; its finalizer and queue
  both exited 0, and the exact completion marker was written only afterward.
- Every active Geometry3K manifest records node, GPU, TP width, replica count,
  Git/config/data hashes, source training-manifest hash, retained merged-checkpoint
  hash, prompt/parser/reward versions, and greedy decoding lock.
- Decoding is fixed to temperature `0`, top-p `1`, `n=1`, maximum `2,048`
  tokens, and seed `20260710` for all three checkpoint readouts.
- The evaluator refuses an occupied GPU, mismatched arm/checkpoint/R19 marker,
  unclean preregistration, missing A3 caption shard, changed checkpoint on resume,
  and any output overwrite.

Problems:
- A2-gray has not completed steps 70–100, final retention, step-100 R19 scoring,
  or its Geometry3K readout.
- The three active Geometry3K outputs have not completed their 601 rows or passed
  the independent row-identity and score-recomputation audit.
- The registered paired estimands, StrictGain identity, hurdle contrast, rank
  analyses, and final M2 report therefore remain unavailable.

Decision:
- Use `an12:4-6` for M2-critical TP1 readouts while disjoint A2 training continues
  on `an12:0-3`.
- Leave `an12:7` unassigned: M11 is fail-closed until all four R19 markers validate,
  while the registered 72B caption stress needs a four-GPU block and must not delay
  M2.
- Preserve all completed R19 aggregates unopened until the registered M2 analysis.

Next actions:
- Complete and structurally audit the three active 601-row Geometry3K readouts.
- Continue A2-gray to step 100, then run retention, exact R19 scoring, and the same
  locked Geometry3K readout.
- Join each final row to its arm-specific frozen L7 baseline only after all four
  readouts pass audit, then compute exactly the preregistered seed-1 analyses.

Machine-readable companion:
- `reports/m2_step100_lifecycle_status_v1.json`.
