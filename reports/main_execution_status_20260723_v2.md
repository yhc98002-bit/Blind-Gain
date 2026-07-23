# Main-Phase Execution Status 2026-07-23 V2

Live state verified against the running cluster 14:54–15:25Z. HEAD at this report:
see the commit carrying it (successor of `527c4a8`). All statements below distinguish
completed / running / queued / ready / human-blocked.

## Completed this round

- **ViRL39K whole-item freeze and decontamination report (M7 data chain)**: frozen
  subset of 29,756 items / 33,249 image references / 28,768 unique images out of
  38,870 items; 9,114 items removed as conservative contamination candidates;
  inspect-only items retained per the registered rule. Artifacts:
  `data/virl39k_main_filtered_{ids.json,.jsonl,images,manifest.json}`,
  `experiments/manifests/decon_virl39k_vs_layer1_v1.json`,
  `reports/decon_virl39k_vs_layer1_v1.{md,json}` — every registered check passes,
  including exact caption-image-index verification.
  - Incident recorded: the login-node finalize chain stalled long enough to be
    misdiagnosed as dead; a retry launched on `an12` raced it. The login chain won
    every final write and finished exit 0; the retry failed harmlessly at the index
    rename and its manifest records `fail`
    (`experiments/runs/virl39k_decon_finalize_retry_an12_20260723T145708Z`); the
    orphaned partial index was removed. Frozen artifacts self-verify against the
    registered report checks.
- **Mini-A5 main run is formally registered and launch-ready**:
  `docs/registered_mini_a5_main_v1.md` (two 120-step arms, full-node TP1 placement,
  matched-except-reward configs, product reward as-registered),
  `scripts/launch_mini_a5_main.sh` (fail-closed guards incl. refusing any node with
  another synchronous trainer), and the binding marker
  `reports/mini_a5_main_registration_marker_v1.json` — status `registered`, all 12
  checks pass, 120 optimizer steps authorized per arm. No human gate remains for
  M6 main; the only dependency is a fully free eight-GPU node plus a checkpoint
  merge/relocation watcher (raw saves are ~50 GiB × 6 per arm).
- **Frozen Mini-A5 corpus inputs committed to history** (they were index-tracked but
  never committed): `data/mini_a5_train_v1/train.parquet` and companions.

## Running now

- **Seed-3 A1 real** (`an29:0-3`): healthy, ~6 h to step 100 at the measured pace
  (~24.6 min/step; step-80 merged/relocated at 13:31–13:44Z). Watcher alive.
- **Seed-3 A2 gray** (`an12:0-3`): healthy, ~15 h to step 100 (~23.4 min/step;
  step-60 raw relocation recorded 15:06Z). Watcher alive.
- **Blind-arm margin calibration** (`an29:4-7`): five of nine cells launched so far;
  both no-image cells finished their full 1,200 pairs; a2_real, a2_gray, a2b_real,
  a2b_gray active; three a3 cells pending. Values sealed until the full matrix and
  finalizer complete.
- **ViRL39K question-blind 3B caption store** (`an12:4-7`, TP1 × 4):
  `experiments/runs/virl39k_caption_store_3b_main_v2_an12_20260723T151428Z` over the
  frozen 28,768-image index; workers at ~50% GPU util and writing shard partials.
  Rough ETA 2–4 h. (First launch attempt appeared dead because the launcher's log
  stayed empty; it had in fact succeeded — recorded so the next operator does not
  double-launch. A probe launch correctly refused occupied GPUs with exit 75.)
- **BlindGain-only storage cleanup** (`an12` CPU, background): executing the
  committed dry-run inventory `reports/cleanup_20260723/…dry-run….json` — 383.5 GiB
  of raw FSDP shards from completed/superseded lineages, each hash-manifested
  before deletion (`checksums_*.json`). 3 of 11 candidates (114 GiB) deleted at
  report time. Preserved invariants: all merged HuggingFace weights, trackers,
  configs, logs; no seed-3 path; M5 fallback raw at
  `checkpoints/m5_anchor_longhorizon_400/global_step_150` retained; `/tmp` archive
  tier untouched; nothing outside BlindGain. Final before/after quota lands in
  `cleanup_execution_*.json` automatically.

## Queued (automated, verified alive on ln207 at 15:20Z — 7 processes)

- **A2b → A3** via `pilot_seed3_remaining_an29_queue_login_20260722T160247Z`
  (an29-only, release-evidence + two stable capacity polls; my calibration cells on
  GPUs 4–7 cannot block the 0–3 pick and finish hours before A1 releases).
- **M5 segments 200→250→300→350→400** via
  `m5_after_seed3_a2_lifecycle_login_20260722T154457Z`, waiting on A2 release with
  per-boundary restore, preflight, capacity, and storage checks.

## Ready to launch next (in order)

1. **Seed-3 A1 step-100 endpoint evaluations** when A1's trainer+watcher complete
   (~21:30–22:30Z): follow the seed-2 pattern
   (`watch_pilot_followup_eval_lifecycle.py` + children spec, cf.
   `experiments/runs/pilot_seed2_recovery_eval_lifecycle_login_20260722T034139Z`).
   Values stay sealed until all four arms and endpoints finish.
2. **Margin-calibration finalizer** once all nine cells complete (needs a
   calibration-aware finalizer run producing
   `reports/blindarm_margin_calibration_results_v1.{md,json}` under the registered
   interpretation rule).
3. **Caption-store coverage audit + four hash-pinned M7 3B configs** after the
   caption store completes (audit tooling exists: `scripts/audit_caption_store.py`).
4. **Mini-A5 arms** on the first fully free node (an29 after A3, unless M5 finishes
   first on an12) — launcher + marker ready; build the accompanying checkpoint
   watcher before launch.

## Human-blocked (unchanged)

- Chart-v08 fixed no-zoom audit (`reports/human_audit_viewer_v3.md`), which gates
  caption-QA scoring, freeze, and confirmation (M12).
- Qualitative review of the 24 support-expansion candidates
  (`reports/support_sharpening_seed1_v2.{md,json}`).

## Storage

- 195.3 GB free at 14:52Z (pre-cleanup); cleanup returns ~383 GiB to the project
  quota, targeting ~580 GB free — comfortable for seed-3 remainder, M5 restores,
  Mini-A5 with watcher pruning, and 7B caption/config preparation.
- Login `/tmp` archive tier is 80% full (155 GB free of 815 GB) — flagged: the next
  raw-relocation-heavy phase (M5 segments) must verify archive headroom; the M5
  lifecycle already refuses restores below its thresholds.

## Interpretation discipline

No seed-3, calibration, or Mini-A5 value has been opened. The freeze and cleanup
open no performance value. The strongest supported statement remains the two-seed
Geometry3K dissociation with the falsified 30–70% blind-recovery prediction.
