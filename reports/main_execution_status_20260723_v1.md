# Main-Phase Execution Status 2026-07-23 V1

Live state verified against the running cluster at 2026-07-23T14:00–14:40Z from repository
commits `b3481c2`→`959b779` (both pushed to `origin/agent/gate2-recovery` and `origin/master`).

## Complete

- Seeds 1 and 2: all four arms, endpoint evaluations, and unified readouts (unchanged).
- ViRL39K decontamination signal stack is now COMPLETE:
  - RapidOCR coverage 45,302/45,302 unique images, 0 extraction errors. The quota-crashed
    v2 login run contributed 24,652 validated rows (0 truncated, 0 quota-tainted); the
    remaining 20,650 were extracted in ~25 minutes on `an12` CPUs by the v4 continuation
    (`experiments/runs/decon_ocr_virl39k_layer1_resume_v4_an12_20260723T141713Z`, 16
    shards, `intra_op_num_threads=3`, cores 56–111, nice 19).
  - Resume-record subtraction run:
    `experiments/runs/decon_ocr_virl39k_resume_records_login_20260723T140800Z`.
  - Combined immutable 24-shard set:
    `experiments/runs/decon_ocr_virl39k_combined_shards_login_20260723T143230Z`
    (v2/v4 disjointness machine-verified).
  - OCR-signal merge against the calibrated embedding baseline is complete with exit 0:
    `experiments/runs/decon_ocr_compare_virl39k_layer1_full_an12_20260723T143237Z/comparison_v4.json`
    — 254,187 candidate edges, action counts inspect=199,407 / remove=54,780,
    `pending_layers=[]`, OCR coverage 45,302 present / 0 missing.
- M5 step-200 durable state, prior arm checkpoints, and archives: unchanged and intact.

## Currently running

- Seed-3 A1 real, `an29` GPUs 0–3: ~step 81/100 (tqdm 32.8h elapsed / ~7.9h remaining at
  14:00Z). Step-80 checkpoint merged, raw-relocated, and registered. Trainer, watcher
  (`pilot_checkpoint_watch_mech_a1_real_seed3_login_20260722T050427Z`), and log all healthy.
- Seed-3 A2 gray, `an12` GPUs 0–3: ~step 59/100 (22.5h elapsed / ~16.8h remaining).
  Step-40 merged and relocated. Trainer and watcher healthy; policy updates advancing
  normally throughout today's an12 CPU incident (see Problems).
- Blind-arm margin-calibration matrix (registered
  `docs/registered_blindarm_margin_calibration_v1.md`), `an29` GPUs 4–7: nine TP1 cells
  (a2/a2b/a3 step-100 × real/no_image/gray); first four cells active at 14:36Z; queue
  `experiments/runs/blindarm_margin_calibration_matrix_queue_login_20260723T143504Z`.
  Values stay closed until all nine cells and the finalizer complete.
- ViRL39K decontamination finalize + whole-item freeze chain, login:
  `experiments/runs/virl39k_decon_finalize_virl39k_main_v1_login_20260723T143637Z`
  (summarize → freeze → source/category report).
- Storage snapshot refresh loop, login (`ln207`), unchanged.

## Queued (automated, verified alive on ln207 with fresh heartbeats)

- Seed-3 A2b then A3 on `an29`: `pilot_seed3_remaining_an29_queue_login_20260722T160247Z`
  (an29-only launch set; requires trainer+watcher completion evidence plus two stable
  capacity polls; A2b/A3 pending; dependencies m6_smoke/seed2 complete, m5 running).
- M5 segmented continuation 200→250→300→350→400 on `an12:0-3`:
  `m5_after_seed3_a2_lifecycle_login_20260722T154457Z`, state `waiting_seed3_a2_release`;
  it performs storage refresh, raw restore, Ray preflight, and capacity checks at every
  boundary. Do not colocate a second synchronous trainer on `an12`.

## Ready to launch (next in line)

- After the freeze completes: full question-blind 3B caption coverage for every retained
  ViRL39K image on free half-node GPUs (TP1 replicas), then caption audits and the four
  matched hashed 3B arm configs (M7), then the registered 3B decomposition.
- After seed-3 A1 completes: A1 step-100 Geometry3K + R19 endpoint evaluations (seed-2
  eval-lifecycle pattern), keeping seed-3 values closed until all four arms finish.
- Margin-calibration finalizer once all nine cells are complete.

## Genuinely blocked (human gates)

- Chart-v08: fixed no-zoom human audit (package ready: `reports/human_audit_viewer_v3.md`;
  200-image 72B strong-caption store audited and preserved). Caption-only QA scoring is
  sequenced after the human audit by the registered M12 order; it is prepared but not run.
- Support-expansion: qualitative review of the 24 still-0/80 candidates
  (`reports/support_sharpening_seed1_v2.{md,json}`, registry v3). Packet ready.

## Problems and incidents

- OCR v3 relaunch incident (resolved, no data loss): the first an12 continuation ran
  uncapped ONNX thread pools (RapidOCR default `intra_op_num_threads=-1`), driving load
  to ~1319 for several minutes. Processes were killed, the run manifest records `fail`,
  and v4 relaunched with per-session thread caps, core pinning (56–111), and nice 19.
  The A2 trainer advanced normally through the window (policy-update cadence unchanged).
  Rule adopted: CPU inference on a trainer node must pin cores and cap ONNX/OMP threads.
- `ln206` refuses SSH from `ln207`; every watcher lives on `ln207`. Single-login-node
  dependency noted; queue state and PIDs are on shared storage, so a dead `ln207` is
  recoverable by relaunching watchers elsewhere with `--resume`.
- `an29:/tmp` remains nearly full (unchanged; Ray uses /dev/shm; no current impact).
- GitHub pushes require the local mihomo proxy on `ln207` (`127.0.0.1:7890`); the
  site proxy in `git config` intermittently returns 503.
- Lustre project quota: 1,414.9 GB used / 195.7 GB free at 11:52Z. The M5 restore guard
  remeasures before each boundary; caption-store text artifacts are small. Watch before
  any new raw-checkpoint-heavy work.

## Node schedule now

- `an29:0-3` seed-3 A1 → (auto) A2b → A3. `an29:4-7` margin-calibration cells; idle after
  cells finish and before A1 release stays idle by design (no second trainer).
- `an12:0-3` seed-3 A2 → (auto) M5 segments. `an12:4-7` free for caption/eval inference
  once the freeze completes (host-memory budget respected; no 72B serving on trainer nodes).
- Login `ln207`: watchers, queues, finalize chain, storage loop, report generation.

## Interpretation discipline

No seed-3 value has been opened. No calibration value has been opened. The freeze chain
opens no performance value. The strongest current supported statement remains the
two-seed Geometry3K dissociation with the falsified 30–70% blind-recovery prediction.
