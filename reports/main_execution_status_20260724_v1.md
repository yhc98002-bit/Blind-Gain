# Blind Gains — Execution Status 2026-07-24 (v1)

Round start 2026-07-24T03:16Z, login ln207, HEAD at round start `c6019f2`.
All statements below distinguish completed / running / queued / ready /
human-blocked work. Values for unfinished registered readouts stay sealed.

## 1. State found at round start

- `an29`: fully idle for ~5.5 h (A1 seed-3 finished 2026-07-23 ~21:42Z, merged
  and raw-relocated; all nine calibration cells complete at 1,200 rows), yet
  the remaining-arm queue had launched nothing.
- `an12`: A2 gray seed-3 at step ~91/100 on GPUs 0–3; caption workers exited
  after full coverage (4 × 7,192 = 28,768 rows, zero resumed).
- Cleanup executed to completion overnight: 11/11 candidates, per-candidate
  SHA-256 manifests in `reports/cleanup_20260723/`.

## 2. Scheduler deadlock: diagnosis and repair (completed)

Root cause: `run_pilot_seed3_queue_v2.py::arm_checkpoint_ready` required the
checkpoint-watcher manifest to be `complete` before releasing a node, but
`watch_pilot_checkpoints.py` holds its manifest open until step-60 evaluation
markers exist, and those evaluations run post-cohort under the registered
seed-2 lifecycle procedure (`run_pilot_step100_eval_queue.py` hardwires the
cohort release to the a3_caption arm of the seed). The M5-after-A2 lifecycle
gate `a2_release_state` had the same watcher dependency. Net effect: A2b/A3
could never launch and M5 could never resume — a mutual wait, not a crash.

Repair (commit `3eaede0`):
- Both pollers now release capacity on the artifact truth: training manifest
  `complete`/exit 0/artifacts verified + step-100 merged HF index +
  `RAW_STATE_RELOCATED.json` marker on disk. Watcher terminal failures still
  fail closed. Step-60 raw retention closes later when the post-cohort
  evaluation lifecycle writes the markers.
- Old pollers retired via SIGTERM (both manifests finalized `fail`/`-15`,
  the same signature as the earlier v5 retirement); relaunched:
  - M5 lifecycle: `experiments/runs/m5_after_seed3_a2_lifecycle_login_20260724T033615Z`
  - Remaining-arm queue (v2 job type, new launcher
    `scripts/launch_pilot_seed3_remaining_an29_v2.sh`):
    `experiments/runs/pilot_seed3_remaining_an29_queue_login_20260724T033648Z`
- Dry-tested both patched gates against live records before any restart.

Outcome: **A2b seed-3 launched** at 03:37:54Z —
`experiments/runs/mech_a2b_noimage_seed3_an29_20260724T033754Z`, an29 GPUs
0–3, watcher `pilot_checkpoint_watch_mech_a2b_noimage_seed3_login_20260724T033855Z`.
A3 remains queued behind A2b on an29 by design.

## 3. Blind-arm margin calibration — readout complete, values open

Registered in `docs/registered_blindarm_margin_calibration_v1.md`; finalizer
`scripts/finalize_blindarm_margin_calibration.py` verified all 18 cells
(9 calibration + 9 frozen seed-1), integrity controls pass (all 30
blind-condition cells structurally zero), audit
`reports/blindarm_margin_calibration_audit_v1.json` status `pass`.

Real-input paired-margin effects vs frozen base (primary template,
600 pairs, 10,000-resample paired bootstrap):

| model | effect | 95% CI |
|---|---|---|
| A1 real step-100 (reference) | +0.1501 | [+0.1448, +0.1554] |
| A2 gray step-100 | +0.0356 | [+0.0337, +0.0375] |
| A2b no-image step-100 | +0.0348 | [+0.0327, +0.0369] |
| A3 caption step-100 | +0.0900 | [+0.0866, +0.0934] |

Registered verdict: **intermediate_pattern** — no blind arm overlaps the A1
CI, A2/A2b sit below half of the A1 effect, but A3 does not. Descriptively:
the seed-1 margin inflation decomposes along an information-access gradient
(gray ≈ no-image < caption < real). Roughly 23% of the A1 effect appears as
condition-independent RL sharpening, caption-mediated training recovers ~60%,
and the remainder requires real-image training. Discrete pair success is flat
in every arm (0.897–0.907); normalized entropy falls and the top1−top2 gap
widens monotonically along the same gradient, and only under real inputs
(blind-condition entropy ≈ 0.998 for all models). Terminology per
registration: visual-evidence ranking; no perception claim.

## 4. ViRL39K (M7) chain

- Caption store artifact frozen: `data/virl39k_caption_store_3b_main_v2.jsonl`
  (28,768 rows, SHA256 `45b0ef5ab6da6b872e81e46215e28418563f08e20931d4d3cc6bf14cfce57d04`),
  concatenated deterministically from the four v2 worker shards.
- Independent coverage audit (fresh image hashing on an12):
  `reports/virl39k_caption_store_audit_v1.json` — see status line in §7.
- Remaining before any M7 optimizer step: four matched hash-pinned arm
  configurations (+ per-arm train parquet build) and the fail-closed launcher
  required by `docs/registered_m7_amendment_v1.md`.

## 5. Storage

- Cleanup complete: 11/11 candidates, 383.5 GiB reclaimed, per-candidate
  checksum manifests committed. The `quota_after` block in the execution
  report caught a transient Lustre quota-device error; live usage after
  cleanup is ~950 GiB of the 1.5 TB project allocation (~585 GiB headroom
  for M5 resumption, A2b/A3 checkpoints, and Mini-A5).

## 6. Running / queued / ready / human-blocked

Running now:
- A2 gray seed-3 final steps then finalize (an12 GPUs 0–3), watcher alive.
- A2b no-image seed-3 (an29 GPUs 0–3), watcher alive.
- v2 remaining-arm queue and rearmed M5 lifecycle (ln207 pollers).
- Caption-store coverage audit (an12 CPU, taskset-pinned, nice 19).

Queued (automatic):
- A3 caption seed-3 launch on an29 after A2b reaches artifact-complete.
- M5 segment resumption on an12 GPUs 0–3 once A2 finalizes and its step-100
  merge + relocation land (M5 lifecycle then drives 200→250→…→400, never
  beyond 400).

Ready (engineer action next round):
- Post-cohort seed-3 evaluation lifecycle: sixteen
  `m3_seed3_*_{r19,geo3k}_queue_v1.json` endpoint configs + a seed-3 launcher
  cloned from `scripts/launch_pilot_seed2_eval_lifecycle.sh`, launched after
  A3 training completes (cohort-release gate then matches the registered
  seed-2 procedure verbatim). This also closes the four watchers and step-60
  raw retention.
- M7: four matched arm configs + train-parquet build + registered launcher.
- Mini-A5: registered and authorized (120 steps/arm); needs the checkpoint
  watcher build and a genuinely free 8-GPU node (an29 after A2b+A3, or an12
  after M5 reaches 400).
- Three-seed summary once seed-3 arms + endpoints complete.

Human-blocked (unchanged):
- chart-v08 no-zoom audit (`reports/human_audit_viewer_v3.md`).
- Qualitative review of 24 support-expansion candidates
  (`reports/support_sharpening_seed1_v2.{md,json}`).

## 7. Deviations and incidents this round

- The v1 remaining-arm queue and the first M5-after-A2 lifecycle were
  intentionally retired (SIGTERM, manifests `fail`/`-15`) to load the patched
  gate code; both successors adopted the exact live children. No trainer,
  watcher, or checkpoint was touched.
- First finalizer invocation failed fast on a schema mismatch
  (`candidate_scores_*` are id-keyed mappings, not arrays); fixed and rerun
  in a fresh run dir; the failed run dir records `fail` honestly.
- Caption-store audit status at commit time: recorded in
  `reports/virl39k_caption_store_audit_v1.json` (this file is the source of
  truth; if absent or failing, M7 configs stay blocked).
